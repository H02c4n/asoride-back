from django.db.models import Q
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.gis.db.models.functions import Distance
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from users.models import User
from .models import Ride
from .serializers import RideSerializer, RideCreateSerializer

class RideViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = RideSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == User.Role.CUSTOMER:
            # Müşteri sadece kendi yolculuklarını görür
            return Ride.objects.filter(customer=user).order_by('-created_at')
        elif user.role == User.Role.DRIVER:
            # Sürücü: Kendi kabul ettiği yolculuklar VEYA henüz kimsenin kabul etmediği (REQUESTED) yolculuklar
            return Ride.objects.filter(
                Q(driver=user) | Q(driver__isnull=True, status=Ride.Status.REQUESTED)
            ).order_by('-created_at')
        return Ride.objects.none()

    def get_serializer_class(self):
        if self.action == 'create':
            return RideCreateSerializer
        return RideSerializer

    def create(self, request, *args, **kwargs):
        if request.user.role != User.Role.CUSTOMER:
            return Response({"detail": "Sadece müşteriler yolculuk talebi oluşturabilir."}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ride = serializer.save(customer=request.user)
        
        return Response(RideSerializer(ride).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def nearby_drivers(self, request):
        """Müşterinin konumuna en yakın müsait sürücüleri bulur (PostGIS)."""
        if request.user.role != User.Role.CUSTOMER:
            return Response({"detail": "Sadece müşteriler sürücü arayabilir."}, status=status.HTTP_403_FORBIDDEN)

        try:
            lat = float(request.query_params.get('lat'))
            lng = float(request.query_params.get('lng'))
        except (TypeError, ValueError):
            return Response({"detail": "Geçerli lat ve lng parametreleri gerekli."}, status=status.HTTP_400_BAD_REQUEST)

        customer_location = Point(lng, lat, srid=4326)

        # PostGIS Sihri: Konumdan 5 km çevredeki müsait sürücüleri bul ve mesafeyi hesapla
        nearby_drivers = User.objects.filter(
            role=User.Role.DRIVER,
            is_online=True,
            current_location__distance_lte=(customer_location, D(m=5000))
        ).annotate(
            distance=Distance('current_location', customer_location) # <-- DÜZELTİLDİ
        ).order_by('distance')

        driver_list = [{
            "id": driver.id,
            "username": driver.username,
            "distance_meters": round(driver.distance.m), # Artık driver.distance var
            "location": {"lat": driver.current_location.y, "lng": driver.current_location.x}
        } for driver in nearby_drivers]

        return Response({"count": len(driver_list), "drivers": driver_list})

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def accept(self, request, pk=None):
        """Sürücünün yolculuğu kabul etmesi."""
        ride = self.get_object()
        
        if request.user.role != User.Role.DRIVER:
            return Response({"detail": "Sadece sürücüler yolculuk kabul edebilir."}, status=status.HTTP_403_FORBIDDEN)
            
        if ride.status != Ride.Status.REQUESTED:
            return Response({"detail": "Bu yolculuk artık talep aşamasında değil."}, status=status.HTTP_400_BAD_REQUEST)
            
        if ride.driver is not None:
            return Response({"detail": "Bu yolculuk zaten başka bir sürücü tarafından alınmış."}, status=status.HTTP_400_BAD_REQUEST)

        ride.driver = request.user
        ride.status = Ride.Status.ACCEPTED
        ride.save()

        # WebSocket'e bildir
        self._notify_ride_status(ride, Ride.Status.ACCEPTED)

        return Response({"detail": "Yolculuk kabul edildi.", "status": ride.status})

    @action(detail=True, methods=['patch'], permission_classes=[permissions.IsAuthenticated])
    def update_status(self, request, pk=None):
        """Yolculuk durumunu güncelle (Sadece atanmış sürücü)."""
        ride = self.get_object()
        
        if ride.driver != request.user:
            return Response({"detail": "Sadece atandığınız yolculukları güncelleyebilirsiniz."}, status=status.HTTP_403_FORBIDDEN)

        new_status = request.data.get('status')
        valid_statuses = [s[0] for s in Ride.Status.choices]
        
        if new_status not in valid_statuses:
            return Response({"detail": "Geçersiz durum."}, status=status.HTTP_400_BAD_REQUEST)

        # State Machine mantığı: Sadece belirli durumlardan belirli durumlara geçilebilir.
        # (Örn: ACCEPTED'dan REQUESTED'a dönülemez)
        valid_transitions = {
            Ride.Status.ACCEPTED: [Ride.Status.ARRIVED, Ride.Status.CANCELLED],
            Ride.Status.ARRIVED: [Ride.Status.ONGOING, Ride.Status.CANCELLED],
            Ride.Status.ONGOING: [Ride.Status.COMPLETED],
        }

        if ride.status not in valid_transitions or new_status not in valid_transitions[ride.status]:
             return Response({"detail": f"{ride.status} durumundan {new_status} durumuna geçilemez."}, status=status.HTTP_400_BAD_REQUEST)

        ride.status = new_status
        ride.save()
        
        # WebSocket'e bildir
        self._notify_ride_status(ride, new_status)

        return Response({"detail": "Durum güncellendi.", "status": ride.status})

    # ------------------------------------------------------------------
    # WebSocket Yayın Yardımcısı
    # ------------------------------------------------------------------
    def _notify_ride_status(self, ride, new_status):
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'ride_{ride.id}',
            {
                'type': 'ride_status_broadcast',
                'status': new_status,
            }
        )