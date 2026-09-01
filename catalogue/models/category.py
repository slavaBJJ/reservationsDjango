from django.db import models

class Category(models.Model):
    name =models.CharField(max_length=60, unique = True)
    slug = models.SlugField(max_length=60, unique=True)
    description= models.TextField(blank = True)

    def __str__(self):
        return self.name

    class Meta:
        db_table ='categories'
        verbose_name_plural = 'categories'