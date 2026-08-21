from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from catalogue.models import Artist


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
