from django.db.models import Min, Q

from catalogue.models import Artist, Show
from catalogue.models.serializers import ArtistSerializer, ShowSerializer
from rest_framework import generics
from rest_framework.permissions import DjangoModelPermissions

from .pagination import AffiliatePagination
from .permissions import AffiliateCataloguePermission

class ArtistListCreateView(generics.ListCreateAPIView):
    queryset = Artist.objects.all()
    serializer_class = ArtistSerializer
    permission_classes = [DjangoModelPermissions]

class ArtistRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Artist.objects.all()
    serializer_class = ArtistSerializer
    permission_classes = [DjangoModelPermissions]


class ShowQuerysetMixin:
    def base_queryset(self):
        return Show.objects.select_related('location').annotate(
            min_price=Min('prices__price'),
        )


class ShowListCreateView(ShowQuerysetMixin, generics.ListCreateAPIView):
    serializer_class = ShowSerializer
    permission_classes = [AffiliateCataloguePermission]
    pagination_class = AffiliatePagination

    def get_queryset(self):
        queryset = self.base_queryset()
        search = self.request.query_params.get('q', '').strip()
        location = self.request.query_params.get('location', '').strip()
        bookable = self.request.query_params.get('bookable', '').lower()
        ordering = self.request.query_params.get('ordering', 'title')

        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search)
            )
        if location:
            queryset = queryset.filter(location__slug=location)
        if bookable in {'1', 'true', 'yes', 'oui'}:
            queryset = queryset.filter(bookable=True)
        elif bookable in {'0', 'false', 'no', 'non'}:
            queryset = queryset.filter(bookable=False)

        ordering_fields = {
            'title': ('title', 'pk'),
            '-title': ('-title', 'pk'),
            'created_in': ('created_in', 'title', 'pk'),
            '-created_in': ('-created_in', 'title', 'pk'),
            'duration': ('duration', 'title', 'pk'),
            '-duration': ('-duration', 'title', 'pk'),
            'price': ('min_price', 'title', 'pk'),
            '-price': ('-min_price', 'title', 'pk'),
        }
        return queryset.order_by(*ordering_fields.get(ordering, ('title', 'pk')))


class ShowRetrieveUpdateDestroyView(
    ShowQuerysetMixin,
    generics.RetrieveUpdateDestroyAPIView,
):
    serializer_class = ShowSerializer
    permission_classes = [AffiliateCataloguePermission]

    def get_queryset(self):
        return self.base_queryset()
