from django.utils import timezone

from catalogue.models import RepresentationReservation


def can_review_show(user, show):
    if not user.is_authenticated:
        return False

    return RepresentationReservation.objects.filter(
        reservation__user=user,
        representation__show=show,
        representation__schedule__lt=timezone.now(),
    ).exclude(
        reservation__status__iexact='annulée',
    ).exists()
