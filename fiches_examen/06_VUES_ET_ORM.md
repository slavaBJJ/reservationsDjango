# 06 — Vues Django et ORM

## Quand utiliser cette fiche ?

Après les modèles, migrations et données, pour transformer une URL en lecture ou modification contrôlée de la base.

```text
URL → vue (contrôleur) → ORM → base → contexte → template → réponse
```

Une **classe de modèle** décrit une entité/table ; une **instance** représente une ligne. Une vue orchestre la requête, mais ne doit pas déplacer toutes les règles métier hors des modèles, formulaires et contraintes.

## Étapes dans l’ordre

```text
1. Définir l'entrée URL et la méthode HTTP
2. Récupérer/filtrer les objets avec l'ORM
3. Vérifier authentification et autorisation
4. Valider les données reçues
5. Modifier seulement après validation
6. Construire le contexte ou la réponse JSON
7. Optimiser les relations
8. Tester succès, vide, 404 et accès refusé
```

## Vue de liste

```python
from django.shortcuts import render

from application.models import Model


def index(request):
    objects = Model.objects.all()
    return render(
        request,
        'model/index.html',
        {'objects': objects},
    )
```

- `render` fabrique une réponse HTML depuis un template.
- `Model` est la classe à remplacer.
- `request` contient la requête, l'utilisateur et les paramètres.
- `Model.objects.all()` renvoie un `QuerySet`, évalué lorsque nécessaire.
- Le dictionnaire est le contexte ; le template recevra `objects`.

Exemple réel : `catalogue.views.category.index` précharge `shows`, trie les catégories puis rend `category/index.html`.

## Vue de détail

```python
from django.shortcuts import get_object_or_404

object = get_object_or_404(Model, pk=object_id)
```

`get_object_or_404` renvoie une instance ou une réponse 404 propre. Comparaison :

| Méthode | Résultat | Si absent | Si plusieurs |
|---|---|---|---|
| `get_object_or_404()` | une instance | 404 | erreur si recherche non unique |
| `Model.objects.get()` | une instance | `DoesNotExist` | `MultipleObjectsReturned` |
| `Model.objects.filter(...).first()` | instance ou `None` | `None` | prend la première selon l'ordre |

Ne pas utiliser `first()` pour cacher une incohérence lorsque le métier exige exactement un objet.

## Méthodes ORM essentielles

```python
Model.objects.all()
Model.objects.filter(active=True)
Model.objects.exclude(status='hidden')
Model.objects.get(pk=1)
Model.objects.first()
Model.objects.filter(active=True).exists()
Model.objects.filter(active=True).count()
Model.objects.order_by('name', '-created_at')
Model.objects.create(name='Exemple')
Model.objects.filter(active=False).update(active=True)
Model.objects.filter(active=False).delete()
Model.objects.get_or_create(name='Exemple')
Model.objects.update_or_create(name='Exemple', defaults={'active': True})
```

- `all`, `filter`, `exclude`, `order_by` renvoient des `QuerySet` chaînables.
- `get` renvoie une instance et exige une correspondance unique.
- `first` renvoie une instance ou `None`.
- `exists` renvoie un booléen ; `count` un entier.
- `create` renvoie l'instance sauvegardée.
- `update` renvoie le nombre de lignes modifiées et contourne `save()`.
- `delete` renvoie des informations de suppression et peut déclencher `PROTECT`/`RESTRICT`.
- `get_or_create` et `update_or_create` renvoient `(instance, created)`.

## Lookups

```python
name__exact='Théâtre'
name__iexact='théâtre'
name__contains='âtre'
name__icontains='ATRE'
name__startswith='Thé'
pk__in=[1, 2, 3]
seats__gt=0
seats__gte=1
schedule__lt=limit
schedule__lte=limit
location__isnull=True
```

- `i` indique généralement une comparaison insensible à la casse selon la base.
- `gt/gte/lt/lte` signifient supérieur, supérieur ou égal, inférieur, inférieur ou égal.
- `isnull` teste SQL `NULL`.

## Traverser les relations

```python
Room.objects.filter(location__slug=location_slug)
Show.objects.filter(tags__tag=tag_value)
Representation.objects.filter(room__location=location)
Show.objects.filter(representations__room=room)
```

Le double soulignement traverse une relation. `Room` et `Tag` sont des modèles d'examen encore absents du projet ; `Show.representations` est un vrai accès inverse actuel.

**À renommer :** modèles, champs, `related_name` et variables selon le sujet.

## Recherche GET par mot-clé

```python
from django.db.models import Q

query = request.GET.get('q', '').strip()
shows = Show.objects.all()
if query:
    shows = shows.filter(
        Q(title__icontains=query) |
        Q(tags__tag__icontains=query)
    ).distinct()
result_count = shows.count()
```

- GET convient à une recherche sans modification et permet une URL partageable.
- `''` évite `None`; `strip()` retire les espaces externes.
- `Q(...) | Q(...)` exprime un OU.
- Une jointure M2M peut produire plusieurs lignes SQL pour un même spectacle ; `distinct()` élimine les doublons.
- `count()` calcule le nombre de résultats.

Le projet recherche actuellement dans `Show.title` et `Show.description`; la branche par tags est un exemple futur.

## Exclure une relation

Version courte :

```python
shows = Show.objects.exclude(tags__tag=tag_value)
```

Avec plusieurs jointures/conditions, une sous-requête explicite est parfois plus robuste et plus lisible :

```python
from django.db.models import Exists, OuterRef

matching_tags = Tag.objects.filter(
    shows=OuterRef('pk'),
    tag=tag_value,
)
shows = Show.objects.annotate(
    has_tag=Exists(matching_tags),
).filter(has_tag=False)
```

- `OuterRef('pk')` relie la sous-requête au spectacle courant.
- `Exists` calcule un booléen sans charger les tags.
- Le filtre final conserve ceux qui ne possèdent pas le tag.

## Optimisation et problème N+1

```python
Representation.objects.select_related('room', 'room__location', 'show')
Category.objects.prefetch_related('shows')
```

- `select_related()` joint les FK/one-to-one vers un objet unique.
- `prefetch_related()` effectue une requête séparée pour les collections inverses et M2M.
- N+1 signifie : une requête pour la liste, puis une requête supplémentaire par ligne. Précharger évite ce coût.
- Dans le projet actuel, remplacer l'exemple `room` par `location` tant que `Room` n'existe pas.

## GET et POST

```python
if request.method == 'POST':
    # valider puis modifier
    ...
```

- GET lit/recherche et ne devrait généralement pas modifier les données.
- POST soumet une création, modification ou action ; il requiert CSRF dans un formulaire navigateur.
- Le backend doit vérifier la méthode, même si le bouton n'apparaît que dans le template.

## Réponses

```python
return render(request, 'model/index.html', context)
return redirect('catalogue:show-show', show_id=show.pk)
return JsonResponse({'success': True})
return HttpResponse('Texte', content_type='text/plain')
```

- `render()` produit du HTML.
- `redirect()` produit une redirection, souvent après un POST réussi.
- `JsonResponse()` sérialise un dictionnaire JSON pour JavaScript/API.
- `HttpResponse()` produit une réponse brute, utile notamment pour CSV ou texte.

## Messages

```python
from django.contrib import messages

messages.success(request, 'Enregistrement réussi.')
messages.error(request, 'Impossible d’enregistrer.')
```

Le template de base réel affiche déjà `messages` avec des alertes Bootstrap.

## Exemples prêts à adapter

```python
def category_detail(request, slug):
    category = get_object_or_404(
        Category.objects.prefetch_related('shows'),
        slug=slug,
    )
    return render(request, 'category/show.html', {'category': category})
```

**À renommer :** fonction, paramètre, modèle, lookup, template et clé de contexte. Ce patron correspond de près à la vraie vue catégorie.

## Erreurs fréquentes

- Oublier `return` devant `render`, `redirect` ou `JsonResponse`.
- Utiliser `get()` pour une collection.
- Laisser remonter `DoesNotExist` au lieu d'un 404 attendu.
- Employer une clé de contexte différente de celle du template.
- Oublier `distinct()` après certaines jointures M2M.
- Créer un N+1 dans une boucle de template.
- Confondre la classe `Show` et l'instance `show`.
- Modifier des données pendant GET.
- Faire confiance à un identifiant ou rôle envoyé par le navigateur.

## Vérifications

```powershell
.venv\Scripts\python.exe manage.py check
.venv\Scripts\python.exe manage.py test
```

Tester aussi une liste vide, un identifiant absent, un utilisateur non autorisé et les paramètres de recherche combinés.

## Checklist express

```text
[ ] Méthode GET/POST correcte
[ ] Objet absent géré en 404
[ ] Permission vérifiée côté vue
[ ] Formulaire validé avant save
[ ] Contexte cohérent avec le template
[ ] distinct utilisé si nécessaire
[ ] select_related/prefetch_related réfléchis
[ ] redirection après POST
[ ] cas vide et erreurs testés
```
