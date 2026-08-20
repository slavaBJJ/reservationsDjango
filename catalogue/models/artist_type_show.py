from django.db import models

from .artist_type import ArtistType
from .show import Show


class ArtistTypeShow(models.Model):
    show = models.ForeignKey(
        Show,
        on_delete=models.CASCADE,
        related_name='artistTypeShows',
    )
    artist_type = models.ForeignKey(
        ArtistType,
        on_delete=models.CASCADE,
        related_name='artistTypeShows',
    )

    class Meta:
        db_table = 'artist_type_show'
        constraints = [
            models.UniqueConstraint(
                fields=['show', 'artist_type'],
                name='unique_show_artist_type',
            ),
        ]
