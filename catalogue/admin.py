from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from catalogue.models import (
    Artist,
    ArtistType,
    ArtistTypeShow,
    Locality,
    Location,
    Price,
    PressReview,
    Representation,
    RepresentationReservation,
    Reservation,
    Review,
    Show,
    Type,
    UserMeta,
)


@admin.register(Artist)
class ArtistAdmin(admin.ModelAdmin):
    list_display = ('firstname', 'lastname')
    search_fields = ('firstname', 'lastname')
    ordering = ('lastname', 'firstname')


@admin.register(Type)
class TypeAdmin(admin.ModelAdmin):
    list_display = ('type',)
    search_fields = ('type',)
    ordering = ('type',)


@admin.register(Locality)
class LocalityAdmin(admin.ModelAdmin):
    list_display = ('postal_code', 'locality')
    search_fields = ('postal_code', 'locality')
    ordering = ('postal_code', 'locality')


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('designation', 'locality', 'website', 'phone')
    search_fields = ('designation', 'slug', 'address', 'locality__locality')
    list_filter = ('locality',)
    list_select_related = ('locality',)


@admin.register(Price)
class PriceAdmin(admin.ModelAdmin):
    list_display = ('type', 'price', 'start_date', 'end_date')
    search_fields = ('type', 'description')
    list_filter = ('start_date', 'end_date')


@admin.register(Show)
class ShowAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_in', 'location', 'bookable', 'duration')
    search_fields = (
        'title',
        'slug',
        'description',
        'location__designation',
        'producers__username',
    )
    list_filter = ('bookable', 'created_in', 'location')
    list_select_related = ('location',)
    filter_horizontal = ('prices', 'producers')
    prepopulated_fields = {'slug': ('title',)}


@admin.register(Representation)
class RepresentationAdmin(admin.ModelAdmin):
    list_display = ('show', 'schedule', 'location')
    search_fields = ('show__title', 'location__designation')
    list_filter = ('schedule', 'location')
    list_select_related = ('show', 'location')
    date_hierarchy = 'schedule'


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'booking_date', 'status')
    search_fields = ('user__username', 'user__email', 'status')
    list_filter = ('status', 'booking_date')
    list_select_related = ('user',)
    date_hierarchy = 'booking_date'


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'show', 'stars', 'validated', 'created_at')
    search_fields = ('user__username', 'show__title', 'review')
    list_filter = ('validated', 'stars', 'created_at')
    list_select_related = ('user', 'show')
    date_hierarchy = 'created_at'


@admin.register(PressReview)
class PressReviewAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'user',
        'show',
        'moderation_status',
        'moderated_by',
        'created_at',
    )
    search_fields = ('title', 'content', 'user__username', 'show__title')
    list_filter = ('moderation_status', 'created_at')
    list_select_related = ('user', 'show', 'moderated_by')
    date_hierarchy = 'created_at'


@admin.register(ArtistType)
class ArtistTypeAdmin(admin.ModelAdmin):
    list_display = ('artist', 'type')
    search_fields = (
        'artist__firstname',
        'artist__lastname',
        'type__type',
    )
    list_filter = ('type',)
    list_select_related = ('artist', 'type')


@admin.register(ArtistTypeShow)
class ArtistTypeShowAdmin(admin.ModelAdmin):
    list_display = ('show', 'artist_type')
    search_fields = (
        'show__title',
        'artist_type__artist__firstname',
        'artist_type__artist__lastname',
        'artist_type__type__type',
    )
    list_select_related = (
        'show',
        'artist_type__artist',
        'artist_type__type',
    )


@admin.register(RepresentationReservation)
class RepresentationReservationAdmin(admin.ModelAdmin):
    list_display = (
        'reservation',
        'representation',
        'price',
        'quantity',
    )
    search_fields = (
        'reservation__user__username',
        'representation__show__title',
    )
    list_select_related = (
        'reservation__user',
        'representation__show',
    )


# Define an inline admin descriptor for Employee model
# which acts a bit like a singleton
class UserMetaInline(admin.StackedInline):
    model = UserMeta
    can_delete = False
    verbose_name_plural = "user_meta"

# Define a new User admin

class UserAdmin(BaseUserAdmin):
    inlines = [UserMetaInline]


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
