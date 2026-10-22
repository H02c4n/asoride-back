from rest_framework import serializers
from django.contrib.gis.geos import Point
from .models import Ride
from users.serializers import UserSerializer

class RideSerializer(serializers.ModelSerializer):
    customer = UserSerializer(read_only=True)
    driver = UserSerializer(read_only=True)

    class Meta:
        model = Ride
        fields = [
            'id', 'customer', 'driver', 'pickup_location', 'dropoff_location',
            'pickup_address', 'dropoff_address', 'status', 'price', 'created_at'
        ]
        read_only_fields = ['id', 'customer', 'driver', 'status', 'price', 'created_at']

class RideCreateSerializer(serializers.ModelSerializer):
    # Haritadan gelen enlem/boylamları alıp PostGIS Point'e çevireceğiz
    pickup_lat = serializers.FloatField(write_only=True)
    pickup_lng = serializers.FloatField(write_only=True)
    dropoff_lat = serializers.FloatField(write_only=True)
    dropoff_lng = serializers.FloatField(write_only=True)

    class Meta:
        model = Ride
        fields = [
            'pickup_lat', 'pickup_lng', 'pickup_address',
            'dropoff_lat', 'dropoff_lng', 'dropoff_address'
        ]

    def create(self, validated_data):
        # Enlem/Boylamları PostGIS Point formatına çevir (DİKKAT: Önce Lng, sonra Lat)
        pickup_point = Point(validated_data.pop('pickup_lng'), validated_data.pop('pickup_lat'), srid=4326)
        dropoff_point = Point(validated_data.pop('dropoff_lng'), validated_data.pop('dropoff_lat'), srid=4326)
        
        # Yolculuğu oluştur (Customer'ı view'da set edeceğiz)
        ride = Ride.objects.create(
            pickup_location=pickup_point,
            dropoff_location=dropoff_point,
            **validated_data
        )
        return ride