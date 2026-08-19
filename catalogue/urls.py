"""reservationd.catalogue URL Configuration"""

from django.urls import path
from . import views
from api.catalogue.views import ArtistListCreateView, ArtistRetrieveUpdateDestroyView

app_name='catalogue'

urlpatterns = [
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


]