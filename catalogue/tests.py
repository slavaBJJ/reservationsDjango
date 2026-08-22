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
