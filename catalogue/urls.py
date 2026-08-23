"""reservationd.catalogue URL Configuration"""

from django.urls import path
from . import views
from api.catalogue.views import ArtistListCreateView, ArtistRetrieveUpdateDestroyView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .feeds import UpcomingRepresentationsFeed

app_name='catalogue'

urlpatterns = [
    path(
        'csv/shows/export/',
        views.csv_catalogue.export_shows,
        name='shows-csv-export',
    ),
    path(
        'csv/shows/import/',
        views.csv_catalogue.import_shows,
        name='shows-csv-import',
    ),
    path('press-reviews/', views.press_review.index, name='press-review-index'),
    path(
        'press-reviews/create/',
        views.press_review.create,
        name='press-review-create',
    ),
    path(
        'press-reviews/<int:press_review_id>/edit/',
        views.press_review.edit,
        name='press-review-edit',
    ),
    path(
        'press-reviews/<int:press_review_id>/delete/',
        views.press_review.delete,
        name='press-review-delete',
    ),
    path(
        'press-reviews/moderation/',
        views.press_review.moderation,
        name='press-review-moderation',
    ),
    path(
        'press-reviews/<int:press_review_id>/moderate/',
        views.press_review.moderate,
        name='press-review-moderate',
    ),
    path(
        'rss/representations/',
        UpcomingRepresentationsFeed(),
        name='representations-rss',
    ),
    path('artist/', views.artist.index, name='artist-index'),
    path('artist/<int:artist_id>', views.artist.show, name='artist-show'),
    path('artist/edit/<int:artist_id>',views.artist.edit, name='artist-edit'),
    path('artist/create', views.artist.create, name='artist-create'),
    path('artist/delete/<int:artist_id>',views.artist.delete, name='artist-delete'),
    path('type/',views.type.index, name ='type-index'),
    path('type/<int:type_id>', views.type.show, name = 'type-show'),
    path('api/artists/', ArtistListCreateView.as_view(), name='artist-list'),
    path('api/artists/<int:pk>/', ArtistRetrieveUpdateDestroyView.as_view(), name='artist-detail'),
    path('locality/', views.locality.index, name='locality-index'),
    path('locality/<int:locality_id>', views.locality.show, name='locality-show'),
    path('price/', views.price.index, name='price-index'),
    path('price/<int:price_id>', views.price.show, name='price-show'),
    path('location/', views.location.index, name='location-index'),
    path('location/<int:location_id>', views.location.show, name='location-show'),
    path('show/', views.show_.index, name='show-index'),
    path('show/<int:show_id>', views.show_.show, name='show-show'),
    path('show/<int:show_id>/review', views.review.create, name='review-create'),
    path('review/<int:review_id>/edit', views.review.edit, name='review-edit'),
    path('review/<int:review_id>/delete', views.review.delete, name='review-delete'),
    path('representation/', views.representation.index, name='representation-index'),
    path(
        'representation/<int:representation_id>',
        views.representation.show,
        name='representation-show',
    ),
    path(
        'representation/<int:representation_id>/reserve',
        views.reservation.create,
        name='reservation-create',
    ),
    path('reservation/', views.reservation.index, name='reservation-index'),
    path(
        'reservation/<int:reservation_id>',
        views.reservation.show,
        name='reservation-show',
    ),
    path('api/token/', TokenObtainPairView.as_view(), name='token-obtain-pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),


]
