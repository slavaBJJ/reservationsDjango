from django.db import models

from .location import Location
from .show import Show


class Representation(models.Model):
    show = models.ForeignKey(
        Show,
        on_delete=models.RESTRICT,
        related_name='representations',
    )
    schedule = models.DateTimeField()
    location = models.ForeignKey(
        Location,
        on_delete=models.RESTRICT,
        null=True,
        related_name='representations',
    )

    def __str__(self):
        return f"{self.show.slug} @ {self.schedule}"

    class Meta:
        db_table = "representations"
