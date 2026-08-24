from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.db.models.deletion import RestrictedError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from catalogue.forms import LocationForm
from catalogue.models import Location


def index(request):
    locations = Location.objects.select_related('locality').order_by(
        'designation',
        'pk',
    )
    return render(request, 'location/index.html', {'locations': locations})


def show(request, location_id):
    location = get_object_or_404(
        Location.objects.select_related('locality').prefetch_related('shows'),
        id=location_id,
    )
    return render(request, 'location/show.html', {'location': location})


@permission_required('catalogue.add_location', raise_exception=True)
def create(request):
    form = LocationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        location = form.save()
        messages.success(request, 'Lieu créé avec succès.')
        return redirect('catalogue:location-show', location_id=location.pk)
    return render(request, 'location/create.html', {'form': form})


@permission_required('catalogue.change_location', raise_exception=True)
def edit(request, location_id):
    location = get_object_or_404(Location, id=location_id)
    form = LocationForm(request.POST or None, instance=location)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Lieu modifié avec succès.')
        return redirect('catalogue:location-show', location_id=location.pk)
    return render(
        request,
        'location/edit.html',
        {'form': form, 'location': location},
    )


@permission_required('catalogue.delete_location', raise_exception=True)
@require_POST
def delete(request, location_id):
    location = get_object_or_404(Location, id=location_id)
    try:
        location.delete()
    except RestrictedError:
        messages.error(
            request,
            'Ce lieu ne peut pas être supprimé car il est utilisé par une représentation.',
        )
        return redirect('catalogue:location-show', location_id=location.pk)
    messages.success(request, 'Lieu supprimé avec succès.')
    return redirect('catalogue:location-index')
