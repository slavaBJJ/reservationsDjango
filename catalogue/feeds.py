from django.contrib.syndication.views import Feed
from django.urls import reverse
from django.utils import timezone

from catalogue.models import Representation


class UpcomingRepresentationsFeed(Feed):
    title = 'Prochaines représentations'
    link = '/catalogue/representation/'
    description = 'Les prochaines représentations disponibles au catalogue.'

    def items(self):
        return Representation.objects.select_related(
            'show',
            'location',
            'show__location',
        ).filter(
            schedule__gt=timezone.now(),
        ).order_by('schedule', 'pk')[:20]

    def item_title(self, item):
        return item.show.title

    def item_description(self, item):
        location = item.location or item.show.location
        location_name = location.designation if location else 'Lieu à déterminer'
        return (
            f'{item.schedule:%d/%m/%Y à %H:%M} — {location_name}. '
            f'{item.show.description or ""}'
        ).strip()

    def item_link(self, item):
        return reverse('catalogue:representation-show', args=[item.pk])

    def item_pubdate(self, item):
        return item.schedule

    def item_guid(self, item):
        return f'representation-{item.pk}'
