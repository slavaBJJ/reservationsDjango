from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def migrate_validation_status(apps, schema_editor):
    Review = apps.get_model('catalogue', 'Review')
    Review.objects.filter(validated=True).update(moderation_status='approved')
    Review.objects.filter(validated=False).update(moderation_status='pending')


def restore_validation_status(apps, schema_editor):
    Review = apps.get_model('catalogue', 'Review')
    Review.objects.filter(moderation_status='approved').update(validated=True)
    Review.objects.exclude(moderation_status='approved').update(validated=False)


class Migration(migrations.Migration):

    dependencies = [
        ('catalogue', '0020_show_producers_and_business_roles'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='review',
            name='moderation_status',
            field=models.CharField(
                choices=[
                    ('pending', 'En attente'),
                    ('approved', 'Publié'),
                    ('rejected', 'Refusé'),
                ],
                default='pending',
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name='review',
            name='moderated_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='review',
            name='moderated_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='moderated_reviews',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.RunPython(
            migrate_validation_status,
            reverse_code=restore_validation_status,
        ),
        migrations.RemoveField(
            model_name='review',
            name='validated',
        ),
    ]
