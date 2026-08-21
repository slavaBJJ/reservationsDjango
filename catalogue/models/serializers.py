from rest_framework import serializers
from rest_framework.reverse import reverse

from .artist import Artist


class ArtistSerializer(serializers.HyperlinkedModelSerializer):
    links = serializers.SerializerMethodField()

    class Meta:
        model = Artist
        fields = ['id', 'firstname', 'lastname', 'links']

    def get_links(self, obj):
        request = self.context.get('request')
        return {
            'self': reverse(
                'catalogue:artist-detail',
                kwargs={'pk': obj.pk},
                request=request,
            ),
            'all_artists': reverse(
                'catalogue:artist-list',
                request=request,
            ),
        }
