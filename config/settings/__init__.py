import os

DJANGO_ENV = os.environ.get('DJANGO_ENV', 'development')

if DJANGO_ENV == 'production':
    from .production import *  # noqa
else:
    from .development import *  # noqa