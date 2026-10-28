from .models import PushSubscription


def get_user_subscriptions(user):
    """Kullanıcının tüm abonelikleri (birden fazla cihaz)."""
    return PushSubscription.objects.filter(user=user)