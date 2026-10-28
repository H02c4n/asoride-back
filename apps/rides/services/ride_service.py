"""
Ride iş mantığı. State machine burada.
View'lar sadece request/response ile ilgilenir; kurallar burada.
"""
from django.db import transaction
from django.utils import timezone

from apps.core.utils import make_point
from ..models import Ride
from ..selectors import get_active_ride_for_driver
from . import notify_service


# İzin verilen durum geçişleri (state machine)
VALID_TRANSITIONS: dict[str, list[str]] = {
    Ride.Status.REQUESTED: [Ride.Status.ACCEPTED, Ride.Status.CANCELLED],
    Ride.Status.ACCEPTED:  [Ride.Status.ARRIVED, Ride.Status.CANCELLED],
    Ride.Status.ARRIVED:   [Ride.Status.ONGOING, Ride.Status.CANCELLED],
    Ride.Status.ONGOING:   [Ride.Status.COMPLETED],
    Ride.Status.COMPLETED: [],
    Ride.Status.CANCELLED: [],
}


class RideError(Exception):
    """Ride business kural ihlali. View bunu yakalayıp 400 döner."""
    pass


# ------------------------------------------------------------------
# CREATE
# ------------------------------------------------------------------
@transaction.atomic
def create_ride(*, customer, validated_data: dict) -> Ride:
    """Müşteri yeni yolculuk talebi oluşturur."""
    # Sürücü zaten aktif bir ride'da olabilir — bu müşteri için sorun değil
    ride = Ride.objects.create(
        customer=customer,
        pickup_location=make_point(validated_data['pickup_lat'], validated_data['pickup_lng']),
        dropoff_location=make_point(validated_data['dropoff_lat'], validated_data['dropoff_lng']),
        pickup_address=validated_data.get('pickup_address', ''),
        dropoff_address=validated_data.get('dropoff_address', ''),
    )

    # Fiyatı hesapla ve kaydet
    ride.apply_pricing(save=False)
    ride.save(update_fields=['distance_km', 'price', 'updated_at'])

    # Bildirim (Adım 7-9'da aktif)
    notify_service.publish_ride_created(ride)
    notify_service.notify_new_ride_to_nearby_drivers(ride)

    return ride


# ------------------------------------------------------------------
# ACCEPT (sürücü)
# ------------------------------------------------------------------
@transaction.atomic
def accept_ride(*, driver, ride: Ride) -> Ride:
    """Sürücü bir talebi kabul eder."""
    # Zaten bir aktif ride'ı var mı?
    existing = get_active_ride_for_driver(driver)
    if existing and existing.id != ride.id:
        raise RideError('Zaten aktif bir yolculuğunuz var.')

    if ride.driver_id is not None:
        raise RideError('Bu yolculuk başka bir sürücü tarafından alınmış.')

    if ride.status != Ride.Status.REQUESTED:
        raise RideError(f'Bu yolculuk artık talep aşamasında değil ({ride.status}).')

    old_status = ride.status
    ride.driver = driver
    ride.status = Ride.Status.ACCEPTED
    ride.save(update_fields=['driver', 'status', 'updated_at'])

    notify_service.broadcast_ride_status(ride)
    notify_service.publish_ride_status_changed(ride, old_status, ride.status)
    notify_service.notify_ride_event_to_customer(
        ride,
        title='Sürücü Yolda! 🚗',
        body=f'{driver.username} yolculuğunuzu kabul etti.',
        url='/customer',
        tag=f'ride-{ride.id}-accepted',
    )

    return ride


# ------------------------------------------------------------------
# UPDATE STATUS (sürücü)
# ------------------------------------------------------------------
@transaction.atomic
def update_ride_status(*, ride: Ride, driver, new_status: str) -> Ride:
    """Sürücü ride durumunu ilerletir (ARRIVED → ONGOING → COMPLETED)."""
    if ride.driver_id != driver.id:
        raise RideError('Sadece atandığınız yolculukları güncelleyebilirsiniz.')

    allowed = VALID_TRANSITIONS.get(ride.status, [])
    if new_status not in allowed:
        raise RideError(f'{ride.status} → {new_status} geçişi geçersiz.')

    old_status = ride.status
    ride.status = new_status
    update_fields = ['status', 'updated_at']

    if new_status == Ride.Status.COMPLETED:
        ride.completed_at = timezone.now()
        update_fields.append('completed_at')

    ride.save(update_fields=update_fields)

    notify_service.broadcast_ride_status(ride)
    notify_service.publish_ride_status_changed(ride, old_status, new_status)

    if new_status == Ride.Status.ARRIVED:
        notify_service.notify_ride_event_to_customer(
            ride,
            title='Sürücü Konumda! 📍',
            body='Sürücünüz sizi bekliyor.',
            url='/customer',
            tag=f'ride-{ride.id}-arrived',
        )
    elif new_status == Ride.Status.COMPLETED:
        notify_service.notify_ride_event_to_customer(
            ride,
            title='Yolculuk Tamamlandı 🎉',
            body='Bizi tercih ettiğiniz için teşekkürler!',
            url='/customer',
            tag=f'ride-{ride.id}-completed',
        )

    return ride


# ------------------------------------------------------------------
# CANCEL (müşteri veya sürücü)
# ------------------------------------------------------------------
@transaction.atomic
def cancel_ride(*, ride: Ride, actor) -> Ride:
    """Yolculuğu iptal et. Müşteri veya atanmış sürücü iptal edebilir."""
    # Sadece ilgili taraflar
    if actor.id not in (ride.customer_id, ride.driver_id):
        raise RideError('Bu yolculuğu iptal etme yetkiniz yok.')

    # Terminal durumlardan iptal edilemez
    if ride.status in (Ride.Status.COMPLETED, Ride.Status.CANCELLED):
        raise RideError(f'{ride.status} durumundaki yolculuk iptal edilemez.')

    # ONGOING'den iptal edilemez (yolculuk başlamış)
    if ride.status == Ride.Status.ONGOING:
        raise RideError('Devam eden yolculuk iptal edilemez. Lütfen tamamlayın.')

    old_status = ride.status
    ride.status = Ride.Status.CANCELLED
    ride.save(update_fields=['status', 'updated_at'])

    notify_service.broadcast_ride_status(ride)
    notify_service.publish_ride_status_changed(ride, old_status, ride.status)

    return ride