from django.db import models


class BaseModel(models.Model):
    """
    Tüm modellerin miras alacağı soyut temel sınıf.

    - created_at: oluşturulma zamanı (auto)
    - updated_at: son güncelleme (auto)
    - is_deleted: soft delete (fiziksel silme yerine işaretleme)

    Meta.abstract = True olduğu için DB'de tablo oluşturmaz;
    sadece miras alan sınıflara bu alanları enjekte eder.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        abstract = True
        ordering = ['-created_at']

    def soft_delete(self, save=True):
        """Fiziksel silme yerine işaretle. İlişkiler korunur."""
        self.is_deleted = True
        if save:
            self.save(update_fields=['is_deleted', 'updated_at'])

    def restore(self, save=True):
        """Soft-deleted kaydı geri getir."""
        self.is_deleted = False
        if save:
            self.save(update_fields=['is_deleted', 'updated_at'])