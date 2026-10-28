"""
Web Push gönderimi. pywebpush + VAPID.
Hatalı/expired abonelikler otomatik temizlenir.
"""
import json
import logging

from django.conf import settings
from pywebpush import webpush, WebPushException

from ..models import PushSubscription
from ..selectors import get_user_subscriptions

logger = logging.getLogger(__name__)


def _is_configured() -> bool:
    return bool(settings.VAPID_PRIVATE_KEY and settings.VAPID_PUBLIC_KEY)


def _build_payload(subscription: PushSubscription, title: str, body: str, url: str, tag: str) -> str:
    return json.dumps({
        'title': title,
        'body': body,
        'url': url,
        'tag': tag,
    })


def send_push_to_user(
    *,
    user,
    title: str,
    body: str,
    url: str = '/',
    tag: str = 'asoride',
) -> int:
    """
    Bir kullanıcının tüm aboneliklerine push gönderir.
    Returns: başarılı gönderim sayısı.
    """
    if not _is_configured():
        logger.warning('[Push] VAPID anahtarları tanımlı değil, atlanıyor')
        return 0

    sent = 0
    for sub in get_user_subscriptions(user):
        payload = _build_payload(sub, title, body, url, tag)
        try:
            webpush(
                subscription_info={
                    'endpoint': sub.endpoint,
                    'keys': {'p256dh': sub.p256dh, 'auth': sub.auth},
                },
                data=payload,
                vapid_private_key=settings.VAPID_PRIVATE_KEY,
                vapid_claims={'sub': f'mailto:{settings.VAPID_ADMIN_EMAIL}'},
            )
            sub.save(update_fields=['last_used_at'])
            sent += 1
        except WebPushException as e:
            status = e.response.status_code if e.response else None
            # 404 / 410 → abonelik geçersiz, sil
            if status in (404, 410):
                logger.info(f'[Push] Geçersiz abonelik silindi: {sub.endpoint[:40]}')
                sub.delete()
            else:
                logger.warning(f'[Push] Gönderim hatası ({status}): {e}')
        except Exception as e:
            logger.error(f'[Push] Beklenmeyen hata: {type(e).__name__}: {e}')

    return sent


def push_new_ride_to_nearby_drivers(ride, radius_meters: int = 10_000) -> None:
    """Yeni ride → çevredeki online sürücülere push."""
    from django.contrib.gis.measure import D
    from apps.users.models import User

    nearby = User.objects.filter(
        role=User.Role.DRIVER,
        is_online=True,
        is_verified_driver=True,
        current_location__isnull=False,
        current_location__distance_lte=(ride.pickup_location, D(m=radius_meters)),
    ).exclude(id=ride.customer_id)[:20]

    for driver in nearby:
        send_push_to_user(
            user=driver,
            title='Yeni Yolculuk Talebi! 🚕',
            body=f'{ride.pickup_address or "Konum"} → {ride.dropoff_address or "Konum"} ({ride.price} TL)',
            url='/driver',
            tag='new-ride-request',
        )