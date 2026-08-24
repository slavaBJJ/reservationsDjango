from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from catalogue.forms import ArtistForm
from catalogue.models import Artist


def index(request):
    artists = Artist.objects.order_by('lastname', 'firstname')
    return render(request, 'artist/index.html', {'artists': artists})


def show(request, artist_id):
    artist = get_object_or_404(
        Artist.objects.prefetch_related('a_artistTypes__type'),
        id=artist_id,
    )
    return render(request, 'artist/show.html', {'artist': artist})


@permission_required('catalogue.add_artist', raise_exception=True)
def create(request):
    form = ArtistForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        artist = form.save()
        messages.success(request, 'Nouvel artiste créé avec succès.')
        return redirect('catalogue:artist-show', artist_id=artist.pk)
    return render(request, 'artist/create.html', {'form': form})


@permission_required('catalogue.change_artist', raise_exception=True)
def edit(request, artist_id):
    artist = get_object_or_404(Artist, id=artist_id)
    form = ArtistForm(request.POST or None, instance=artist)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Artiste modifié avec succès.')
        return redirect('catalogue:artist-show', artist_id=artist.pk)
    return render(request, 'artist/edit.html', {'form': form, 'artist': artist})


@permission_required('catalogue.delete_artist', raise_exception=True)
@require_POST
def delete(request, artist_id):
    artist = get_object_or_404(Artist, id=artist_id)
    artist.delete()
    messages.success(request, 'Artiste supprimé avec succès.')
    return redirect('catalogue:artist-index')
