from django.core.validators import MinValueValidator
from django.db import models

from .representation import Representation
from .reservation import Reservation


class RepresentationReservation(models.Model):
    reservation = models.ForeignKey(
        Reservation,
        on_delete=models.CASCADE,
        related_name='representation_reservations',
    )
    representation = models.ForeignKey(
        Representation,
        on_delete=models.CASCADE,
        related_name='representation_reservations',
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    quantity = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)],
    )

    class Meta:
        db_table = 'representation_reservation'
        constraints = [
            models.UniqueConstraint(
                fields=['reservation', 'representation'],
                name='unique_reservation_representation',
            ),
        ]
