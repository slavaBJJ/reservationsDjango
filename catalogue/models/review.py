from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from .show import Show


class Review(models.Model):
    class ModerationStatus(models.TextChoices):
        PENDING = 'pending', 'En attente'
        APPROVED = 'approved', 'Publié'
        REJECTED = 'rejected', 'Refusé'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.RESTRICT,
        related_name='reviews',
    )
    show = models.ForeignKey(
        Show,
        on_delete=models.RESTRICT,
        related_name='reviews',
    )
    review = models.TextField()
    stars = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
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
        related_name='moderated_reviews',
    )
    moderated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True)

    def __str__(self):
        return f"{self.user.username} - {self.show.title} : {self.stars}"

    class Meta:
        db_table = "reviews"
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'show'],
                name='unique_review_user_show',
            ),
        ]
