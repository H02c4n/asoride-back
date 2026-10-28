import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Django'yu erken başlat
django_asgi_app = get_asgi_application()

# Django başladıktan SONRA import et
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.conf import settings

from apps.rides.middleware import JWTAuthMiddleware
from apps.rides.routing import websocket_urlpatterns


# WebSocket router — JWT auth + URL routing
websocket_router = JWTAuthMiddleware(URLRouter(websocket_urlpatterns))

# Production'da Origin kontrolü ekle; local'de (DEBUG=True) ekleme
# wscat gibi araçlar Origin göndermediği için local'de reddediliyordu
if not settings.DEBUG:
    websocket_router = AllowedHostsOriginValidator(websocket_router)

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': websocket_router,
})