# 07 — Routes Django paramétrées

## Quand utiliser cette fiche ?

Pour relier une adresse à une vue et transmettre un identifiant, slug, nom, mot-clé ou UUID.

## Étapes dans l’ordre

```text
1. Choisir une URL lisible
2. Choisir le convertisseur
3. Nommer le paramètre
4. Déclarer la vue avec le même nom
5. Nommer la route
6. Générer l'URL avec son namespace
7. Tester valeur valide, absente et encodée
```

## Organisation

Le projet utilise :

```python
# reservations/urls.py
from django.urls import include, path

urlpatterns = [
    path('catalogue/', include('catalogue.urls')),
]
```

- Le fichier du projet choisit le préfixe global.
- `include()` délègue la suite à l'application.

Dans l'application :

```python
# catalogue/urls.py
from django.urls import path
from . import views

app_name = 'catalogue'

urlpatterns = [
    # routes de l'application
]
```

- `app_name` crée le namespace `catalogue`.
- `urlpatterns` est la liste examinée dans l'ordre.

## Route simple

```python
path('rooms/', views.room.index, name='room-index')
```

- `'rooms/'` est le chemin après `/catalogue/`.
- `views.room.index` est le contrôleur appelé.
- `name` permet de générer l'URL sans la coder en dur.

## Convertisseurs de paramètres

```python
path('room/<int:room_id>/', views.room.show, name='room-show')
path('category/<slug:slug>/', views.category.show, name='category-show')
path('language/<str:name>/', views.language.show, name='language-show')
path('job/<uuid:identifier>/', views.job.show, name='job-show')
```

| Convertisseur | Valeur Python | Usage |
|---|---|---|
| `int` | entier positif | clé primaire numérique |
| `slug` | chaîne type lettres/chiffres/tirets/underscores | URL métier stable |
| `str` | chaîne sans `/` | nom ou mot-clé |
| `uuid` | instance UUID | identifiant UUID |

Django extrait la valeur, la convertit, puis l'envoie à la vue comme argument nommé.

## Exemple avec identifiant

```python
path(
    'room/<int:room_id>/',
    views.room.show,
    name='room-show',
)
```

```python
def show(request, room_id):
    room = get_object_or_404(Room, pk=room_id)
    return render(request, 'room/show.html', {'room': room})
```

Le nom `room_id` doit être identique dans la route et la signature. La vue convertit cet identifiant en instance avec un 404 propre.

## Exemple avec slug

```python
path(
    'category/<slug:category_slug>/',
    views.category.show,
    name='category-show',
)
```

```python
def show(request, category_slug):
    category = get_object_or_404(Category, slug=category_slug)
    return render(request, 'category/show.html', {'category': category})
```

Ce patron correspond à la route réelle du projet. Un slug évite d'exposer un nom avec espaces et accents.

## Exemple avec texte

```python
path('language/<str:name>/', views.language.fluent_artists, name='language-artists')
```

```python
def fluent_artists(request, name):
    artists = Artist.objects.filter(
        artist_languages__language__name__iexact=name,
        artist_languages__level='fluent',
    ).distinct()
    return render(request, 'language/artists.html', {'artists': artists})
```

Espaces et accents doivent être encodés dans l'URL. Un slug ou un identifiant est souvent plus robuste qu'un nom mutable. Ne pas décoder manuellement une valeur déjà fournie par Django.

## Génération dans les templates

```django
{% url 'catalogue:room-show' room.id %}
{% url 'catalogue:category-show' category.slug %}
```

- `catalogue:` est le namespace.
- Les arguments doivent respecter l'ordre et le type de la route.

## Redirection

```python
return redirect(
    'catalogue:room-show',
    room_id=room.pk,
)
```

Le nom du mot-clé doit correspondre à `<int:room_id>`.

## Routes inspirées des examens

Ces modèles sont génériques : adapter les noms de champs aux modèles réellement créés.

### Spectacles d’une salle

```python
path('room/<int:room_id>/shows/', views.room.shows, name='room-shows')

def shows(request, room_id):
    room = get_object_or_404(Room, pk=room_id)
    shows = Show.objects.filter(representations__room=room).distinct()
    return render(request, 'room/shows.html', {'room': room, 'shows': shows})
```

Template : `room/shows.html`. **À renommer :** route, fonction, champs inverses et contexte.

### Artistes parlant couramment une langue

```python
path('language/<slug:slug>/fluent-artists/', views.language.fluent, name='language-fluent')

def fluent(request, slug):
    language = get_object_or_404(Language, slug=slug)
    artists = Artist.objects.filter(
        artist_languages__language=language,
        artist_languages__level='fluent',
    ).distinct()
    return render(request, 'language/fluent.html', {'language': language, 'artists': artists})
```

Template : `language/fluent.html`.

### Vidéos des spectacles d’un artiste

```python
path('artist/<int:artist_id>/videos/', views.artist.videos, name='artist-videos')

def videos(request, artist_id):
    artist = get_object_or_404(Artist, pk=artist_id)
    videos = Video.objects.filter(
        show__artist_types__artist=artist,
    ).distinct()
    return render(request, 'artist/videos.html', {'artist': artist, 'videos': videos})
```

Template : `artist/videos.html`. Le chemin ORM exact doit être adapté au mapping créé ; le projet actuel passe par `ArtistType`/`ArtistTypeShow`.

### Spectacles ne possédant pas un tag

```python
path('tag/<slug:slug>/without/', views.tag.without, name='tag-without')

def without(request, slug):
    tag = get_object_or_404(Tag, slug=slug)
    shows = Show.objects.exclude(tags=tag).distinct()
    return render(request, 'tag/without.html', {'tag': tag, 'shows': shows})
```

Template : `tag/without.html`.

### Spectacles d’une catégorie

```python
path('category/<slug:category_slug>/', views.category.show, name='category-show')

def show(request, category_slug):
    category = get_object_or_404(
        Category.objects.prefetch_related('shows'),
        slug=category_slug,
    )
    return render(request, 'category/show.html', {'category': category})
```

Template : `category/show.html`; cet exemple correspond à l'implémentation réelle.

## Ordre des routes

```text
room/create/
room/<str:name>/
```

Django choisit la première route compatible. Si la route dynamique vient d'abord, `create` peut être interprété comme un nom. Placer les chemins fixes spécifiques avant les chemins dynamiques ambigus. Avec `<int:id>`, ce conflit particulier n'existe pas.

## Slash final et `APPEND_SLASH`

Une convention uniforme évite des redirections inattendues. Avec `APPEND_SLASH=True` et `CommonMiddleware`, Django peut rediriger `/rooms` vers `/rooms/`. Un POST sans slash peut perdre ses données ou échouer selon la situation : générer les URLs avec `{% url %}`.

Le projet historique mélange actuellement routes avec et sans slash final ; suivre la route nommée plutôt que saisir l'adresse manuellement.

## Exemples prêts à adapter

```python
# urls.py
path('object/<int:object_id>/', views.object_detail, name='object-detail')

# views.py
def object_detail(request, object_id):
    object = get_object_or_404(Model, pk=object_id)
    return render(request, 'model/detail.html', {'object': object})
```

**À renommer :** chemin, convertisseur, paramètre aux deux endroits, fonction, modèle, template, contexte et nom de route.

## Erreurs fréquentes

- Paramètre URL `room_id` mais vue `id` sans correspondance.
- Oublier `catalogue:` dans `{% url %}`.
- Utiliser un nom de route inexistant et obtenir `NoReverseMatch`.
- Placer une route dynamique ambiguë avant `create/`.
- Passer `room` quand la route attend `room.id`, sauf convertisseur personnalisé.
- Oublier le slash final ou mélanger les conventions.
- Utiliser `<str:name>` pour une valeur instable ou contenant `/`.
- Coder l'URL en dur au lieu de la résoudre par son nom.

## Vérifications

```powershell
.venv\Scripts\python.exe manage.py check
```

La commande `show_urls`, parfois proposée dans des tutoriels, dépend d'une extension qui ne figure pas dans les dépendances actuelles. La vérification portable consiste à tester `reverse()` ou les pages.

```powershell
.venv\Scripts\python.exe manage.py test
```

## Checklist express

```text
[ ] Préfixe du projet compris
[ ] app_name défini
[ ] Route nommée
[ ] Convertisseur adapté
[ ] Paramètre identique dans la vue
[ ] Route fixe avant route dynamique ambiguë
[ ] {% url %} utilise le namespace
[ ] 404 testé
[ ] Slash cohérent
```
