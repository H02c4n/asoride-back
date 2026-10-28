"""
Puanlama iş mantığı. Sadece COMPLETED + ilgili müşteri + tek puan.
"""
from django.db import transaction

from ..models import Rating, Ride


class RatingError(Exception):
    pass


@transaction.atomic
def create_rating(*, ride: Ride, customer, data: dict) -> Rating:
    if ride.customer_id != customer.id:
        raise RatingError('Sadece bu yolculuğun müşterisi puan verebilir.')

    if ride.status != Ride.Status.COMPLETED:
        raise RatingError('Sadece tamamlanmış yolculuklar puanlanabilir.')

    if hasattr(ride, 'rating') and ride.rating is not None:
        raise RatingError('Bu yolculuk zaten puanlanmış.')

    return Rating.objects.create(
        ride=ride,
        customer=customer,
        driver=ride.driver,
        score=data['score'],
        comment=data.get('comment', ''),
    )