from django.conf import settings
from django.contrib.gis.db import models as gis_models
from django.db import models

from apps.core.models import BaseModel
from apps.core.utils import calculate_price_from_points


class Ride(BaseModel):
    """
    Yolculuk. State Machine:
    REQUESTED → ACCEPTED → ARRIVED → ONGOING → COMPLETED
    Herhangi bir aşamada CANCELLED olabilir (COMPLETED hariç).
    """

    class Status(models.TextChoices):
        REQUESTED = 'REQUESTED', 'Talep Edildi'
        ACCEPTED = 'ACCEPTED', 'Kabul Edildi'
        ARRIVED = 'ARRIVED', 'Sürücü Konumda'
        ONGOING = 'ONGOING', 'Devam Ediyor'
        COMPLETED = 'COMPLETED', 'Tamamlandı'
        CANCELLED = 'CANCELLED', 'İptal Edildi'

    # Taraflar
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,          # müşteri silinemez, önce ride'lar çözülsün
        related_name='rides_as_customer',
    )
    driver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rides_as_driver',
    )

    # Konumlar (PostGIS)
    pickup_location = gis_models.PointField(geography=True, srid=4326)
    dropoff_location = gis_models.PointField(geography=True, srid=4326)
    pickup_address = models.CharField(max_length=255, blank=True)
    dropoff_address = models.CharField(max_length=255, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Durum ve fiyat
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.REQUESTED,
        db_index=True,
    )
    distance_km = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True
    )
    price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )

    class Meta(BaseModel.Meta):
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['driver', 'status']),
            models.Index(fields=['customer', '-created_at']),
        ]

    def __str__(self):
        return f"Ride #{self.id} [{self.status}] {self.customer.username}"

    # ------------------------------------------------------------------
    # İş metotları (kısa, tek sorumluluk)
    # ------------------------------------------------------------------
    def calculate_pricing(self):
        """PostGIS noktalarından fiyat + mesafe hesapla (DB'ye yazmaz)."""
        return calculate_price_from_points(self.pickup_location, self.dropoff_location)

    def apply_pricing(self, save=True):
        """Fiyatı ve mesafeyi hesaplayıp kayda yaz."""
        pricing = self.calculate_pricing()
        self.distance_km = pricing['distance_km']
        self.price = pricing['price']
        if save:
            self.save(update_fields=['distance_km', 'price', 'updated_at'])


class Rating(BaseModel):
    """
    Yolculuk başına TEK puan (OneToOne).
    Sadece COMPLETED durumundaki ride'lar puanlanabilir (Adım 5'te kontrol).
    """

    ride = models.OneToOneField(
        Ride,
        on_delete=models.CASCADE,
        related_name='rating',
    )
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ratings_given',
    )
    driver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ratings_received',
    )
    score = models.PositiveSmallIntegerField()  # 1-5, validate_score serializer'da
    comment = models.TextField(max_length=500, blank=True)

    class Meta(BaseModel.Meta):
        indexes = [
            models.Index(fields=['driver', '-created_at']),
        ]

    def __str__(self):
        return f"Ride #{self.ride_id} → {self.score}★"