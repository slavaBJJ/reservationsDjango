import csv
from datetime import timedelta
from decimal import Decimal
from io import StringIO

from django.contrib.auth.models import Group, User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from catalogue.models import (
    Locality,
    Location,
    PressReview,
    Price,
    Representation,
    RepresentationReservation,
    Reservation,
    Review,
    Show,
)
from catalogue.roles import (
    ROLE_CRITIC,
    ROLE_MEMBER,
    ROLE_PRODUCER,
    has_role,
    is_producer_for,
)
from accounts.forms import UserSignUpForm


class BusinessRoleTests(TestCase):
    def test_signup_creates_member_group_when_missing(self):
        self.assertFalse(Group.objects.filter(name=ROLE_MEMBER).exists())
        form = UserSignUpForm(data={
            'username': 'new-member',
            'email': 'member@example.com',
            'password1': 'A-secure-password-2026',
            'password2': 'A-secure-password-2026',
            'first_name': 'Nouveau',
            'last_name': 'Membre',
            'langue': 'fr',
        })

        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()

        self.assertTrue(user.groups.filter(name=ROLE_MEMBER).exists())
        self.assertTrue(has_role(user, ROLE_MEMBER))

    def test_producer_must_have_role_and_be_assigned_to_show(self):
        producer = User.objects.create_user(username='producer')
        producer_group = Group.objects.create(name=ROLE_PRODUCER)
        producer.groups.add(producer_group)
        show = Show.objects.create(
            slug='production-test',
            title='Production test',
            created_in=2026,
        )

        self.assertFalse(is_producer_for(producer, show))

        show.producers.add(producer)

        self.assertTrue(is_producer_for(producer, show))
        self.assertIn(show, producer.produced_shows.all())

    def test_show_assignment_without_producer_role_is_not_enough(self):
        member = User.objects.create_user(username='simple-member')
        show = Show.objects.create(
            slug='role-required',
            title='Rôle requis',
            created_in=2026,
        )
        show.producers.add(member)

        self.assertFalse(is_producer_for(member, show))


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
            moderation_status=Review.ModerationStatus.APPROVED,
        )
        past_representation = Representation.objects.create(
            show=cls.show,
            schedule=timezone.now() - timedelta(days=2),
        )
        eligible_reservation = Reservation.objects.create(
            user=cls.user,
            status='payée',
        )
        RepresentationReservation.objects.create(
            reservation=eligible_reservation,
            representation=past_representation,
            price=Decimal('20.00'),
            quantity=1,
        )

    def test_show_only_displays_validated_reviews_publicly(self):
        Review.objects.create(
            user=self.user,
            show=self.show,
            review='Avis secret en attente',
            stars=3,
            moderation_status=Review.ModerationStatus.PENDING,
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
        self.assertEqual(review.moderation_status, Review.ModerationStatus.PENDING)

    def test_user_without_past_reservation_cannot_submit_review(self):
        ineligible_user = User.objects.create_user(username='ineligible')
        self.client.force_login(ineligible_user)

        response = self.client.post(
            reverse('catalogue:review-create', args=[self.show.pk]),
            {'stars': 5, 'review': 'Avis non autorisé'},
            follow=True,
        )

        self.assertContains(response, 'Vous devez avoir réservé une représentation passée')
        self.assertFalse(Review.objects.filter(user=ineligible_user).exists())

    def test_cancelled_reservation_does_not_allow_review(self):
        cancelled_user = User.objects.create_user(username='cancelled')
        past_representation = self.show.representations.first()
        reservation = Reservation.objects.create(
            user=cancelled_user,
            status='annulée',
        )
        RepresentationReservation.objects.create(
            reservation=reservation,
            representation=past_representation,
            price=Decimal('20.00'),
            quantity=1,
        )
        self.client.force_login(cancelled_user)

        response = self.client.get(
            reverse('catalogue:review-create', args=[self.show.pk]),
            follow=True,
        )

        self.assertContains(response, 'Vous devez avoir réservé une représentation passée')
        self.assertFalse(Review.objects.filter(user=cancelled_user).exists())

    def test_future_reservation_does_not_allow_review(self):
        future_user = User.objects.create_user(username='future-attendee')
        future_representation = Representation.objects.create(
            show=self.show,
            schedule=timezone.now() + timedelta(days=2),
        )
        reservation = Reservation.objects.create(
            user=future_user,
            status='payée',
        )
        RepresentationReservation.objects.create(
            reservation=reservation,
            representation=future_representation,
            price=Decimal('20.00'),
            quantity=1,
        )
        self.client.force_login(future_user)

        response = self.client.get(
            reverse('catalogue:review-create', args=[self.show.pk]),
            follow=True,
        )

        self.assertContains(response, 'Vous devez avoir réservé une représentation passée')
        self.assertFalse(Review.objects.filter(user=future_user).exists())

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
            moderation_status=Review.ModerationStatus.APPROVED,
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
        self.assertEqual(review.moderation_status, Review.ModerationStatus.PENDING)
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


class ProducerReviewModerationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        producer_group = Group.objects.create(name=ROLE_PRODUCER)
        cls.producer = User.objects.create_user(username='producer-one')
        cls.other_producer = User.objects.create_user(username='producer-two')
        cls.member = User.objects.create_user(username='ordinary-member')
        cls.staff = User.objects.create_user(username='staff-user', is_staff=True)
        cls.producer.groups.add(producer_group)
        cls.other_producer.groups.add(producer_group)

        cls.own_show = Show.objects.create(
            slug='producer-show',
            title='Spectacle du producteur',
            created_in=2026,
        )
        cls.other_show = Show.objects.create(
            slug='other-producer-show',
            title='Spectacle d’un autre producteur',
            created_in=2026,
        )
        cls.own_show.producers.add(cls.producer)
        cls.other_show.producers.add(cls.other_producer)

        reviewer = User.objects.create_user(username='review-author')
        cls.own_review = Review.objects.create(
            user=reviewer,
            show=cls.own_show,
            review='À modérer par le premier producteur',
            stars=5,
        )
        cls.other_review = Review.objects.create(
            user=reviewer,
            show=cls.other_show,
            review='À modérer par le second producteur',
            stars=3,
        )

    def test_producer_only_sees_reviews_for_own_shows(self):
        self.client.force_login(self.producer)

        response = self.client.get(reverse('catalogue:review-moderation'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.own_review.review)
        self.assertNotContains(response, self.other_review.review)

    def test_member_cannot_access_moderation_page(self):
        self.client.force_login(self.member)

        response = self.client.get(reverse('catalogue:review-moderation'))

        self.assertEqual(response.status_code, 403)

    def test_producer_can_approve_review_with_json_response(self):
        self.client.force_login(self.producer)

        response = self.client.post(
            reverse('catalogue:review-moderate', args=[self.own_review.pk]),
            {'action': 'approve'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertEqual(response.json()['status'], Review.ModerationStatus.APPROVED)
        self.own_review.refresh_from_db()
        self.assertEqual(
            self.own_review.moderation_status,
            Review.ModerationStatus.APPROVED,
        )
        self.assertEqual(self.own_review.moderated_by, self.producer)
        self.assertIsNotNone(self.own_review.moderated_at)

    def test_producer_cannot_moderate_another_producers_review(self):
        self.client.force_login(self.producer)

        response = self.client.post(
            reverse('catalogue:review-moderate', args=[self.other_review.pk]),
            {'action': 'reject'},
        )

        self.assertEqual(response.status_code, 403)
        self.other_review.refresh_from_db()
        self.assertEqual(
            self.other_review.moderation_status,
            Review.ModerationStatus.PENDING,
        )

    def test_staff_can_reject_any_review(self):
        self.client.force_login(self.staff)

        response = self.client.post(
            reverse('catalogue:review-moderate', args=[self.other_review.pk]),
            {'action': 'reject'},
        )

        self.assertEqual(response.status_code, 200)
        self.other_review.refresh_from_db()
        self.assertEqual(
            self.other_review.moderation_status,
            Review.ModerationStatus.REJECTED,
        )
        self.assertEqual(self.other_review.moderated_by, self.staff)


class PressReviewWorkflowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        critic_group = Group.objects.create(name=ROLE_CRITIC)
        producer_group = Group.objects.create(name=ROLE_PRODUCER)
        cls.critic = User.objects.create_user(username='press-critic')
        cls.other_critic = User.objects.create_user(username='other-critic')
        cls.producer = User.objects.create_user(username='press-producer')
        cls.other_producer = User.objects.create_user(username='outside-producer')
        cls.member = User.objects.create_user(username='press-reader')
        cls.critic.groups.add(critic_group)
        cls.other_critic.groups.add(critic_group)
        cls.producer.groups.add(producer_group)
        cls.other_producer.groups.add(producer_group)

        cls.show = Show.objects.create(
            slug='press-show',
            title='Spectacle pour la presse',
            created_in=2026,
        )
        cls.show.producers.add(cls.producer)

    def test_only_critic_can_open_submission_form(self):
        self.client.force_login(self.member)

        response = self.client.get(reverse('catalogue:press-review-create'))

        self.assertEqual(response.status_code, 403)

    def test_critic_can_submit_article_for_moderation(self):
        self.client.force_login(self.critic)

        response = self.client.post(
            reverse('catalogue:press-review-create'),
            {
                'show': self.show.pk,
                'title': 'Une soirée remarquable',
                'content': 'Le spectacle propose une mise en scène remarquable.',
                'url': '',
            },
        )

        self.assertRedirects(response, reverse('catalogue:press-review-index'))
        press_review = PressReview.objects.get(user=self.critic)
        self.assertEqual(
            press_review.moderation_status,
            PressReview.ModerationStatus.PENDING,
        )

    def test_article_or_external_link_is_required(self):
        self.client.force_login(self.critic)

        response = self.client.post(
            reverse('catalogue:press-review-create'),
            {
                'show': self.show.pk,
                'title': 'Critique vide',
                'content': '',
                'url': '',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ajoutez le texte de l’article ou un lien externe')
        self.assertFalse(PressReview.objects.exists())

    def test_critic_cannot_edit_another_critics_submission(self):
        press_review = PressReview.objects.create(
            user=self.other_critic,
            show=self.show,
            title='Critique privée',
            content='Contenu',
        )
        self.client.force_login(self.critic)

        response = self.client.get(reverse(
            'catalogue:press-review-edit',
            args=[press_review.pk],
        ))

        self.assertEqual(response.status_code, 404)

    def test_only_approved_press_reviews_are_public(self):
        PressReview.objects.create(
            user=self.critic,
            show=self.show,
            title='Critique publiée',
            content='Visible publiquement',
            moderation_status=PressReview.ModerationStatus.APPROVED,
        )
        PressReview.objects.create(
            user=self.other_critic,
            show=self.show,
            title='Critique en attente',
            content='Invisible publiquement',
        )

        response = self.client.get(reverse('catalogue:show-show', args=[self.show.pk]))

        self.assertContains(response, 'Visible publiquement')
        self.assertNotContains(response, 'Invisible publiquement')

    def test_assigned_producer_can_approve_with_json_response(self):
        press_review = PressReview.objects.create(
            user=self.critic,
            show=self.show,
            title='À publier',
            url='https://example.com/article',
        )
        self.client.force_login(self.producer)

        response = self.client.post(
            reverse('catalogue:press-review-moderate', args=[press_review.pk]),
            {'action': 'approve'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        press_review.refresh_from_db()
        self.assertEqual(
            press_review.moderation_status,
            PressReview.ModerationStatus.APPROVED,
        )
        self.assertEqual(press_review.moderated_by, self.producer)
        self.assertIsNotNone(press_review.moderated_at)

    def test_unassigned_producer_cannot_moderate(self):
        press_review = PressReview.objects.create(
            user=self.critic,
            show=self.show,
            title='Hors périmètre',
            content='Contenu',
        )
        self.client.force_login(self.other_producer)

        response = self.client.post(
            reverse('catalogue:press-review-moderate', args=[press_review.pk]),
            {'action': 'reject'},
        )

        self.assertEqual(response.status_code, 403)
        press_review.refresh_from_db()
        self.assertEqual(
            press_review.moderation_status,
            PressReview.ModerationStatus.PENDING,
        )


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


class ShowCsvExportTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff = User.objects.create_user(
            username='catalogue-admin',
            password='secret',
            is_staff=True,
        )
        cls.customer = User.objects.create_user(
            username='customer',
            password='secret',
        )
        locality = Locality.objects.create(postal_code='6000', locality='Charleroi')
        cls.location = Location.objects.create(
            slug='palais-beaux-arts',
            designation='Palais des Beaux-Arts',
            locality=locality,
        )
        Show.objects.create(
            slug='opera-accentue',
            title='Opéra accentué',
            description='Un spectacle à découvrir',
            duration=95,
            created_in=2026,
            location=cls.location,
            bookable=True,
        )

    def test_export_requires_staff_access(self):
        url = reverse('catalogue:shows-csv-export')
        self.client.force_login(self.customer)

        response = self.client.get(url)

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('admin:login'), response.url)

    def test_staff_can_download_utf8_csv(self):
        self.client.force_login(self.staff)

        response = self.client.get(reverse('catalogue:shows-csv-export'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv; charset=utf-8')
        self.assertEqual(
            response['Content-Disposition'],
            'attachment; filename="spectacles.csv"',
        )
        self.assertTrue(response.content.startswith(b'\xef\xbb\xbf'))

    def test_export_contains_header_and_show_data(self):
        self.client.force_login(self.staff)

        response = self.client.get(reverse('catalogue:shows-csv-export'))
        content = response.content.decode('utf-8-sig')
        rows = list(csv.DictReader(StringIO(content)))

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0], {
            'slug': 'opera-accentue',
            'title': 'Opéra accentué',
            'description': 'Un spectacle à découvrir',
            'duration': '95',
            'created_in': '2026',
            'location_slug': self.location.slug,
            'bookable': '1',
        })

    def csv_upload(self, rows):
        header = 'slug,title,description,duration,created_in,location_slug,bookable\n'
        content = header + '\n'.join(rows) + '\n'
        return SimpleUploadedFile(
            'spectacles.csv',
            content.encode('utf-8'),
            content_type='text/csv',
        )

    def test_import_requires_staff_access(self):
        self.client.force_login(self.customer)

        response = self.client.get(reverse('catalogue:shows-csv-import'))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('admin:login'), response.url)

    def test_import_creates_new_show(self):
        self.client.force_login(self.staff)
        upload = self.csv_upload([
            'nouveau-show,Nouveau spectacle,Description,80,2027,palais-beaux-arts,oui',
        ])

        response = self.client.post(
            reverse('catalogue:shows-csv-import'),
            {'csv_file': upload},
            follow=True,
        )

        self.assertContains(response, '1 spectacle(s) créé(s), 0 spectacle(s) mis à jour')
        show = Show.objects.get(slug='nouveau-show')
        self.assertEqual(show.title, 'Nouveau spectacle')
        self.assertEqual(show.duration, 80)
        self.assertEqual(show.created_in, 2027)
        self.assertEqual(show.location, self.location)
        self.assertTrue(show.bookable)

    def test_import_updates_existing_show_by_slug(self):
        self.client.force_login(self.staff)
        upload = self.csv_upload([
            'opera-accentue,Opéra mis à jour,Nouveau texte,110,2028,,0',
        ])

        response = self.client.post(
            reverse('catalogue:shows-csv-import'),
            {'csv_file': upload},
            follow=True,
        )

        self.assertContains(response, '0 spectacle(s) créé(s), 1 spectacle(s) mis à jour')
        show = Show.objects.get(slug='opera-accentue')
        self.assertEqual(show.title, 'Opéra mis à jour')
        self.assertEqual(show.duration, 110)
        self.assertEqual(show.created_in, 2028)
        self.assertIsNone(show.location)
        self.assertFalse(show.bookable)

    def test_invalid_row_prevents_entire_import(self):
        self.client.force_login(self.staff)
        upload = self.csv_upload([
            'ligne-valide,Ligne valide,,75,2027,palais-beaux-arts,1',
            'ligne-invalide,Ligne invalide,,90,2027,lieu-inexistant,1',
        ])

        response = self.client.post(
            reverse('catalogue:shows-csv-import'),
            {'csv_file': upload},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'le lieu lieu-inexistant n’existe pas')
        self.assertFalse(Show.objects.filter(slug='ligne-valide').exists())
        self.assertFalse(Show.objects.filter(slug='ligne-invalide').exists())
