from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User
from .serializers import RegisterSerializer, UserSerializer, DriverLocationSerializer

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

class LoginView(TokenObtainPairView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        # Giriş yapan kullanıcının bilgilerini de dönelim
        user = User.objects.get(username=request.data['username'])
        response.data['user'] = UserSerializer(user).data
        return response

class MeView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

class DriverLocationUpdateView(generics.GenericAPIView):
    """Sadece sürücülerin konum güncellemesi yapabilmesi için."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = DriverLocationSerializer

    def post(self, request):
        if request.user.role != User.Role.DRIVER:
            return Response({"detail": "Sadece sürücüler konum güncelleyebilir."}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # PostGIS PointField'ı güncelle
        from django.contrib.gis.geos import Point
        lat = serializer.validated_data['latitude']
        lng = serializer.validated_data['longitude']
        request.user.current_location = Point(lng, lat, srid=4326)
        request.user.is_online = True
        request.user.save()
        
        return Response({"detail": "Konum güncellendi.", "location": {"lat": lat, "lng": lng}})