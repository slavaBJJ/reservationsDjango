from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from catalogue.models import Artist, Locality, Location, Show
from catalogue.roles import (
    ROLE_AFFILIATE_FREE,
    ROLE_AFFILIATE_PREMIUM,
    ROLE_AFFILIATE_STARTER,
)


class ArtistAPITests(APITestCase):
    def setUp(self):
        self.password = 'temporary-test-password'
        self.user = get_user_model().objects.create_user(
            username='api-test-user',
            password=self.password,
        )
        artist_permissions = Permission.objects.filter(
            content_type__app_label='catalogue',
            content_type__model='artist',
        )
        self.user.user_permissions.set(artist_permissions)
        self.client.force_authenticate(user=self.user)

    def test_unauthenticated_request_is_rejected(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(reverse('catalogue:artist-list'))

        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    def test_artist_crud_responses_include_hateoas_links(self):
        list_url = reverse('catalogue:artist-list')

        create_response = self.client.post(
            list_url,
            {'firstname': 'John', 'lastname': 'Doe'},
            format='json',
        )
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        artist_id = create_response.data['id']
        detail_url = reverse('catalogue:artist-detail', args=[artist_id])

        self.assertEqual(
            create_response.data['links']['self'],
            f'http://testserver{detail_url}',
        )
        self.assertEqual(
            create_response.data['links']['all_artists'],
            f'http://testserver{list_url}',
        )

        detail_response = self.client.get(detail_url)
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)

        update_response = self.client.put(
            detail_url,
            {'firstname': 'Jane', 'lastname': 'Doe'},
            format='json',
        )
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.assertEqual(update_response.data['firstname'], 'Jane')
        self.assertIn('links', update_response.data)

        delete_response = self.client.delete(detail_url)
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Artist.objects.filter(pk=artist_id).exists())

    def test_artist_list_contains_hateoas_links(self):
        artist = Artist.objects.create(firstname='Jane', lastname='Smith')

        response = self.client.get(reverse('catalogue:artist-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(
            response.data[0]['links']['self'],
            'http://testserver'
            + reverse('catalogue:artist-detail', args=[artist.pk]),
        )

    def test_jwt_authentication_and_refresh(self):
        self.client.force_authenticate(user=None)
        token_response = self.client.post(
            reverse('catalogue:token-obtain-pair'),
            {'username': self.user.username, 'password': self.password},
            format='json',
        )
        self.assertEqual(token_response.status_code, status.HTTP_200_OK)
        self.assertIn('access', token_response.data)
        self.assertIn('refresh', token_response.data)

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token_response.data['access']}"
        )
        api_response = self.client.get(reverse('catalogue:artist-list'))
        self.assertEqual(api_response.status_code, status.HTTP_200_OK)

        refresh_response = self.client.post(
            reverse('catalogue:token-refresh'),
            {'refresh': token_response.data['refresh']},
            format='json',
        )
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn('access', refresh_response.data)


class ShowAffiliateAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.free_group = Group.objects.create(name=ROLE_AFFILIATE_FREE)
        cls.starter_group = Group.objects.create(name=ROLE_AFFILIATE_STARTER)
        cls.premium_group = Group.objects.create(name=ROLE_AFFILIATE_PREMIUM)

        cls.free_user = get_user_model().objects.create_user(username='affiliate-free')
        cls.starter_user = get_user_model().objects.create_user(username='affiliate-starter')
        cls.premium_user = get_user_model().objects.create_user(username='affiliate-premium')
        cls.member = get_user_model().objects.create_user(username='api-member')
        cls.staff = get_user_model().objects.create_user(
            username='api-staff',
            is_staff=True,
        )
        cls.free_user.groups.add(cls.free_group)
        cls.starter_user.groups.add(cls.starter_group)
        cls.premium_user.groups.add(cls.premium_group)

        locality = Locality.objects.create(postal_code='1050', locality='Ixelles')
        cls.location = Location.objects.create(
            slug='api-theatre',
            designation='Théâtre API',
            locality=locality,
        )
        cls.other_location = Location.objects.create(
            slug='api-other-location',
            designation='Autre salle API',
            locality=locality,
        )

        for index in range(30):
            Show.objects.create(
                slug=f'api-show-{index:02d}',
                title=f'Spectacle API {index:02d}',
                description='Description recherchable',
                duration=60 + index,
                created_in=2020 + index % 5,
                location=cls.location if index else cls.other_location,
                bookable=(index % 2 == 0),
            )

    def test_non_affiliate_cannot_read_show_api(self):
        self.client.force_authenticate(user=self.member)

        response = self.client.get(reverse('catalogue:show-api-list'))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_free_affiliate_is_limited_to_ten_results(self):
        self.client.force_authenticate(user=self.free_user)

        response = self.client.get(reverse('catalogue:show-api-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 30)
        self.assertEqual(len(response.data['results']), 10)
        self.assertIsNotNone(response.data['next'])

    def test_starter_affiliate_is_capped_at_twenty_five_results(self):
        self.client.force_authenticate(user=self.starter_user)

        response = self.client.get(
            reverse('catalogue:show-api-list'),
            {'page_size': 100},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 25)

    def test_premium_affiliate_can_receive_up_to_one_hundred_results(self):
        self.client.force_authenticate(user=self.premium_user)

        response = self.client.get(reverse('catalogue:show-api-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 30)

    def test_show_api_supports_search_filters_and_ordering(self):
        self.client.force_authenticate(user=self.premium_user)

        response = self.client.get(reverse('catalogue:show-api-list'), {
            'q': 'Spectacle API',
            'location': self.location.slug,
            'bookable': 'true',
            'ordering': '-duration',
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        self.assertTrue(results)
        self.assertTrue(all(result['bookable'] for result in results))
        self.assertTrue(all(result['location'] == self.location.pk for result in results))
        durations = [result['duration'] for result in results]
        self.assertEqual(durations, sorted(durations, reverse=True))

    def test_show_response_contains_hateoas_links(self):
        self.client.force_authenticate(user=self.free_user)
        show = Show.objects.get(slug='api-show-00')

        response = self.client.get(reverse('catalogue:show-api-detail', args=[show.pk]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data['links']['self'],
            'http://testserver'
            + reverse('catalogue:show-api-detail', args=[show.pk]),
        )

    def test_affiliate_cannot_write_but_staff_can(self):
        url = reverse('catalogue:show-api-list')
        payload = {
            'slug': 'created-through-api',
            'title': 'Créé via API',
            'created_in': 2026,
            'bookable': True,
        }
        self.client.force_authenticate(user=self.premium_user)

        forbidden_response = self.client.post(url, payload, format='json')

        self.assertEqual(forbidden_response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.staff)
        created_response = self.client.post(url, payload, format='json')

        self.assertEqual(created_response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Show.objects.filter(slug='created-through-api').exists())
