from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.db.models.deletion import RestrictedError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from catalogue.forms import TypeForm
from catalogue.models import Type


def index(request):
    types = Type.objects.order_by('type', 'pk')
    return render(request, 'type/index.html', {'types': types})


def show(request, type_id):
    type_obj = get_object_or_404(
        Type.objects.prefetch_related('t_artistTypes__artist'),
        id=type_id,
    )
    return render(request, 'type/show.html', {'type': type_obj})


@permission_required('catalogue.add_type', raise_exception=True)
def create(request):
    form = TypeForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        type_obj = form.save()
        messages.success(request, 'Type artistique créé avec succès.')
        return redirect('catalogue:type-show', type_id=type_obj.pk)
    return render(request, 'type/create.html', {'form': form})


@permission_required('catalogue.change_type', raise_exception=True)
def edit(request, type_id):
    type_obj = get_object_or_404(Type, id=type_id)
    form = TypeForm(request.POST or None, instance=type_obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Type artistique modifié avec succès.')
        return redirect('catalogue:type-show', type_id=type_obj.pk)
    return render(request, 'type/edit.html', {'form': form, 'type': type_obj})


@permission_required('catalogue.delete_type', raise_exception=True)
@require_POST
def delete(request, type_id):
    type_obj = get_object_or_404(Type, id=type_id)
    try:
        type_obj.delete()
    except RestrictedError:
        messages.error(
            request,
            'Ce type ne peut pas être supprimé car il est associé à un artiste.',
        )
        return redirect('catalogue:type-show', type_id=type_obj.pk)
    messages.success(request, 'Type artistique supprimé avec succès.')
    return redirect('catalogue:type-index')
