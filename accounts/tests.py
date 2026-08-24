from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.core.exceptions import ValidationError

from accounts.validators import UppercaseAndSpecialCharacterValidator


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class PasswordResetTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='spectateur',
            email='spectateur@example.com',
            password='ancien-mot-de-passe',
        )

    def test_login_page_links_to_password_reset(self):
        response = self.client.get(reverse('login'))

        self.assertContains(response, reverse('password_reset'))
        self.assertContains(response, 'Mot de passe oublié ?')

    def test_password_reset_generates_email_with_reset_link(self):
        response = self.client.post(
            reverse('password_reset'),
            {'email': self.user.email},
        )

        self.assertRedirects(response, reverse('password_reset_done'))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Réinitialisation', mail.outbox[0].subject)
        self.assertIn('/reset/', mail.outbox[0].body)

    def test_admin_password_reset_page_is_available(self):
        response = self.client.get(reverse('admin_password_reset'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Mot de passe oublié ?')


class SignupAvailabilityTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='artlover',
            email='artlover@example.com',
            password='mot-de-passe-test',
        )
        self.url = reverse('accounts:signup-availability')

    def test_existing_username_is_unavailable_case_insensitively(self):
        response = self.client.get(self.url, {'field': 'username', 'value': 'ArtLover'})

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['available'])

    def test_existing_email_is_unavailable_case_insensitively(self):
        response = self.client.get(
            self.url,
            {'field': 'email', 'value': 'ARTLOVER@example.com'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['available'])

    def test_new_values_are_available(self):
        for field, value in (
            ('username', 'nouveau-membre'),
            ('email', 'nouveau@example.com'),
        ):
            with self.subTest(field=field):
                response = self.client.get(self.url, {'field': field, 'value': value})
                self.assertTrue(response.json()['available'])

    def test_invalid_field_is_rejected(self):
        response = self.client.get(self.url, {'field': 'password', 'value': 'secret'})

        self.assertEqual(response.status_code, 400)

    def test_signup_form_rejects_duplicate_email(self):
        from accounts.forms import UserSignUpForm

        form = UserSignUpForm(data={
            'username': 'autre-membre',
            'email': 'ARTLOVER@example.com',
            'password1': 'Un-mot-de-passe-123!',
            'password2': 'Un-mot-de-passe-123!',
            'first_name': 'Autre',
            'last_name': 'Membre',
            'langue': 'fr',
        })

        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_signup_page_loads_async_validation(self):
        response = self.client.get(reverse('accounts:user-signup'))

        self.assertContains(response, 'data-signup-form')
        self.assertContains(response, 'signup-validation.js')

    def test_layout_uses_vector_logo_and_favicon(self):
        response = self.client.get(reverse('home'))

        self.assertContains(response, 'logo-scene-ouverte.svg', count=2)
        self.assertContains(response, 'favicon.svg')


class PasswordPolicyTests(TestCase):
    def setUp(self):
        self.validator = UppercaseAndSpecialCharacterValidator()

    def test_password_requires_an_uppercase_character(self):
        with self.assertRaisesMessage(ValidationError, 'au moins une majuscule'):
            self.validator.validate('mot-de-passe!')

    def test_password_requires_a_special_character(self):
        with self.assertRaisesMessage(ValidationError, 'au moins un caractère spécial'):
            self.validator.validate('MotDePasse123')

    def test_password_with_uppercase_and_special_character_is_valid(self):
        self.validator.validate('Mot-de-passe-123!')


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class SignupConfirmationTests(TestCase):
    def test_successful_signup_sends_confirmation_and_redirects_to_login(self):
        response = self.client.post(reverse('accounts:user-signup'), {
            'username': 'nouvelle-membre',
            'email': 'nouvelle@example.com',
            'password1': 'Mot-de-passe-123!',
            'password2': 'Mot-de-passe-123!',
            'first_name': 'Camille',
            'last_name': 'Dupont',
            'langue': 'fr',
        })

        self.assertRedirects(response, reverse('login'))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['nouvelle@example.com'])
        self.assertIn('Bienvenue sur Scène ouverte', mail.outbox[0].subject)
        self.assertIn('nouvelle-membre', mail.outbox[0].body)
        user = get_user_model().objects.get(username='nouvelle-membre')
        self.assertTrue(user.check_password('Mot-de-passe-123!'))
        self.assertTrue(user.groups.filter(name='MEMBER').exists())
