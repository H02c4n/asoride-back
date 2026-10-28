from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.gis.db import models as gis_models


class User(AbstractUser):
    """
    Sistemin tek kullanıcı modeli. Rolüne göre iki farklı davranış sergiler:
    - CUSTOMER: yolculuk talebi oluşturur
    - DRIVER: çevrimiçi olduğunda konumunu günceller, talepleri kabul eder
    """
    class Role(models.TextChoices):
        CUSTOMER = 'CUSTOMER', 'Customer'
        DRIVER = 'DRIVER', 'Driver'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CUSTOMER,
        db_index=True,   # rolüne göre filtreleme sık yapılır
    )
    phone_number = models.CharField(max_length=15, blank=True)

    # Sadece sürücüler için geçerli alanlar
    is_verified_driver = models.BooleanField(default=False)
    is_online = models.BooleanField(default=False, db_index=True)
    current_location = gis_models.PointField(
        null=True, blank=True, geography=True, srid=4326
    )
    location_updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Kullanıcı'
        verbose_name_plural = 'Kullanıcılar'

    def __str__(self):
        return f"{self.username} ({self.role})"

    @property
    def is_customer(self) -> bool:
        return self.role == self.Role.CUSTOMER

    @property
    def is_driver(self) -> bool:
        return self.role == self.Role.DRIVER