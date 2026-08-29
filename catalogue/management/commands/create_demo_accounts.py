
import os
import secrets
import string

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from catalogue.management.commands.seed_demo_catalogue import DEMO_SHOWS
from catalogue.models import Show, UserMeta
from catalogue.roles import (
    ROLE_AFFILIATE_FREE,
    ROLE_AFFILIATE_PREMIUM,
    ROLE_AFFILIATE_STARTER,
    ROLE_CRITIC,
    ROLE_MEMBER,
    ROLE_PRODUCER,
)


DEMO_ACCOUNTS = (
    ('demo_member', 'DemoMember!2026', (ROLE_MEMBER,), 'Membre'),
    (
        'demo_producer',
        'DemoProducer!2026',
        (ROLE_MEMBER, ROLE_PRODUCER),
        'Producteur',
    ),
    (
        'demo_critic',
        'DemoCritic!2026',
        (ROLE_MEMBER, ROLE_CRITIC),
        'Critique',
    ),
    (
        'demo_affiliate_free',
        'DemoFree!2026',
        (ROLE_MEMBER, ROLE_AFFILIATE_FREE),
        'Affilié Free',
    ),
    (
        'demo_affiliate_starter',
        'DemoStarter!2026',
        (ROLE_MEMBER, ROLE_AFFILIATE_STARTER),
        'Affilié Starter',
    ),
    (
        'demo_affiliate_premium',
        'DemoPremium!2026',
        (ROLE_MEMBER, ROLE_AFFILIATE_PREMIUM),
        'Affilié Premium',
    ),
)


class Command(BaseCommand):
    help = 'Crée les comptes locaux nécessaires à la démonstration du projet.'

    @transaction.atomic
    def handle(self, *args, **options):
        demo_data_allowed = os.getenv('ALLOW_DEMO_DATA') == 'True'

        if not settings.DEBUG and not demo_data_allowed:
            raise CommandError(
                'Commande refusée : définissez ALLOW_DEMO_DATA=True '
                'pour autoriser les données de démonstration.'
            )

        User = get_user_model()
        groups = {
            role: Group.objects.get_or_create(name=role)[0]
            for role in {
                role
                for _, _, account_roles, _ in DEMO_ACCOUNTS
                for role in account_roles
            }
        }

        for username, password, account_roles, label in DEMO_ACCOUNTS:
            user, _ = User.objects.update_or_create(
                username=username,
                defaults={
                    'email': f'{username}@example.test',
                    'first_name': 'Compte',
                    'last_name': label,
                    'is_active': True,
                    'is_staff': False,
                    'is_superuser': False,
                },
            )
            user.set_password(password)
            user.save(update_fields=['password'])
            user.groups.set(groups[role] for role in account_roles)
            UserMeta.objects.update_or_create(
                user=user,
                defaults={'langue': 'fr'},
            )

        admin, admin_created = User.objects.update_or_create(
            username='demo_admin',
            defaults={
                'email': 'demo_admin@example.test',
                'first_name': 'Compte',
                'last_name': 'Administrateur',
                'is_active': True,
                'is_staff': True,
                'is_superuser': True,
            },
        )
        if admin_created or not admin.has_usable_password():
            admin_password = self._admin_password()
            admin.set_password(admin_password)
            admin.save(update_fields=['password'])
        else:
            admin_password = None
        UserMeta.objects.update_or_create(
            user=admin,
            defaults={'langue': 'fr'},
        )

        call_command('seed_demo_catalogue', username='demo_member')
        producer = User.objects.get(username='demo_producer')
        demo_slugs = [definition[0] for definition in DEMO_SHOWS]
        for show in Show.objects.filter(slug__in=demo_slugs):
            show.producers.add(producer)

        self.stdout.write(self.style.SUCCESS(
            'Les 7 comptes de démonstration sont configurés.'
        ))
        if admin_password:
            self.stdout.write(
                f'Mot de passe temporaire demo_admin : {admin_password}'
            )
        else:
            self.stdout.write(
                'Le mot de passe existant de demo_admin a été conservé.'
            )

    @staticmethod
    def _admin_password():
        alphabet = string.ascii_letters + string.digits
        suffix = ''.join(secrets.choice(alphabet) for _ in range(10))
        return f'DemoAdmin!{suffix}'
