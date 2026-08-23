from rest_framework import serializers
from rest_framework.reverse import reverse

from .artist import Artist
from .show import Show


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


class ShowSerializer(serializers.ModelSerializer):
    location_name = serializers.CharField(
        source='location.designation',
        read_only=True,
        allow_null=True,
    )
    minimum_price = serializers.SerializerMethodField()
    links = serializers.SerializerMethodField()

    class Meta:
        model = Show
        fields = [
            'id',
            'slug',
            'title',
            'description',
            'duration',
            'created_in',
            'location',
            'location_name',
            'bookable',
            'minimum_price',
            'links',
        ]

    def get_links(self, obj):
        request = self.context.get('request')
        return {
            'self': reverse(
                'catalogue:show-api-detail',
                kwargs={'pk': obj.pk},
                request=request,
            ),
            'all_shows': reverse(
                'catalogue:show-api-list',
                request=request,
            ),
            'html_detail': reverse(
                'catalogue:show-show',
                kwargs={'show_id': obj.pk},
                request=request,
            ),
        }

    def get_minimum_price(self, obj):
        return getattr(obj, 'min_price', None)
