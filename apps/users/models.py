from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.gis.db import models as gis_models

class User(AbstractUser):
    class Role(models.TextChoices):
        CUSTOMER = 'CUSTOMER', 'Customer'
        DRIVER = 'DRIVER', 'Driver'

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CUSTOMER)
    phone_number = models.CharField(max_length=15, blank=True)
    is_verified_driver = models.BooleanField(default=False)
    is_online = models.BooleanField(default=False)
    current_location = gis_models.PointField(null=True, blank=True, geography=True, srid=4326)


