"""
Sadece OKUMA sorguları. İş mantığı yok.
View'lar bu fonksiyonları çağırır.
"""
from django.db.models import Q, Prefetch

from .models import Ride


def get_ride_by_id(ride_id: int) -> Ride | None:
    """Tek ride — ilişkileri eager load ederek."""
    return (
        Ride.objects
        .select_related('customer', 'driver', 'rating')
        .filter(id=ride_id)
        .first()
    )


def get_rides_for_customer(customer):
    """Müşterinin tüm yolculukları (aktif + geçmiş)."""
    return (
        Ride.objects
        .filter(customer=customer)
        .select_related('driver')
        .order_by('-created_at')
    )


def get_active_ride_for_driver(driver):
    """Sürücünün devam eden aktif yolculuğu (varsa)."""
    return (
        Ride.objects
        .filter(
            driver=driver,
            status__in=[
                Ride.Status.ACCEPTED,
                Ride.Status.ARRIVED,
                Ride.Status.ONGOING,
            ],
        )
        .select_related('customer')
        .first()
    )


def get_available_rides_for_driver(driver):
    """
    Sürücünün kendi kabul ettiği aktif + sahipsiz REQUESTED yolculuklar.
    Sürücü henüz bir ride kabul etmediyse yalnızca REQUESTED listelenir.
    """
    return (
        Ride.objects
        .filter(
            Q(driver=driver) |
            Q(driver__isnull=True, status=Ride.Status.REQUESTED)
        )
        .select_related('customer', 'driver')
        .order_by('-created_at')
    )


def get_completed_rides_for_driver(driver):
    """Sürücünün tamamladığı tüm yolculuklar (istatistik için)."""
    return (
        Ride.objects
        .filter(driver=driver, status=Ride.Status.COMPLETED)
        .only('id', 'price', 'created_at', 'distance_km')
    )