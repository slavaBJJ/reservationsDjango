from django.db import models

from .artist import Artist
from .type import Type


class ArtistType(models.Model):
    artist = models.ForeignKey(
        Artist,
        on_delete=models.RESTRICT,
        related_name='a_artistTypes',
    )
    type = models.ForeignKey(
        Type,
        on_delete=models.RESTRICT,
        related_name='t_artistTypes',
    )

    def __str__(self):
        return f"{self.artist.firstname} {self.artist.lastname} ({self.type.type})"

    class Meta:
        db_table = 'artist_type'
        constraints = [
            models.UniqueConstraint(
                fields=['artist', 'type'],
                name='unique_artist_type',
            ),
        ]
