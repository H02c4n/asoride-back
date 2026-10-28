from rest_framework import serializers

from apps.users.serializers import UserReadSerializer
from ..models import Rating


class RatingReadSerializer(serializers.ModelSerializer):
    customer = UserReadSerializer(read_only=True)
    driver = UserReadSerializer(read_only=True)

    class Meta:
        model = Rating
        fields = ['id', 'ride', 'customer', 'driver', 'score', 'comment', 'created_at']
        read_only_fields = fields


class RatingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = ['score', 'comment']
        # ride/customer/driver view'da atanır → read_only

    def validate_score(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError('Puan 1 ile 5 arasında olmalıdır.')
        return value