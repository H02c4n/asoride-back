from .base import *  # noqa
import os

DEBUG = True
ALLOWED_HOSTS = ['*']

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': os.environ.get('DB_NAME', 'asoride'),
        'USER': os.environ.get('DB_USER', 'asoride_user'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'asoride_pass'),
        'HOST': os.environ.get('DB_HOST', 'db'),
        'PORT': '5432',
    }
}