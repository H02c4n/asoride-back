from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from .models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'phone_number', 'is_verified_driver', 'is_online'
        ]
        read_only_fields = ['id', 'is_verified_driver', 'is_online']

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2', 'first_name', 'last_name', 'role', 'phone_number']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Şifreler eşleşmiyor."})
        
        # Rol kontrolü: Sadece CUSTOMER veya DRIVER seçilebilir
        if attrs.get('role') not in [User.Role.CUSTOMER, User.Role.DRIVER]:
            raise serializers.ValidationError({"role": "Geçersiz rol. 'CUSTOMER' veya 'DRIVER' seçmelisiniz."})
        
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        return user

class DriverLocationSerializer(serializers.Serializer):
    """Sürücünün konumunu güncellemek için kullanılacak."""
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()