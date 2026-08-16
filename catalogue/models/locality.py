from django.db import models

class Locality(models.Model):
    locality = models.CharField(max_length=30)
    postal_code = models.CharField(max_length=6, null=True, blank=True)

    def __str__(self):
        return f"{self.locality} {self.postal_code}"

    class Meta:
        db_table = 'locality'
