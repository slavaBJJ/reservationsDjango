from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from catalogue.forms import PriceForm
from catalogue.models import Price


def index(request):
    prices = Price.objects.prefetch_related('shows').order_by('price', 'type', 'pk')
    return render(request, 'price/index.html', {'prices': prices})


def show(request, price_id):
    price = get_object_or_404(Price.objects.prefetch_related('shows'), pk=price_id)
    return render(request, 'price/show.html', {'price': price})


@permission_required('catalogue.add_price', raise_exception=True)
def create(request):
    form = PriceForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        price = form.save()
        messages.success(request, 'Tarif créé avec succès.')
        return redirect('catalogue:price-show', price_id=price.pk)
    return render(request, 'price/form.html', {'form': form, 'title': 'Créer un tarif'})


@permission_required('catalogue.change_price', raise_exception=True)
def edit(request, price_id):
    price = get_object_or_404(Price, pk=price_id)
    form = PriceForm(request.POST or None, instance=price)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Tarif modifié avec succès.')
        return redirect('catalogue:price-show', price_id=price.pk)
    return render(request, 'price/form.html', {
        'form': form, 'price': price, 'title': 'Modifier le tarif',
    })


@permission_required('catalogue.delete_price', raise_exception=True)
@require_POST
def delete(request, price_id):
    price = get_object_or_404(Price, pk=price_id)
    if price.shows.exists():
        messages.error(
            request,
            'Ce tarif ne peut pas être supprimé car il est associé à un spectacle.',
        )
        return redirect('catalogue:price-show', price_id=price.pk)
    price.delete()
    messages.success(request, 'Tarif supprimé avec succès.')
    return redirect('catalogue:price-index')
