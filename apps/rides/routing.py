from django.urls import path

from .consumers import RideConsumer

websocket_urlpatterns = [
    path('ws/rides/<int:ride_id>/', RideConsumer.as_asgi()),
]