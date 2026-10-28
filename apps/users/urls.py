from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import DriverLocationView, LoginView, MeView, RegisterView


urlpatterns = [
    path('register/', RegisterView.as_view(), name='users-register'),
    path('login/', LoginView.as_view(), name='users-login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='users-token-refresh'),
    path('me/', MeView.as_view(), name='users-me'),
    path('driver/location/', DriverLocationView.as_view(), name='users-driver-location'),
]