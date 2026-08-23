from django.core.paginator import Paginator
from django.db.models import Min, Q
from django.http import Http404
from django.shortcuts import render

from catalogue.models import Location, Show
from catalogue.review_rules import can_review_show


def index(request):
    search = request.GET.get('q', '').strip()
    location = request.GET.get('location', '')
    bookable = request.GET.get('bookable', '')
    sort = request.GET.get('sort', 'title')

    shows = Show.objects.select_related('location').annotate(
        min_price=Min('prices__price'),
    )

    if search:
        shows = shows.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search)
        )

    if location.isdigit():
        shows = shows.filter(location_id=location)

    if bookable in {'0', '1'}:
        shows = shows.filter(bookable=(bookable == '1'))

    sort_fields = {
        'title': ('title', 'pk'),
        'location': ('location__designation', 'title', 'pk'),
        'bookable': ('bookable', 'title', 'pk'),
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
    })


def show(request, show_id):
    try:
        show = Show.objects.get(id=show_id)
    except Show.DoesNotExist:
        raise Http404('Spectacle inexistant')

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

    return render(request, 'show/show.html', {
        'show': show,
        'title': title,
        'reviews': reviews,
        'user_review': user_review,
        'user_can_review': user_can_review,
        'press_reviews': press_reviews,
    })
