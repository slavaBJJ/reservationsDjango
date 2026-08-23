from django.conf import settings
from django.db import migrations, models


BUSINESS_ROLES = (
    'MEMBER',
    'PRODUCER',
    'CRITIC',
    'AFFILIATE_FREE',
    'AFFILIATE_STARTER',
    'AFFILIATE_PREMIUM',
)


def create_business_roles(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    for role in BUSINESS_ROLES:
        Group.objects.get_or_create(name=role)


class Migration(migrations.Migration):

    dependencies = [
        ('catalogue', '0019_review_constraints'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='show',
            name='producers',
            field=models.ManyToManyField(
                blank=True,
                related_name='produced_shows',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.RunPython(
            create_business_roles,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
