import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.gis.geos import Point


class RideConsumer(AsyncWebsocketConsumer):
    """
    Bir yolculuğa (ride) ait WebSocket kanalı.
    - Sürücü: 'location_update' mesajı gönderir → DB güncellenir → Müşteriye yayınlanır.
    - Müşteri: Sadece dinler (konum ve durum güncellemelerini alır).
    """

    async def connect(self):
        user = self.scope['user']
        if user.is_anonymous:
            await self.close(code=4001)
            return

        self.ride_id = self.scope['url_route']['kwargs']['ride_id']
        self.group_name = f'ride_{self.ride_id}'

        # Kullanıcının bu yolculuğa erişim yetkisi var mı?
        has_access = await self._user_has_ride_access(user)
        if not has_access:
            await self.close(code=4003)
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        await self.send(text_data=json.dumps({
            'type': 'connected',
            'message': f'Ride #{self.ride_id} kanalına bağlandınız.',
            'role': user.role,
        }))

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name, self.channel_name
            )

    async def receive(self, text_data):
        user = self.scope['user']
        data = json.loads(text_data)
        message_type = data.get('type')

        if message_type == 'location_update':
            # Sadece sürücü konum gönderebilir
            if user.role != 'DRIVER':
                return

            lat = data.get('lat')
            lng = data.get('lng')
            if lat is None or lng is None:
                return

            # DB'yi güncelle
            await self._update_driver_location(user, lat, lng)

            # Gruptaki herkese (müşteriye) yayınla
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'location_broadcast',
                    'lat': lat,
                    'lng': lng,
                    'driver_id': user.id,
                }
            )

        elif message_type == 'ping':
            await self.send(text_data=json.dumps({'type': 'pong'}))

    # ------------------------------------------------------------------
    # Group'tan gelen mesajları işleyiciler
    # ------------------------------------------------------------------
    async def location_broadcast(self, event):
        """Sürücüden gelen konumu istemciye ilet."""
        await self.send(text_data=json.dumps({
            'type': 'driver_location',
            'lat': event['lat'],
            'lng': event['lng'],
            'driver_id': event['driver_id'],
        }))

    async def ride_status_broadcast(self, event):
        """Yolculuk durum değişikliğini istemciye ilet."""
        await self.send(text_data=json.dumps({
            'type': 'ride_status',
            'status': event['status'],
        }))

    # ------------------------------------------------------------------
    # DB Yardımcıları
    # ------------------------------------------------------------------
    @database_sync_to_async
    def _user_has_ride_access(self, user):
        from .models import Ride
        try:
            ride = Ride.objects.get(id=self.ride_id)
        except Ride.DoesNotExist:
            return False
        return ride.customer_id == user.id or ride.driver_id == user.id

    @database_sync_to_async
    def _update_driver_location(self, driver, lat, lng):
        driver.current_location = Point(lng, lat, srid=4326)
        driver.save(update_fields=['current_location', 'updated_at'])