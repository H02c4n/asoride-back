from django.conf import settings
from django.db import models


class PushSubscription(models.Model):
    """
    Kullanıcının tarayıcı push aboneliği.
    Aynı kullanıcı birden fazla cihaz/tarayıcıda olabilir → her biri ayrı satır.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='push_subscriptions',
    )
    endpoint = models.TextField(unique=True)   # push servis URL'i
    p256dh = models.CharField(max_length=200)  # public key
    auth = models.CharField(max_length=100)    # auth secret
    user_agent = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Push Aboneliği'
        verbose_name_plural = 'Push Abonelikleri'
        indexes = [
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f"{self.user.username} — {self.endpoint[:40]}..."