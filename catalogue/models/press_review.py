from django.conf import settings
from django.db import models

from .show import Show


class PressReview(models.Model):
    class ModerationStatus(models.TextChoices):
        PENDING = 'pending', 'En attente'
        APPROVED = 'approved', 'Publié'
        REJECTED = 'rejected', 'Refusé'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.RESTRICT,
        related_name='press_reviews',
    )
    show = models.ForeignKey(
        Show,
        on_delete=models.RESTRICT,
        related_name='press_reviews',
    )
    title = models.CharField(max_length=255)
    content = models.TextField(blank=True)
    url = models.URLField(blank=True)
    moderation_status = models.CharField(
        max_length=10,
        choices=ModerationStatus.choices,
        default=ModerationStatus.PENDING,
    )
    moderated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='moderated_press_reviews',
    )
    moderated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'{self.title} — {self.show.title}'

    class Meta:
        db_table = 'press_reviews'
        ordering = ('-created_at', '-pk')
