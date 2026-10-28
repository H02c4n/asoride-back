from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsDriver
from ..services import get_driver_stats


class DriverStatsView(APIView):
    """GET /api/rides/driver-stats/ — Sürücü istatistikleri."""
    permission_classes = [IsAuthenticated, IsDriver]

    def get(self, request):
        return Response(get_driver_stats(request.user))