from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('catalogue', '0020_show_producers_and_business_roles'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PressReview',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                ('title', models.CharField(max_length=255)),
                ('content', models.TextField(blank=True)),
                ('url', models.URLField(blank=True)),
                (
                    'moderation_status',
                    models.CharField(
                        choices=[
                            ('pending', 'En attente'),
                            ('approved', 'Publié'),
                            ('rejected', 'Refusé'),
                        ],
                        default='pending',
                        max_length=10,
                    ),
                ),
                ('moderated_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(blank=True, null=True)),
                (
                    'moderated_by',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='moderated_press_reviews',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    'show',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.RESTRICT,
                        related_name='press_reviews',
                        to='catalogue.show',
                    ),
                ),
                (
                    'user',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.RESTRICT,
                        related_name='press_reviews',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                'db_table': 'press_reviews',
                'ordering': ('-created_at', '-pk'),
            },
        ),
    ]
