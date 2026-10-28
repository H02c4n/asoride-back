from rest_framework import serializers


class SubscribeSerializer(serializers.Serializer):
    """Web Push aboneliği payload'ı (tarayıcıdan gelir)."""
    subscription = serializers.DictField()

    def validate_subscription(self, value):
        endpoint = value.get('endpoint')
        keys = value.get('keys', {})
        if not endpoint:
            raise serializers.ValidationError('endpoint zorunlu.')
        if not keys.get('p256dh') or not keys.get('auth'):
            raise serializers.ValidationError('p256dh ve auth anahtarları zorunlu.')
        return value


class UnsubscribeSerializer(serializers.Serializer):
    endpoint = serializers.CharField()