"""
Bir ride'a ait WebSocket kanalı.

Akış:
- Sürücü: `{"type": "location_update", "lat": ..., "lng": ...}` gönderir
  → DB güncellenir → gruba yayın (müşteri görür)
- Müşteri: sadece dinler (location + ride_status)
- Durum değişiklikleri `notify_service.broadcast_ride_status` üzerinden gelir
"""
import json
import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)


class RideConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        user = self.scope['user']
        if user.is_anonymous:
            await self.close(code=4001)
            return

        self.ride_id = self.scope['url_route']['kwargs']['ride_id']
        self.group_name = f'ride_{self.ride_id}'

        if not await self._user_has_ride_access(user):
            await self.close(code=4003)
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        await self.send(text_data=json.dumps({
            'type': 'connected',
            'ride_id': self.ride_id,
            'role': user.role,
        }))

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name, self.channel_name
            )

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return

        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        msg_type = data.get('type')
        user = self.scope['user']

        if msg_type == 'location_update':
            if user.role != 'DRIVER':
                return  # sadece sürücü konum gönderir

            lat = data.get('lat')
            lng = data.get('lng')
            if lat is None or lng is None:
                return

            try:
                await self._save_location(user, lat, lng)
            except Exception as e:
                logger.error(f'[WS] Konum kaydedilemedi: {e}')
                return

            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'location_broadcast',
                    'lat': lat,
                    'lng': lng,
                    'driver_id': user.id,
                },
            )

        elif msg_type == 'ping':
            await self.send(text_data=json.dumps({'type': 'pong'}))

    # ------------------------------------------------------------------
    # Group → Client
    # ------------------------------------------------------------------
    async def location_broadcast(self, event):
        await self.send(text_data=json.dumps({
            'type': 'driver_location',
            'lat': event['lat'],
            'lng': event['lng'],
            'driver_id': event['driver_id'],
        }))

    async def ride_status_broadcast(self, event):
        await self.send(text_data=json.dumps({
            'type': 'ride_status',
            'status': event['status'],
        }))

    # ------------------------------------------------------------------
    # DB helpers
    # ------------------------------------------------------------------
    @database_sync_to_async
    def _user_has_ride_access(self, user) -> bool:
        from ..selectors import get_ride_by_id
        ride = get_ride_by_id(self.ride_id)
        if not ride:
            return False
        return ride.customer_id == user.id or ride.driver_id == user.id

    @database_sync_to_async
    def _save_location(self, user, lat, lng):
        from apps.users.services import update_driver_location
        update_driver_location(user=user, lat=lat, lng=lng)