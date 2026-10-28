from rest_framework import serializers

from apps.users.serializers import UserReadSerializer
from ..models import Ride


class RideReadSerializer(serializers.ModelSerializer):
    """
    Ride yanıtı. Nested `customer` ve `driver` (tam obje), `my_rating`
    (kullanıcı bu ride'ı puanladı mı?) ve `rating` (verilmiş puan) içerir.
    """
    customer = UserReadSerializer(read_only=True)
    driver = UserReadSerializer(read_only=True)
    my_rating = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()

    class Meta:
        model = Ride
        fields = [
            'id',
            'customer', 'driver',
            'pickup_location', 'dropoff_location',
            'pickup_address', 'dropoff_address',
            'status', 'distance_km', 'price',
            'rating', 'my_rating',
            'created_at', 'updated_at',
        ]
        read_only_fields = fields

    def _get_rating_obj(self, obj):
        try:
            return obj.rating
        except Ride.rating.RelatedObjectDoesNotExist:
            return None

    def get_rating(self, obj):
        r = self._get_rating_obj(obj)
        if not r:
            return None
        return {'score': r.score, 'comment': r.comment}

    def get_my_rating(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        r = self._get_rating_obj(obj)
        if not r:
            return None
        if r.customer_id != request.user.id:
            return None
        return {'score': r.score, 'comment': r.comment}