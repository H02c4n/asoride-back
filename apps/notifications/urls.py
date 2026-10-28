from django.urls import path
from .views import SubscribeView, UnsubscribeView, VapidPublicKeyView

urlpatterns = [
    path('vapid-public-key/', VapidPublicKeyView.as_view(), name='push-vapid-key'),
    path('subscribe/', SubscribeView.as_view(), name='push-subscribe'),
    path('unsubscribe/', UnsubscribeView.as_view(), name='push-unsubscribe'),
]