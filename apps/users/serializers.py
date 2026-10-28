from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import User


class UserReadSerializer(serializers.ModelSerializer):
    """Kullanıcı okuma (me endpoint, login response)."""
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'phone_number', 'is_verified_driver',
            'is_online', 'current_location', 'date_joined',
        ]
        read_only_fields = fields


class RegisterSerializer(serializers.ModelSerializer):
    """Kayıt formu."""
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password2',
            'first_name', 'last_name', 'role', 'phone_number',
        ]

    def validate_role(self, value):
        if value not in [User.Role.CUSTOMER, User.Role.DRIVER]:
            raise serializers.ValidationError(
                "Rol 'CUSTOMER' veya 'DRIVER' olmalı."
            )
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError(
                {'password': 'Şifreler eşleşmiyor.'}
            )
        return attrs


class UserUpdateSerializer(serializers.ModelSerializer):
    """Profil güncelleme — sadece güvenli alanlar."""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone_number']


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Login yanıtına `user` objesini de ekler."""
    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = UserReadSerializer(self.user).data
        return data


class DriverLocationSerializer(serializers.Serializer):
    """Sürücü konum güncelleme payload'ı."""
    latitude = serializers.FloatField(min_value=-90, max_value=90)
    longitude = serializers.FloatField(min_value=-180, max_value=180)