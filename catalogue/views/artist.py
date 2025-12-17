from django.shortcuts import render, redirect, get_object_or_404
from django.http import Http404
from django.contrib import messages
from catalogue.models import Artist
from catalogue.forms import ArtistForm

def index(request):
    artists = Artist.objects.all()
    print (artists)

    return render(request, 'artist/index.html',{
        'artists':artists,
    })

def show (request, artist_id):
    try:
        artist = Artist.objects.get(id=artist_id)
    except Artist.DoesNotExist:
        raise Http404('Artist inexistant')

    return render(request,'artist/show.html',{'artist':artist})


def create(request):
    form = ArtistForm(request.POST or None)

    if request.method =='POST':
        if form.is_valid():
            form.save()
            messages.add_message(request, messages.SUCCESS, "Nouvel artist crée avec succès.")

            return redirect('catalogue:artist-index')
        else:
            messages.add_message(request, messages.ERROR,"Echec de l'ajout d'un nouvel artiste ! ")
    return render(request,'artist/create.html',{'form': form})



def edit(request, artist_id):
    # fetch the object related to passed id

    artist = Artist.objects.get(id=artist_id)
    # pass the object as instance in form

    form = ArtistForm(request.POST or None, instance = artist)

    if request.method == 'POST':
        method = request.POST.get('_method', '').upper()

        if method == 'PUT':
        # save the data from the form and
        # redirect to detail_view
            if form.is_valid():
                form.save()
                messages.success(request,"Artist modifié avec succès.")
                return render(request, "artist/show.html", { 'artist' : artist,})
            else:
                messages.error(request,"Echec de la modification de l'artiste")
    return render(request, 'artist/edit.html', { 'form' : form, 'artist' : artist, })

def delete(request, artist_id):
    artist = get_object_or_404(Artist, id=artist_id)
    print (artist)

    if request.method=="POST":
        method=request.POST.get('_method','').upper()

        print(f"{method=}")

        if method=="DELETE":
            artist.delete()
            messages.succes(request,"Artist supprimé avec succès ")

            return redirect('catalogue:artist-index')
    messages.error(request,"Echec de la supression de l'artiste ! ")
    return render(request,'artist/show.html',{'artist':artist,})



