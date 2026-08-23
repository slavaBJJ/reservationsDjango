from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from catalogue.forms import PressReviewForm
from catalogue.models import PressReview
from catalogue.roles import ROLE_CRITIC, ROLE_PRODUCER, has_role, is_producer_for


def _require_critic(user):
    if not has_role(user, ROLE_CRITIC):
        raise PermissionDenied


@login_required
def index(request):
    _require_critic(request.user)
    return render(request, 'press_review/index.html', {
        'press_reviews': request.user.press_reviews.select_related('show'),
        'title': 'Mes critiques de presse',
    })


@login_required
def create(request):
    _require_critic(request.user)
    form = PressReviewForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        press_review = form.save(commit=False)
        press_review.user = request.user
        press_review.save()
        messages.success(request, 'Votre critique a été envoyée pour modération.')
        return redirect('catalogue:press-review-index')

    return render(request, 'press_review/form.html', {
        'form': form,
        'title': 'Soumettre une critique de presse',
    })


@login_required
def edit(request, press_review_id):
    _require_critic(request.user)
    press_review = get_object_or_404(
        PressReview,
        pk=press_review_id,
        user=request.user,
    )
    form = PressReviewForm(request.POST or None, instance=press_review)

    if request.method == 'POST' and form.is_valid():
        press_review = form.save(commit=False)
        press_review.moderation_status = PressReview.ModerationStatus.PENDING
        press_review.moderated_by = None
        press_review.moderated_at = None
        press_review.updated_at = timezone.now()
        press_review.save()
        messages.success(request, 'Votre critique modifiée a été renvoyée pour modération.')
        return redirect('catalogue:press-review-index')

    return render(request, 'press_review/form.html', {
        'form': form,
        'title': 'Modifier ma critique de presse',
    })


@login_required
def delete(request, press_review_id):
    _require_critic(request.user)
    press_review = get_object_or_404(
        PressReview,
        pk=press_review_id,
        user=request.user,
    )

    if request.method == 'POST':
        press_review.delete()
        messages.success(request, 'Votre critique a été supprimée.')
        return redirect('catalogue:press-review-index')

    return render(request, 'press_review/delete.html', {
        'press_review': press_review,
        'title': 'Supprimer ma critique de presse',
    })


@login_required
def moderation(request):
    if not request.user.is_staff and not has_role(request.user, ROLE_PRODUCER):
        raise PermissionDenied

    press_reviews = PressReview.objects.select_related('user', 'show').filter(
        moderation_status=PressReview.ModerationStatus.PENDING,
    )
    if not request.user.is_staff:
        press_reviews = press_reviews.filter(show__producers=request.user)

    return render(request, 'press_review/moderation.html', {
        'press_reviews': press_reviews.distinct(),
        'title': 'Modération des critiques de presse',
    })


@login_required
@require_POST
def moderate(request, press_review_id):
    press_review = get_object_or_404(
        PressReview.objects.select_related('show'),
        pk=press_review_id,
    )
    if not request.user.is_staff and not is_producer_for(
        request.user,
        press_review.show,
    ):
        return JsonResponse({'error': 'Accès interdit.'}, status=403)

    statuses = {
        'approve': PressReview.ModerationStatus.APPROVED,
        'reject': PressReview.ModerationStatus.REJECTED,
    }
    action = request.POST.get('action')
    if action not in statuses:
        return JsonResponse({'error': 'Action de modération invalide.'}, status=400)

    press_review.moderation_status = statuses[action]
    press_review.moderated_by = request.user
    press_review.moderated_at = timezone.now()
    press_review.save(update_fields=[
        'moderation_status',
        'moderated_by',
        'moderated_at',
    ])

    return JsonResponse({
        'press_review_id': press_review.pk,
        'status': press_review.moderation_status,
        'status_label': press_review.get_moderation_status_display(),
    })
