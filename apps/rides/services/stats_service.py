"""
Sürücü istatistikleri. Salt okuma.
"""
from django.db.models import Avg, Sum
from django.utils import timezone

from ..models import Rating, Ride


def get_driver_stats(driver) -> dict:
    completed = Ride.objects.filter(driver=driver, status=Ride.Status.COMPLETED)

    total_earnings = completed.aggregate(t=Sum('price'))['t'] or 0
    total_rides = completed.count()

    today = timezone.localdate()
    today_qs = completed.filter(created_at__date=today)
    today_earnings = today_qs.aggregate(t=Sum('price'))['t'] or 0
    today_rides = today_qs.count()

    rating_qs = Rating.objects.filter(driver=driver)
    avg_rating = rating_qs.aggregate(avg=Avg('score'))['avg']

    return {
        'total_earnings': float(total_earnings),
        'total_rides': total_rides,
        'today_earnings': float(today_earnings),
        'today_rides': today_rides,
        'average_rating': round(avg_rating, 2) if avg_rating else None,
        'total_ratings': rating_qs.count(),
    }