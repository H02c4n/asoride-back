from django.urls import path
from .consumers import RideConsumer

websocket_urlpatterns = [
    # /ws/rides/<ride_id>/?token=<jwt>
    path('ws/rides/<int:ride_id>/', RideConsumer.as_asgi()),
]