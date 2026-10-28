from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import DriverStatsView, RideViewSet

router = DefaultRouter()
router.register(r'', RideViewSet, basename='ride')

urlpatterns = [
    path('driver-stats/', DriverStatsView.as_view(), name='ride-driver-stats'),
] + router.urls