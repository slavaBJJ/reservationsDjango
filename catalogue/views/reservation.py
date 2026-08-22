from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from catalogue.forms import ReservationForm
from catalogue.models import (
    Representation,
    RepresentationReservation,
    Reservation,
)


@login_required
def create(request, representation_id):
    representation = get_object_or_404(
        Representation.objects.select_related('show', 'location'),
        pk=representation_id,
    )

    if not representation.show.bookable or representation.schedule <= timezone.now():
        messages.error(request, "Cette représentation n'est pas réservable.")
        return redirect('catalogue:representation-show', representation_id=representation.pk)

    form = ReservationForm(
        request.POST or None,
        representation=representation,
    )

    if request.method == 'POST' and form.is_valid():
        selected_price = form.cleaned_data['price']

        with transaction.atomic():
            reservation = Reservation.objects.create(
                user=request.user,
                status='en attente',
            )
            RepresentationReservation.objects.create(
                reservation=reservation,
                representation=representation,
                price=selected_price.price,
                quantity=form.cleaned_data['quantity'],
            )

        messages.success(request, 'Votre réservation a bien été enregistrée.')
        return redirect('catalogue:representation-show', representation_id=representation.pk)

    return render(request, 'reservation/create.html', {
        'form': form,
        'representation': representation,
        'title': 'Réserver des places',
    })
