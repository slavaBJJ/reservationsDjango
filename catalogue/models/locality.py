from django.db import models

class LocalityManager(models.Manager):
    def get_by_natural_key(self, postal_code, locality):
        return self.get(postal_code=postal_code, locality=locality)


class Locality(models.Model):
    locality = models.CharField(max_length=30)
    postal_code = models.CharField(max_length=6, null=True, blank=True)

    objects = LocalityManager()

    def __str__(self):
        return f"{self.locality} {self.postal_code}"

    class Meta:
        db_table = 'locality'
        constraints = [
            models.UniqueConstraint(
                fields=["postal_code", "locality"],
                name="unique_postal_code_locality",
            ),
        ]

    def natural_key(self):
        return (self.postal_code, self.locality)

