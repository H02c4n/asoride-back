"""
Bu dosya sadece OKUMA sorgularını içerir.
İş mantığı yok, sadece veri çekme.
"""
from .models import User


def get_user_by_username(username: str) -> User | None:
    return User.objects.filter(username=username).first()


def get_driver_by_id(user_id: int) -> User | None:
    return User.objects.filter(id=user_id, role=User.Role.DRIVER).first()


def get_online_verified_drivers_within(point, radius_meters: int = 10_000):
    """
    Belirli bir nokta etrafında çevrimiçi ve onaylı sürücüler.
    PostGIS `distance_lte` ile DB seviyesinde filtreleme yapar.
    """
    from django.contrib.gis.measure import D

    return User.objects.filter(
        role=User.Role.DRIVER,
        is_online=True,
        is_verified_driver=True,
        current_location__isnull=False,
        current_location__distance_lte=(point, D(m=radius_meters)),
    ).distinct()


def get_driver_stats_queryset(driver: User):
    """Sürücü istatistikleri için Ride queryset'i (Adım 5'te kullanılır)."""
    from apps.rides.models import Ride
    return Ride.objects.filter(driver=driver, status=Ride.Status.COMPLETED)