from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalogue.models import (
    Category,
    Locality,
    Location,
    Price,
    Representation,
    RepresentationReservation,
    Reservation,
    Show,
)


DEMO_SHOWS = (
    ('la-nuit-des-etoiles', 'La Nuit des étoiles', 95, 12),
    ('rythmes-de-bruxelles', 'Rythmes de Bruxelles', 80, 19),
    ('le-secret-du-rideau', 'Le Secret du rideau', 105, 26),
    ('danse-des-lumieres', 'La Danse des lumières', 75, 33),
    ('rire-en-scene', 'Rire en scène', 90, 40),
    ('les-voix-du-temps', 'Les Voix du temps', 70, 47),
    ('voyage-imaginaire', 'Le Voyage imaginaire', 110, 54),
)

DEMO_CATEGORIES = (
    ('comedie', 'Comédie', 'Spectacles humoristiques et comiques.'),
    ('theatre', 'Théâtre', 'Pièces de théâtre et créations scéniques.'),
    ('non-classe', 'Non classé', 'Catégorie attribuée par défaut.'),
)

DEMO_CATEGORY_BY_SHOW = {
    'rire-en-scene': 'comedie',
    'le-secret-du-rideau': 'theatre',
}


class Command(BaseCommand):
    help = 'Crée sept spectacles complets pour tester réservation et avis.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            help='Compte recevant les réservations passées nécessaires aux avis.',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        review_user = None
        if options['username']:
            User = get_user_model()
            try:
                review_user = User.objects.get(username=options['username'])
            except User.DoesNotExist as exc:
                raise CommandError('Utilisateur introuvable.') from exc

        locality, _ = Locality.objects.get_or_create(
            postal_code='1000', locality='Bruxelles',
        )
        location, _ = Location.objects.update_or_create(
            slug='theatre-demo-bruxelles',
            defaults={
                'designation': 'Théâtre Démo Bruxelles',
                'address': '1 Place des Arts',
                'locality': locality,
                'website': 'https://example.com/theatre-demo',
                'phone': '+32 2 000 00 00',
            },
        )
        full_price, _ = Price.objects.get_or_create(
            type='Démo plein tarif', end_date=None,
            defaults={
                'price': '24.00',
                'description': 'Tarif standard de démonstration',
            },
        )
        reduced_price, _ = Price.objects.get_or_create(
            type='Démo tarif réduit', end_date=None,
            defaults={
                'price': '14.00',
                'description': 'Tarif réduit de démonstration',
            },
        )

        categories = {
            slug: Category.objects.update_or_create(
                slug=slug,
                defaults={'name': name, 'description': description},
            )[0]
            for slug, name, description in DEMO_CATEGORIES
        }

        now = timezone.now()
        created_count = 0
        for index, (slug, title, duration, future_days) in enumerate(DEMO_SHOWS):
            show, created = Show.objects.update_or_create(
                slug=slug,
                defaults={
                    'title': title,
                    'description': (
                        'Un spectacle complet pour tester la réservation, '
                        'les tarifs et les avis.'
                    ),
                    'duration': duration,
                    'created_in': now.year,
                    'location': location,
                    'bookable': True,
                    'category': categories[
                        DEMO_CATEGORY_BY_SHOW.get(slug, 'non-classe')
                    ],
                },
            )
            created_count += int(created)
            show.prices.set((full_price, reduced_price))

            future_schedule = (now + timedelta(days=future_days)).replace(
                hour=18 + index % 3, minute=0, second=0, microsecond=0,
            )
            past_schedule = (now - timedelta(days=7 + index)).replace(
                hour=19, minute=0, second=0, microsecond=0,
            )
            Representation.objects.get_or_create(
                show=show, schedule=future_schedule,
                defaults={'location': location},
            )
            past_representation, _ = Representation.objects.get_or_create(
                show=show, schedule=past_schedule,
                defaults={'location': location},
            )

            if review_user and not RepresentationReservation.objects.filter(
                reservation__user=review_user,
                representation=past_representation,
            ).exists():
                reservation = Reservation.objects.create(
                    user=review_user, status='confirmée',
                )
                RepresentationReservation.objects.create(
                    reservation=reservation,
                    representation=past_representation,
                    price=reduced_price.price,
                    quantity=1,
                )

        self.stdout.write(self.style.SUCCESS(
            f'Catalogue prêt : 7 spectacles ({created_count} nouveaux).'
        ))
        if review_user:
            self.stdout.write(
                f'{review_user.username} peut publier un avis sur les 7 spectacles.'
            )
