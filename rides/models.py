from django.db import models
from django.conf import settings
from django.contrib.gis.db import models as gis_models
from core.models import BaseModel

class Ride(BaseModel):
    class Status(models.TextChoices):
        REQUESTED = 'REQUESTED', 'Müşteri Talep Etti'
        ACCEPTED = 'ACCEPTED', 'Sürücü Kabul Etti'
        ARRIVED = 'ARRIVED', 'Sürücü Konuma Geldi'
        ONGOING = 'ONGOING', 'Yolculuk Başladı'
        COMPLETED = 'COMPLETED', 'Yolculuk Bitti'
        CANCELLED = 'CANCELLED', 'İptal Edildi'

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='rides_as_customer'
    )
    driver = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='rides_as_driver'
    )

    # Başlangıç ve Bitiş Noktaları
    pickup_location = gis_models.PointField(geography=True, srid=4326)
    dropoff_location = gis_models.PointField(geography=True, srid=4326)
    
    # Başlangıç ve Bitiş Adres Metinleri (Haritadan gelen isimler)
    pickup_address = models.CharField(max_length=255, blank=True)
    dropoff_address = models.CharField(max_length=255, blank=True)

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.REQUESTED)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"Ride #{self.id} - {self.status}"