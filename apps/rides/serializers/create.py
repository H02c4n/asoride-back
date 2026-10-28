from rest_framework import serializers

from apps.core.utils import haversine_km


class RideCreateSerializer(serializers.Serializer):
    """
    Ride oluşturma payload'ı. İş mantığı (fiyat hesabı, Kafka) Adım 5'te service'te.
    Burada sadece validasyon yapılır.
    """
    pickup_lat = serializers.FloatField(min_value=-90, max_value=90)
    pickup_lng = serializers.FloatField(min_value=-180, max_value=180)
    pickup_address = serializers.CharField(max_length=255, required=False, allow_blank=True)

    dropoff_lat = serializers.FloatField(min_value=-90, max_value=90)
    dropoff_lng = serializers.FloatField(min_value=-180, max_value=180)
    dropoff_address = serializers.CharField(max_length=255, required=False, allow_blank=True)

    def validate(self, attrs):
        distance = haversine_km(
            attrs['pickup_lat'], attrs['pickup_lng'],
            attrs['dropoff_lat'], attrs['dropoff_lng'],
        )
        if distance < 0.1:
            raise serializers.ValidationError(
                'Alış ve varış noktaları çok yakın (min 100 metre).'
            )
        if distance > 100:
            raise serializers.ValidationError(
                'Mesafe çok uzun (max 100 km). Lütfen şehir içi bir nokta seçin.'
            )
        attrs['_distance_km'] = round(distance, 2)
        return attrs