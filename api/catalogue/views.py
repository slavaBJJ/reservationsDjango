from catalogue.models import Artist
from catalogue.models.serializers import ArtistSerializer
from rest_framework import generics

class ArtistListCreateView(generics.ListCreateAPIView):
    queryset = Artist.objects.all()
    serializer_class = ArtistSerializer

class ArtistRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Artist.objects.all()
    serializer_class = ArtistSerializer
