from django.contrib.auth.models import AbstractUser
from django.contrib.gis.db import models as gis_models
from django.db import models

class User(AbstractUser):
    class Role(models.TextChoices):
        CUSTOMER = 'CUSTOMER', 'Customer'
        DRIVER = 'DRIVER', 'Driver'

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CUSTOMER)
    phone_number = models.CharField(max_length=15, blank=True)
    
    # Sadece Sürücüler için geçerli alanlar
    is_verified_driver = models.BooleanField(default=False) # Admin onayı
    is_online = models.BooleanField(default=False)          # Sürücü müsait mi?
    
    # Sürücünün anlık konumu (PostGIS Point: Enlem/Boylam)
    current_location = gis_models.PointField(
        null=True, blank=True, geography=True, srid=4326
    )

    def __str__(self):
        return f"{self.username} ({self.role})"