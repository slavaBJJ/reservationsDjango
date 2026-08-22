from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from catalogue.forms import ReviewForm
from catalogue.models import Review, Show


@login_required
def create(request, show_id):
    show = get_object_or_404(Show, pk=show_id)

    if Review.objects.filter(user=request.user, show=show).exists():
        messages.error(request, 'Vous avez déjà donné votre avis sur ce spectacle.')
        return redirect('catalogue:show-show', show_id=show.pk)

    form = ReviewForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        review = form.save(commit=False)
        review.user = request.user
        review.show = show
        review.validated = False
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
        review.validated = False
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
