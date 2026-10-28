from django.shortcuts import render

# Create your views here.
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import (
    CustomTokenObtainPairSerializer,
    DriverLocationSerializer,
    RegisterSerializer,
    UserReadSerializer,
    UserUpdateSerializer,
)
from .services import register_user, update_driver_location


class RegisterView(APIView):
    """POST /api/users/register/ — Kayıt + otomatik login."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data

        user = register_user(
            username=d['username'],
            email=d['email'],
            password=d['password'],
            password2=d['password2'],
            role=d['role'],
            first_name=d.get('first_name', ''),
            last_name=d.get('last_name', ''),
            phone_number=d.get('phone_number', ''),
        )

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                'user': UserReadSerializer(user).data,
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(TokenObtainPairView):
    """POST /api/users/login/ — access + refresh + user."""
    permission_classes = [permissions.AllowAny]
    serializer_class = CustomTokenObtainPairSerializer


class MeView(generics.RetrieveUpdateAPIView):
    """GET/PATCH /api/users/me/ — Kendi profili."""
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return UserUpdateSerializer
        return UserReadSerializer

    def get_object(self):
        return self.request.user


class DriverLocationView(APIView):
    """POST /api/users/driver/location/ — Konum güncelle (sürücü)."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if not request.user.is_driver:
            return Response(
                {'detail': 'Sadece sürücüler konum güncelleyebilir.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = DriverLocationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        update_driver_location(
            user=request.user,
            lat=serializer.validated_data['latitude'],
            lng=serializer.validated_data['longitude'],
        )

        return Response({
            'detail': 'Konum güncellendi.',
            'location': {
                'lat': serializer.validated_data['latitude'],
                'lng': serializer.validated_data['longitude'],
            },
        })