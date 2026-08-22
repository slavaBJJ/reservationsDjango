from django.test import TestCase
from django.urls import reverse

from catalogue.models import Locality, Location, Price, Show


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
