"""
Bu dosya sadece YAZMA işlemlerini içerir.
View'lar bu fonksiyonları çağırır; iş mantığı burada test edilebilir.
"""
from django.contrib.gis.geos import Point
from django.utils import timezone

from .models import User


def register_user(
    *,
    username: str,
    email: str,
    password: str,
    password2: str,
    role: str,
    **extra,
) -> User:
    """Kayıt işlemi. password2 view'da validate edilir, burada garanti."""
    if password != password2:
        raise ValueError('Şifreler eşleşmiyor.')

    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        role=role,
        **extra,
    )
    return user


def update_driver_location(user: User, *, lat: float, lng: float) -> User:
    """
    Sürücünün konumunu ve çevrimiçi durumunu güncelle.
    PostGIS Point(lng, lat) sırasına dikkat!
    """
    if not user.is_driver:
        raise PermissionError('Sadece sürücüler konum güncelleyebilir.')

    user.current_location = Point(lng, lat, srid=4326)
    user.location_updated_at = timezone.now()
    user.is_online = True
    user.save(
        update_fields=[
            'current_location',
            'location_updated_at',
            'is_online',
        ]
    )
    return user


def set_driver_offline(user: User) -> User:
    """Sürücüyü çevrimdışı yap (konum korunur)."""
    if not user.is_driver:
        raise PermissionError('Sadece sürücüler çevrimdışı olabilir.')

    user.is_online = False
    user.save(update_fields=['is_online'])
    return user