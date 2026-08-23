from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from catalogue.forms import ReviewForm
from catalogue.models import Review, Show
from catalogue.review_rules import can_review_show
from catalogue.roles import ROLE_PRODUCER, has_role, is_producer_for


def _can_access_moderation(user):
    return user.is_staff or has_role(user, ROLE_PRODUCER)


@login_required
def moderation(request):
    if not _can_access_moderation(request.user):
        raise PermissionDenied

    reviews = Review.objects.select_related(
        'user',
        'show',
        'moderated_by',
    ).filter(moderation_status=Review.ModerationStatus.PENDING)

    if not request.user.is_staff:
        reviews = reviews.filter(show__producers=request.user)

    return render(request, 'review/moderation.html', {
        'reviews': reviews.order_by('created_at', 'pk').distinct(),
        'title': 'Modération des avis',
    })


@login_required
@require_POST
def moderate(request, review_id):
    review = get_object_or_404(Review.objects.select_related('show'), pk=review_id)

    if not request.user.is_staff and not is_producer_for(request.user, review.show):
        return JsonResponse({'error': 'Accès interdit.'}, status=403)

    statuses = {
        'approve': Review.ModerationStatus.APPROVED,
        'reject': Review.ModerationStatus.REJECTED,
    }
    action = request.POST.get('action')
    if action not in statuses:
        return JsonResponse({'error': 'Action de modération invalide.'}, status=400)

    review.moderation_status = statuses[action]
    review.moderated_by = request.user
    review.moderated_at = timezone.now()
    review.save(update_fields=[
        'moderation_status',
        'moderated_by',
        'moderated_at',
    ])

    return JsonResponse({
        'review_id': review.pk,
        'status': review.moderation_status,
        'status_label': review.get_moderation_status_display(),
    })


@login_required
def create(request, show_id):
    show = get_object_or_404(Show, pk=show_id)

    if not can_review_show(request.user, show):
        messages.error(
            request,
            "Vous devez avoir réservé une représentation passée de ce spectacle "
            "pour donner votre avis.",
        )
        return redirect('catalogue:show-show', show_id=show.pk)

    if Review.objects.filter(user=request.user, show=show).exists():
        messages.error(request, 'Vous avez déjà donné votre avis sur ce spectacle.')
        return redirect('catalogue:show-show', show_id=show.pk)

    form = ReviewForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        review = form.save(commit=False)
        review.user = request.user
        review.show = show
        review.moderation_status = Review.ModerationStatus.PENDING
        review.save()
        messages.success(request, 'Votre avis a été envoyé pour modération.')
        return redirect('catalogue:show-show', show_id=show.pk)

    return render(request, 'review/form.html', {
        'form': form,
        'show': show,
        'title': 'Donner mon avis',
    })


@login_required
def edit(request, review_id):
    review = get_object_or_404(Review, pk=review_id, user=request.user)
    form = ReviewForm(request.POST or None, instance=review)

    if request.method == 'POST' and form.is_valid():
        review = form.save(commit=False)
        review.moderation_status = Review.ModerationStatus.PENDING
        review.moderated_by = None
        review.moderated_at = None
        review.updated_at = timezone.now()
        review.save()
        messages.success(request, 'Votre avis modifié a été renvoyé pour modération.')
        return redirect('catalogue:show-show', show_id=review.show_id)

    return render(request, 'review/form.html', {
        'form': form,
        'show': review.show,
        'title': 'Modifier mon avis',
    })


@login_required
def delete(request, review_id):
    review = get_object_or_404(Review, pk=review_id, user=request.user)

    if request.method == 'POST':
        show_id = review.show_id
        review.delete()
        messages.success(request, 'Votre avis a été supprimé.')
        return redirect('catalogue:show-show', show_id=show_id)

    return render(request, 'review/delete.html', {
        'review': review,
        'title': 'Supprimer mon avis',
    })
