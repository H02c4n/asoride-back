from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.permissions import IsCustomer, IsDriver
from ..models import Ride
from ..selectors import (
    get_available_rides_for_driver,
    get_ride_by_id,
    get_rides_for_customer,
)
from ..serializers import (
    RatingReadSerializer,
    RideCreateSerializer,
    RideReadSerializer,
    RatingCreateSerializer,
)
from ..services import (
    RatingError,
    RideError,
    accept_ride,
    cancel_ride,
    create_rating,
    create_ride,
    update_ride_status,
)


class RideViewSet(viewsets.ModelViewSet):
    """
    Endpoints:
    - GET    /api/rides/                    → list (role'e göre)
    - POST   /api/rides/                    → create (müşteri)
    - GET    /api/rides/{id}/               → retrieve
    - POST   /api/rides/{id}/accept/        → sürücü kabul
    - PATCH  /api/rides/{id}/status/        → sürücü durum ilerlet
    - POST   /api/rides/{id}/cancel/        → müşteri/sürücü iptal
    - POST   /api/rides/{id}/rate/          → müşteri puanla
    """
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_customer:
            return get_rides_for_customer(user)
        if user.is_driver:
            return get_available_rides_for_driver(user)
        return Ride.objects.none()

    def get_serializer_class(self):
        if self.action == 'create':
            return RideCreateSerializer
        return RideReadSerializer

    def get_object(self):
        from rest_framework.exceptions import NotFound, PermissionDenied

        ride = get_ride_by_id(int(self.kwargs['pk']))
        if not ride:
            raise NotFound('Yolculuk bulunamadı.')

        user = self.request.user

        # ------------------------------------------------------------------
        # accept: sürücü, kabul etmeden ÖNCE ride'a erişebilmeli
        # Service katmanı zaten "zaten alınmış mı?" ve "REQUESTED mu?" kontrollerini yapar.
        # ------------------------------------------------------------------
        if self.action == 'accept':
            if not user.is_driver:
                raise PermissionDenied('Sadece sürücüler yolculuk kabul edebilir.')
            return ride

        # ------------------------------------------------------------------
        # Diğer tüm action'lar (retrieve, status, cancel, rate): taraflardan biri olmalı
        # ------------------------------------------------------------------
        if user.id not in (ride.customer_id, ride.driver_id):
            raise PermissionDenied('Bu yolculuğa erişim yetkiniz yok.')

        return ride

    # ------------------------------------------------------------------
    # HTTP Mutasyonları yasak (yalnızca action'lar üzerinden)
    # ------------------------------------------------------------------
    def update(self, request, *args, **kwargs):
        return Response({'detail': 'Yolculuklar doğrudan güncellenemez.'},
                        status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def partial_update(self, request, *args, **kwargs):
        return Response({'detail': 'Yolculuklar doğrudan güncellenemez.'},
                        status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def destroy(self, request, *args, **kwargs):
        return Response({'detail': 'Yolculuklar silinemez, iptal edin.'},
                        status=status.HTTP_405_METHOD_NOT_ALLOWED)

    # ------------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------------
    def create(self, request, *args, **kwargs):
        if not request.user.is_customer:
            return Response({'detail': 'Sadece müşteriler yolculuk talebi oluşturabilir.'},
                            status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ride = create_ride(customer=request.user, validated_data=serializer.validated_data)
        return Response(
            RideReadSerializer(ride, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )

    # ------------------------------------------------------------------
    # ACCEPT
    # ------------------------------------------------------------------
    @action(detail=True, methods=['post'], permission_classes=[IsDriver])
    def accept(self, request, pk=None):
        ride = self.get_object()
        try:
            ride = accept_ride(driver=request.user, ride=ride)
        except RideError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(RideReadSerializer(ride, context={'request': request}).data)

    # ------------------------------------------------------------------
    # UPDATE STATUS
    # ------------------------------------------------------------------
    @action(detail=True, methods=['patch'], url_path='status', permission_classes=[IsDriver])
    def update_status(self, request, pk=None):
        ride = self.get_object()
        new_status = request.data.get('status')

        if not new_status:
            return Response({'detail': 'status alanı zorunlu.'},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            ride = update_ride_status(ride=ride, driver=request.user, new_status=new_status)
        except RideError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(RideReadSerializer(ride, context={'request': request}).data)

    # ------------------------------------------------------------------
    # CANCEL
    # ------------------------------------------------------------------
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        ride = self.get_object()
        try:
            ride = cancel_ride(ride=ride, actor=request.user)
        except RideError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(RideReadSerializer(ride, context={'request': request}).data)

    # ------------------------------------------------------------------
    # RATE
    # ------------------------------------------------------------------
    @action(detail=True, methods=['post'], permission_classes=[IsCustomer])
    def rate(self, request, pk=None):
        ride = self.get_object()
        serializer = RatingCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            rating = create_rating(
                ride=ride,
                customer=request.user,
                data=serializer.validated_data,
            )
        except RatingError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(RatingReadSerializer(rating).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated, IsCustomer])
    def nearby_drivers(self, request):
        """GET /api/rides/nearby-drivers/?lat=..&lng=.. — çevredeki sürücüler."""
        from django.contrib.gis.db.models.functions import Distance
        from apps.core.utils import make_point, point_to_latlng
        from apps.users.selectors import get_online_verified_drivers_within

        try:
            lat = float(request.query_params['lat'])
            lng = float(request.query_params['lng'])
        except (KeyError, TypeError, ValueError):
            return Response(
                {'detail': 'lat ve lng parametreleri zorunlu.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        point = make_point(lat, lng)
        drivers = (
            get_online_verified_drivers_within(point, radius_meters=10_000)
            .annotate(distance=Distance('current_location', point))
            .order_by('distance')[:20]
        )

        return Response({
            'count': len(drivers),
            'drivers': [
                {
                    'id': d.id,
                    'username': d.username,
                    'distance_meters': round(d.distance.m),
                    'location': point_to_latlng(d.current_location),
                }
                for d in drivers
            ],
        })