from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from django.conf import settings

from .models import PushSubscription
from .serializers import SubscribeSerializer, UnsubscribeSerializer


class VapidPublicKeyView(APIView):
    """GET /api/notifications/vapid-public-key/ — frontend abone olurken lazım."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({'publicKey': settings.VAPID_PUBLIC_KEY})


class SubscribeView(APIView):
    """POST /api/notifications/subscribe/ — abonelik kaydet."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SubscribeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        sub_data = serializer.validated_data['subscription']
        keys = sub_data['keys']

        PushSubscription.objects.update_or_create(
            endpoint=sub_data['endpoint'],
            defaults={
                'user': request.user,
                'p256dh': keys['p256dh'],
                'auth': keys['auth'],
                'user_agent': request.META.get('HTTP_USER_AGENT', '')[:200],
            },
        )
        return Response({'detail': 'Abonelik kaydedildi.'},
                        status=status.HTTP_201_CREATED)


class UnsubscribeView(APIView):
    """POST /api/notifications/unsubscribe/ — abonelik sil."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = UnsubscribeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        PushSubscription.objects.filter(
            user=request.user,
            endpoint=serializer.validated_data['endpoint'],
        ).delete()
        return Response({'detail': 'Abonelik silindi.'})