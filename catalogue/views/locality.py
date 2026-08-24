from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.db.models.deletion import RestrictedError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from catalogue.forms import LocalityForm
from catalogue.models import Locality


def index(request):
    localities = Locality.objects.order_by('postal_code', 'locality', 'pk')
    return render(request, 'locality/index.html', {'localities': localities})


def show(request, locality_id):
    locality = get_object_or_404(
        Locality.objects.prefetch_related('locations'),
        id=locality_id,
    )
    return render(request, 'locality/show.html', {'locality': locality})


@permission_required('catalogue.add_locality', raise_exception=True)
def create(request):
    form = LocalityForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        locality = form.save()
        messages.success(request, 'Localité créée avec succès.')
        return redirect('catalogue:locality-show', locality_id=locality.pk)
    return render(request, 'locality/create.html', {'form': form})


@permission_required('catalogue.change_locality', raise_exception=True)
def edit(request, locality_id):
    locality = get_object_or_404(Locality, id=locality_id)
    form = LocalityForm(request.POST or None, instance=locality)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Localité modifiée avec succès.')
        return redirect('catalogue:locality-show', locality_id=locality.pk)
    return render(
        request,
        'locality/edit.html',
        {'form': form, 'locality': locality},
    )


@permission_required('catalogue.delete_locality', raise_exception=True)
@require_POST
def delete(request, locality_id):
    locality = get_object_or_404(Locality, id=locality_id)
    try:
        locality.delete()
    except RestrictedError:
        messages.error(
            request,
            'Cette localité ne peut pas être supprimée car elle contient des lieux.',
        )
        return redirect('catalogue:locality-show', locality_id=locality.pk)
    messages.success(request, 'Localité supprimée avec succès.')
    return redirect('catalogue:locality-index')
