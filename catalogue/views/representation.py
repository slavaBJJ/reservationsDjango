from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from catalogue.forms import RepresentationForm
from catalogue.models import Representation, Show
from catalogue.roles import is_producer_for


def _can_manage(user, show):
    return (
        user.is_authenticated
        and (
            user.has_perm('catalogue.change_representation')
            or is_producer_for(user, show)
        )
    )


def index(request):
    representations = Representation.objects.select_related(
        'show',
        'location',
        'show__location',
    ).prefetch_related('show__prices').filter(
        schedule__gt=timezone.now(),
    ).order_by('schedule', 'pk')
    for representation in representations:
        representation.is_reservable = (
            representation.show.bookable
            and bool(representation.show.prices.all())
        )
    title = 'Liste des représentations'

    return render(request, 'representation/index.html', {
        'representations': representations,
        'title': title,
    })


def show(request, representation_id):
    representation = get_object_or_404(
        Representation.objects.select_related('show', 'location', 'show__location'),
        pk=representation_id,
    )

    title = "Fiche d'une représentation"
    rep_date = representation.schedule.strftime('%Y-%m-%d')
    rep_time = representation.schedule.strftime('%H:%M')
    can_reserve = (
        representation.show.bookable
        and representation.schedule > timezone.now()
        and representation.show.prices.exists()
    )

    return render(request, 'representation/show.html', {
        'representation': representation,
        'title': title,
        'rep_date': rep_date,
        'rep_time': rep_time,
        'can_reserve': can_reserve,
        'can_manage_representation': _can_manage(request.user, representation.show),
    })


@login_required
def create(request, show_id):
    managed_show = get_object_or_404(Show, pk=show_id)
    if not (
        request.user.has_perm('catalogue.add_representation')
        or is_producer_for(request.user, managed_show)
    ):
        raise PermissionDenied
    form = RepresentationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        representation = form.save(commit=False)
        representation.show = managed_show
        representation.save()
        messages.success(request, 'Représentation créée avec succès.')
        return redirect('catalogue:representation-show', representation_id=representation.pk)
    return render(request, 'representation/form.html', {
        'form': form, 'managed_show': managed_show,
        'title': 'Ajouter une représentation',
    })


@login_required
def edit(request, representation_id):
    representation = get_object_or_404(
        Representation.objects.select_related('show'), pk=representation_id,
    )
    if not _can_manage(request.user, representation.show):
        raise PermissionDenied
    form = RepresentationForm(request.POST or None, instance=representation)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Représentation modifiée avec succès.')
        return redirect('catalogue:representation-show', representation_id=representation.pk)
    return render(request, 'representation/form.html', {
        'form': form, 'managed_show': representation.show,
        'representation': representation, 'title': 'Modifier la représentation',
    })


@login_required
@require_POST
def delete(request, representation_id):
    representation = get_object_or_404(
        Representation.objects.select_related('show'), pk=representation_id,
    )
    if not (
        request.user.has_perm('catalogue.delete_representation')
        or is_producer_for(request.user, representation.show)
    ):
        raise PermissionDenied
    show_id = representation.show_id
    if representation.representation_reservations.exists():
        messages.error(
            request,
            'Cette représentation ne peut pas être supprimée car elle contient des réservations.',
        )
        return redirect('catalogue:representation-show', representation_id=representation.pk)
    representation.delete()
    messages.success(request, 'Représentation supprimée avec succès.')
    return redirect('catalogue:show-show', show_id=show_id)
