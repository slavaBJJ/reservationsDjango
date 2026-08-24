from django.http import Http404
from django.shortcuts import render
from django.utils import timezone

from catalogue.models import Representation


def index(request):
    representations = Representation.objects.select_related(
        'show',
        'location',
        'show__location',
    ).order_by('schedule', 'pk')
    title = 'Liste des représentations'

    return render(request, 'representation/index.html', {
        'representations': representations,
        'title': title,
    })


def show(request, representation_id):
    try:
        representation = Representation.objects.select_related(
            'show',
            'location',
            'show__location',
        ).get(id=representation_id)
    except Representation.DoesNotExist:
        raise Http404('Représentation inexistante')

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
    })
