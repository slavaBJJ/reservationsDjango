from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from catalogue.models import (
    Locality,
    Location,
    Price,
    Representation,
    RepresentationReservation,
    Reservation,
    Review,
    Show,
)


class ShowCatalogueTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        locality = Locality.objects.create(postal_code='1000', locality='Bruxelles')
        cls.location = Location.objects.create(
            slug='theatre-royal',
            designation='Théâtre Royal',
            locality=locality,
        )

        for index in range(12):
            Show.objects.create(
                slug=f'spectacle-{index:02d}',
                title=f'Spectacle {index:02d}',
                description='Une création originale',
                created_in=2026,
                location=cls.location,
                bookable=(index % 2 == 0),
            )

    def test_catalogue_is_sorted_by_title_and_paginated_by_ten(self):
        response = self.client.get(reverse('catalogue:show-index'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['shows']), 10)
        self.assertEqual(response.context['shows'].paginator.num_pages, 2)
        self.assertEqual(response.context['shows'][0].title, 'Spectacle 00')

    def test_search_and_filters_can_be_combined(self):
        response = self.client.get(reverse('catalogue:show-index'), {
            'q': 'Spectacle 0',
            'location': self.location.pk,
            'bookable': '1',
        })

        shows = list(response.context['shows'])
        self.assertEqual(len(shows), 5)
        self.assertTrue(all(show.bookable for show in shows))
        self.assertTrue(all(show.location == self.location for show in shows))

    def test_catalogue_can_be_sorted_by_minimum_price(self):
        expensive = Price.objects.create(type='Plein', price='30.00')
        cheap = Price.objects.create(type='Réduit', price='10.00')
        Show.objects.get(slug='spectacle-00').prices.add(expensive)
        Show.objects.get(slug='spectacle-01').prices.add(cheap)

        response = self.client.get(reverse('catalogue:show-index'), {
            'q': 'Spectacle 0',
            'sort': 'price',
        })

        priced_shows = [show for show in response.context['shows'] if show.min_price is not None]
        self.assertEqual([show.slug for show in priced_shows], [
            'spectacle-01',
            'spectacle-00',
        ])

    def test_pagination_link_keeps_active_criteria(self):
        response = self.client.get(reverse('catalogue:show-index'), {
            'q': 'Spectacle',
            'sort': 'title',
        })

        self.assertContains(response, 'q=Spectacle&amp;sort=title&amp;page=2')


class ReservationWorkflowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='client', password='secret')
        locality = Locality.objects.create(postal_code='4000', locality='Liège')
        location = Location.objects.create(
            slug='forum',
            designation='Forum',
            locality=locality,
        )
        cls.price = Price.objects.create(type='Plein', price='25.00')
        cls.show = Show.objects.create(
            slug='concert-test',
            title='Concert test',
            created_in=2026,
            location=location,
            bookable=True,
        )
        cls.show.prices.add(cls.price)
        cls.representation = Representation.objects.create(
            show=cls.show,
            schedule=timezone.now() + timedelta(days=7),
            location=location,
        )

    def reservation_url(self, representation=None):
        representation = representation or self.representation
        return reverse('catalogue:reservation-create', args=[representation.pk])

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(self.reservation_url())

        self.assertRedirects(
            response,
            f'{reverse("login")}?next={self.reservation_url()}',
        )

    def test_authenticated_user_can_open_reservation_form(self):
        self.client.force_login(self.user)

        response = self.client.get(self.reservation_url())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Confirmer la réservation')
        self.assertContains(response, '25.00')

    def test_valid_submission_creates_reservation_and_line(self):
        self.client.force_login(self.user)

        response = self.client.post(self.reservation_url(), {
            'price': self.price.pk,
            'quantity': 3,
        })

        self.assertRedirects(
            response,
            reverse('catalogue:representation-show', args=[self.representation.pk]),
        )
        reservation = Reservation.objects.get()
        line = RepresentationReservation.objects.get()
        self.assertEqual(reservation.user, self.user)
        self.assertEqual(reservation.status, 'en attente')
        self.assertEqual(line.reservation, reservation)
        self.assertEqual(line.representation, self.representation)
        self.assertEqual(line.price, Decimal('25.00'))
        self.assertEqual(line.quantity, 3)

    def test_past_representation_cannot_be_reserved(self):
        past_representation = Representation.objects.create(
            show=self.show,
            schedule=timezone.now() - timedelta(days=1),
            location=self.representation.location,
        )
        self.client.force_login(self.user)

        response = self.client.post(self.reservation_url(past_representation), {
            'price': self.price.pk,
            'quantity': 1,
        })

        self.assertRedirects(
            response,
            reverse('catalogue:representation-show', args=[past_representation.pk]),
        )
        self.assertFalse(Reservation.objects.exists())


class MyReservationsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user(username='owner', password='secret')
        cls.other_user = User.objects.create_user(username='other', password='secret')
        locality = Locality.objects.create(postal_code='5000', locality='Namur')
        location = Location.objects.create(
            slug='grand-manege',
            designation='Grand Manège',
            locality=locality,
        )
        show = Show.objects.create(
            slug='danse-test',
            title='Danse test',
            created_in=2026,
            location=location,
        )
        representation = Representation.objects.create(
            show=show,
            schedule=timezone.now() + timedelta(days=10),
            location=location,
        )
        cls.owner_reservation = Reservation.objects.create(
            user=cls.owner,
            status='en attente',
        )
        RepresentationReservation.objects.create(
            reservation=cls.owner_reservation,
            representation=representation,
            price=Decimal('18.00'),
            quantity=2,
        )
        cls.other_reservation = Reservation.objects.create(
            user=cls.other_user,
            status='payée',
        )

    def test_reservation_list_requires_authentication(self):
        url = reverse('catalogue:reservation-index')

        response = self.client.get(url)

        self.assertRedirects(response, f'{reverse("login")}?next={url}')

    def test_user_only_sees_own_reservations(self):
        self.client.force_login(self.owner)

        response = self.client.get(reverse('catalogue:reservation-index'))

        self.assertContains(response, f'Réservation n°{self.owner_reservation.pk}')
        self.assertNotContains(response, f'Réservation n°{self.other_reservation.pk}')
        self.assertContains(response, 'Danse test')

    def test_owner_can_view_reservation_details(self):
        self.client.force_login(self.owner)

        response = self.client.get(reverse(
            'catalogue:reservation-show',
            args=[self.owner_reservation.pk],
        ))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Danse test')
        self.assertContains(response, '18.00 €')

    def test_user_cannot_view_another_users_reservation(self):
        self.client.force_login(self.owner)

        response = self.client.get(reverse(
            'catalogue:reservation-show',
            args=[self.other_reservation.pk],
        ))

        self.assertEqual(response.status_code, 404)


class ShowReviewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='critic', password='secret')
        cls.other_user = User.objects.create_user(username='reader', password='secret')
        cls.show = Show.objects.create(
            slug='piece-test',
            title='Pièce test',
            created_in=2026,
        )
        cls.validated_review = Review.objects.create(
            user=cls.other_user,
            show=cls.show,
            review='Avis public',
            stars=4,
            validated=True,
        )

    def test_show_only_displays_validated_reviews_publicly(self):
        Review.objects.create(
            user=self.user,
            show=self.show,
            review='Avis secret en attente',
            stars=3,
            validated=False,
        )

        response = self.client.get(reverse('catalogue:show-show', args=[self.show.pk]))

        self.assertContains(response, 'Avis public')
        self.assertNotContains(response, 'Avis secret en attente')

    def test_authenticated_user_can_submit_review_for_moderation(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('catalogue:review-create', args=[self.show.pk]),
            {'stars': 5, 'review': 'Excellent spectacle'},
        )

        self.assertRedirects(
            response,
            reverse('catalogue:show-show', args=[self.show.pk]),
        )
        review = Review.objects.get(user=self.user, show=self.show)
        self.assertEqual(review.stars, 5)
        self.assertFalse(review.validated)

    def test_invalid_star_rating_is_rejected(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('catalogue:review-create', args=[self.show.pk]),
            {'stars': 6, 'review': 'Note invalide'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('stars', response.context['form'].errors)
        self.assertFalse(Review.objects.filter(user=self.user).exists())

    def test_editing_review_resets_moderation(self):
        review = Review.objects.create(
            user=self.user,
            show=self.show,
            review='Ancien texte',
            stars=2,
            validated=True,
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('catalogue:review-edit', args=[review.pk]),
            {'stars': 4, 'review': 'Nouveau texte'},
        )

        self.assertRedirects(
            response,
            reverse('catalogue:show-show', args=[self.show.pk]),
        )
        review.refresh_from_db()
        self.assertEqual(review.review, 'Nouveau texte')
        self.assertFalse(review.validated)
        self.assertIsNotNone(review.updated_at)

    def test_user_cannot_edit_or_delete_another_users_review(self):
        self.client.force_login(self.user)

        edit_response = self.client.get(reverse(
            'catalogue:review-edit',
            args=[self.validated_review.pk],
        ))
        delete_response = self.client.post(reverse(
            'catalogue:review-delete',
            args=[self.validated_review.pk],
        ))

        self.assertEqual(edit_response.status_code, 404)
        self.assertEqual(delete_response.status_code, 404)
        self.assertTrue(Review.objects.filter(pk=self.validated_review.pk).exists())


class UpcomingRepresentationsFeedTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        locality = Locality.objects.create(postal_code='7000', locality='Mons')
        location = Location.objects.create(
            slug='theatre-mons',
            designation='Théâtre de Mons',
            locality=locality,
        )
        earlier_show = Show.objects.create(
            slug='spectacle-proche',
            title='Spectacle proche',
            description='La prochaine représentation.',
            created_in=2026,
            location=location,
        )
        later_show = Show.objects.create(
            slug='spectacle-lointain',
            title='Spectacle lointain',
            created_in=2026,
            location=location,
        )
        past_show = Show.objects.create(
            slug='spectacle-passe',
            title='Spectacle passé',
            created_in=2025,
            location=location,
        )
        cls.earlier = Representation.objects.create(
            show=earlier_show,
            schedule=timezone.now() + timedelta(days=2),
            location=location,
        )
        cls.later = Representation.objects.create(
            show=later_show,
            schedule=timezone.now() + timedelta(days=8),
            location=location,
        )
        Representation.objects.create(
            show=past_show,
            schedule=timezone.now() - timedelta(days=2),
            location=location,
        )

    def test_feed_is_valid_rss_and_only_contains_future_items(self):
        response = self.client.get(reverse('catalogue:representations-rss'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/rss+xml; charset=utf-8')
        self.assertContains(response, '<rss version="2.0"')
        self.assertContains(response, 'Spectacle proche')
        self.assertContains(response, 'Spectacle lointain')
        self.assertNotContains(response, 'Spectacle passé')

    def test_feed_orders_representations_chronologically(self):
        response = self.client.get(reverse('catalogue:representations-rss'))
        content = response.content.decode()

        self.assertLess(
            content.index('Spectacle proche'),
            content.index('Spectacle lointain'),
        )

    def test_feed_items_link_to_representation_details(self):
        response = self.client.get(reverse('catalogue:representations-rss'))

        expected_path = reverse(
            'catalogue:representation-show',
            args=[self.earlier.pk],
        )
        self.assertContains(response, f'http://testserver{expected_path}')
