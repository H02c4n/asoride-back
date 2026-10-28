"""
Bildirim köprüsü: WebSocket + Kafka + Push.
Şu an sadece WebSocket grup yayını yapılıyor; Kafka ve Push
Adım 7-9'da bu dosyaya eklenecek. Hataları yutar → HTTP akışı bozulmaz.
"""
import logging

logger = logging.getLogger(__name__)


def broadcast_ride_status(ride) -> None:
    """Yolculuk grubuna durum değişikliği yayını (WebSocket)."""
    try:
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer

        layer = get_channel_layer()
        if not layer:
            return
        async_to_sync(layer.group_send)(
            f'ride_{ride.id}',
            {
                'type': 'ride_status_broadcast',
                'status': ride.status,
            },
        )
    except Exception as e:
        logger.warning(f'[WS] broadcast failed: {e}')


def publish_ride_created(ride) -> None:
    """Kafka'ya ride.requested event'i (Adım 8'de aktif)."""
    try:
        from apps.rides.kafka.producer import publish_ride_requested
        publish_ride_requested(ride)
    except ImportError:
        pass  # Kafka henüz yok
    except Exception as e:
        logger.warning(f'[Kafka] publish failed: {e}')


def publish_ride_status_changed(ride, old_status: str, new_status: str) -> None:
    """Kafka'ya ride.status_changed event'i (Adım 8'de aktif)."""
    try:
        from apps.rides.kafka.producer import publish_ride_status_changed as _pub
        _pub(ride, old_status, new_status)
    except ImportError:
        pass
    except Exception as e:
        logger.warning(f'[Kafka] publish status failed: {e}')


def notify_new_ride_to_nearby_drivers(ride) -> None:
    """Yeni ride talebi → çevredeki online sürücülere push (Adım 9'da aktif)."""
    try:
        from notifications.services.push_service import push_new_ride_to_nearby_drivers
        push_new_ride_to_nearby_drivers(ride)
    except ImportError:
        pass
    except Exception as e:
        logger.warning(f'[Push] notify failed: {e}')


def notify_ride_event_to_customer(ride, title: str, body: str, url: str, tag: str) -> None:
    """Müşteriye push (Adım 9'da aktif)."""
    try:
        from notifications.services.push_service import send_push_to_user
        send_push_to_user(user=ride.customer, title=title, body=body, url=url, tag=tag)
    except ImportError:
        pass
    except Exception as e:
        logger.warning(f'[Push] notify customer failed: {e}')