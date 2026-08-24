from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import BooleanField, Case, Exists, Min, OuterRef, Q, Value, When
from django.db.models.deletion import RestrictedError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from catalogue.forms import ShowForm
from catalogue.models import Location, Price, Representation, Show
from catalogue.review_rules import can_review_show
from catalogue.roles import ROLE_PRODUCER, has_role, is_producer_for


def index(request):
    search = request.GET.get('q', '').strip()
    location = request.GET.get('location', '')
    bookable = request.GET.get('bookable', '')
    sort = request.GET.get('sort', 'title')

    shows = Show.objects.select_related('location').annotate(
        min_price=Min('prices__price'),
        has_upcoming_representation=Exists(Representation.objects.filter(
            show_id=OuterRef('pk'), schedule__gt=timezone.now(),
        )),
        has_available_price=Exists(Price.objects.filter(shows=OuterRef('pk'))),
    ).annotate(
        is_reservable=Case(
            When(bookable=True, has_upcoming_representation=True,
                 has_available_price=True, then=Value(True)),
            default=Value(False), output_field=BooleanField(),
        ),
    )

    if search:
        shows = shows.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search)
        )

    if location.isdigit():
        shows = shows.filter(location_id=location)

    if bookable in {'0', '1'}:
        shows = shows.filter(is_reservable=(bookable == '1'))

    sort_fields = {
        'title': ('title', 'pk'),
        'location': ('location__designation', 'title', 'pk'),
        'bookable': ('is_reservable', 'title', 'pk'),
        'price': ('min_price', 'title', 'pk'),
    }
    if sort not in sort_fields:
        sort = 'title'

    shows = shows.order_by(*sort_fields[sort])
    page = Paginator(shows, 10).get_page(request.GET.get('page'))
    title = 'Liste des spectacles'

    return render(request, 'show/index.html', {
        'shows': page,
        'title': title,
        'locations': Location.objects.order_by('designation'),
        'search': search,
        'selected_location': location,
        'selected_bookable': bookable,
        'selected_sort': sort,
        'can_add_show': (
            request.user.is_authenticated
            and (
                request.user.has_perm('catalogue.add_show')
                or has_role(request.user, ROLE_PRODUCER)
            )
        ),
    })


def show(request, show_id):
    show = get_object_or_404(
        Show.objects.select_related('location').prefetch_related(
            'prices',
            'artistTypeShows__artist_type__artist',
            'artistTypeShows__artist_type__type',
        ),
        id=show_id,
    )

    title = "Fiche d'un spectacle"
    reviews = show.reviews.filter(
        moderation_status='approved',
    ).select_related('user').order_by('-created_at')
    user_review = None
    user_can_review = False
    if request.user.is_authenticated:
        user_review = show.reviews.filter(user=request.user).first()
        user_can_review = can_review_show(request.user, show)

    press_reviews = show.press_reviews.filter(
        moderation_status='approved',
    ).select_related('user')

    upcoming_representations = show.representations.filter(
        schedule__gt=timezone.now(),
    ).select_related('location').order_by('schedule')
    has_prices = show.prices.exists()

    return render(request, 'show/show.html', {
        'show': show,
        'title': title,
        'reviews': reviews,
        'user_review': user_review,
        'user_can_review': user_can_review,
        'press_reviews': press_reviews,
        'upcoming_representations': upcoming_representations,
        'has_prices': has_prices,
        'is_reservable': show.bookable and has_prices and upcoming_representations.exists(),
        'can_manage_show': _can_manage_show(request.user, show),
    })


def _can_manage_show(user, show):
    return (
        user.is_authenticated
        and (
            user.has_perm('catalogue.change_show')
            or is_producer_for(user, show)
        )
    )


@login_required
def create(request):
    if not (
        request.user.has_perm('catalogue.add_show')
        or has_role(request.user, ROLE_PRODUCER)
    ):
        raise PermissionDenied
    form = ShowForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        created_show = form.save()
        if has_role(request.user, ROLE_PRODUCER):
            created_show.producers.add(request.user)
        messages.success(request, 'Spectacle créé avec succès.')
        return redirect('catalogue:show-show', show_id=created_show.pk)
    return render(request, 'show/form.html', {
        'form': form, 'title': 'Créer un spectacle',
    })


@login_required
def edit(request, show_id):
    managed_show = get_object_or_404(Show, pk=show_id)
    if not _can_manage_show(request.user, managed_show):
        raise PermissionDenied
    form = ShowForm(request.POST or None, instance=managed_show)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Spectacle modifié avec succès.')
        return redirect('catalogue:show-show', show_id=managed_show.pk)
    return render(request, 'show/form.html', {
        'form': form, 'managed_show': managed_show,
        'title': 'Modifier le spectacle',
    })


@login_required
@require_POST
def delete(request, show_id):
    managed_show = get_object_or_404(Show, pk=show_id)
    if not (
        request.user.has_perm('catalogue.delete_show')
        or is_producer_for(request.user, managed_show)
    ):
        raise PermissionDenied
    try:
        managed_show.delete()
    except RestrictedError:
        messages.error(
            request,
            'Ce spectacle ne peut pas être supprimé tant que des représentations existent.',
        )
        return redirect('catalogue:show-show', show_id=managed_show.pk)
    messages.success(request, 'Spectacle supprimé avec succès.')
    return redirect('catalogue:show-index')
