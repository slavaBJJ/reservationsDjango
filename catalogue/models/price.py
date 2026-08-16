from django.core.validators import MinValueValidator
from django.db import models
import datetime

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

    def __str__(self):
        return  f"{self.price} : {self.price} €"

    class Meta:
        db_table = "price"