from django.core.validators import MinValueValidator
from django.db import models


class PriceManager(models.Manager):
    def get_by_natural_key(self, type, start_date, end_date):
        return self.get(type=type, start_date=start_date, end_date=end_date)


class Price(models.Model):
    type = models.CharField(max_length=30,null=True, blank=True)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    description = models.CharField(max_length=255, null=True, blank= True)
    start_date = models.DateField(auto_now_add=True)
    end_date= models.DateField(null=True, blank=True)

    objects = PriceManager()

    def __str__(self):
        return f"{self.type} : {self.price} €"

    class Meta:
        db_table = "price"
        constraints = [
            models.UniqueConstraint(
                fields=['type', 'start_date', 'end_date'],
                name='unique_price_period',
            ),
        ]

    def natural_key(self):
        return (self.type, self.start_date, self.end_date)
