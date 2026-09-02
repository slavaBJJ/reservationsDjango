# Choisir une relation ou une validation Django

Cette fiche sert à déterminer rapidement dans quelle famille se trouve une consigne d’examen.

Les quatre familles principales sont :

1. relation enfant-parent avec `ForeignKey` ;
2. association multiple simple avec `ManyToManyField` ;
3. association multiple avec informations supplémentaires ;
4. règle métier portant sur un ou plusieurs champs.

---

## 1. Questions à se poser avant de coder

### Question 1 — Quels sont les objets métier ?

Repérer les noms importants de la phrase.

Exemple :

> Un spectacle possède plusieurs vidéos.

Objets concernés :

- `Show` ;
- `Video`.

### Question 2 — Que dit la phrase dans chaque direction ?

Il faut toujours lire la relation dans les deux sens.

Exemple :

```text
Un spectacle possède plusieurs vidéos.
Une vidéo appartient à un seul spectacle.
```

On obtient :

```text
Show 1 ───────── N Video
```

### Question 3 — Combien d’objets peut-on avoir de chaque côté ?

Utiliser ce tableau :

| Formulation | Cardinalité probable |
|---|---:|
| un seul | `1` |
| zéro ou un | `0..1` |
| plusieurs | `N` |
| zéro ou plusieurs | `0..N` |
| un ou plusieurs | `1..N` |

### Question 4 — La relation peut-elle être absente ?

Exemple :

> Un artiste appartient éventuellement à une troupe.

Le mot « éventuellement » indique que la relation est facultative :

```python
null=True,
blank=True,
```

Pour une `ForeignKey` :

- `null=True` autorise `NULL` dans la base ;
- `blank=True` autorise une valeur vide dans les formulaires.

### Question 5 — La relation possède-t-elle ses propres informations ?

Exemple :

> Un artiste parle une langue avec un niveau de maîtrise.

Le niveau n’appartient pas uniquement à l’artiste ni uniquement à la langue. Il appartient à leur association.

Il faut donc un modèle intermédiaire.

### Question 6 — La règle dépend-elle d’un seul champ ou d’une combinaison ?

Exemples :

```text
seats > 0
```

La règle porte sur un champ.

```text
Une salle ne peut pas être occupée deux fois au même horaire.
```

La règle porte sur la combinaison :

```text
room + schedule
```

### Question 7 — Que doit-il se passer si le parent est supprimé ?

Choix fréquents :

| Choix | Effet |
|---|---|
| `CASCADE` | supprime aussi les enfants |
| `PROTECT` | interdit la suppression du parent utilisé |
| `RESTRICT` | interdit la suppression selon les dépendances présentes |
| `SET_NULL` | conserve l’enfant et retire la relation |

Ne pas choisir `CASCADE` automatiquement. Il faut analyser la règle métier.

---

## 2. Arbre de décision rapide

```text
Les deux modèles sont-ils liés ?
│
├── Non
│   └── Il s’agit probablement d’un champ ou d’une validation simple.
│
└── Oui
    │
    ├── Chaque A possède plusieurs B et chaque B possède un seul A
    │   └── ForeignKey placée dans B
    │
    ├── Plusieurs A possèdent plusieurs B
    │   │
    │   ├── L’association ne contient aucune autre donnée
    │   │   └── ManyToManyField simple
    │   │
    │   └── L’association contient un niveau, rôle, quantité, date, etc.
    │       └── Modèle intermédiaire + through
    │
    └── Un seul A correspond à un seul B
        └── OneToOneField
```

Pour une règle métier :

```text
La règle dépend-elle d’un seul champ ?
│
├── Oui
│   └── Validateur et éventuellement CheckConstraint
│
└── Non, elle combine plusieurs champs
    └── clean() + UniqueConstraint ou CheckConstraint
```

---

# Famille 1 — Enfant d’un parent avec `ForeignKey`

## Formulation à reconnaître

```text
Un parent possède plusieurs enfants.
Un enfant appartient à un seul parent.
```

Exemples d’examen :

- un spectacle possède plusieurs vidéos ;
- un lieu possède plusieurs salles ;
- une salle accueille plusieurs représentations ;
- une troupe regroupe plusieurs artistes.

## Représentation

```text
Parent 1 ───────── N Child
```

La clé étrangère se place du côté `N`, donc dans `Child`.

## Exemple générique

```python
from django.db import models


class Child(models.Model):
    parent = models.ForeignKey(
        'Parent',
        on_delete=models.PROTECT,
        related_name='children',
    )
```

Explications :

- `'Parent'` désigne le modèle associé ;
- `PROTECT` empêche de supprimer un parent encore utilisé ;
- `related_name='children'` crée l’accès inverse.

Accès aux données :

```python
child.parent
parent.children.all()
```

## Variante facultative

```python
parent = models.ForeignKey(
    'Parent',
    on_delete=models.SET_NULL,
    related_name='children',
    null=True,
    blank=True,
)
```

Cette variante convient lorsqu’un enfant peut exister sans parent, par exemple un artiste « Non affilié » à une troupe.

## Exemple `Show` et `Video`

```python
class Video(models.Model):
    title = models.CharField(max_length=255)
    video_url = models.URLField(unique=True)
    show = models.ForeignKey(
        'Show',
        on_delete=models.CASCADE,
        related_name='videos',
    )
```

Une vidéo retrouve son spectacle :

```python
video.show
```

Un spectacle retrouve ses vidéos :

```python
show.videos.all()
```

## Pièges

- placer la clé étrangère dans le mauvais modèle ;
- oublier `on_delete` ;
- utiliser `SET_NULL` sans `null=True` ;
- écrire `blank='True'` au lieu de `blank=True` ;
- déclarer la relation dans les deux modèles.

---

# Famille 2 — Association multiple avec `ManyToManyField`

## Formulation à reconnaître

```text
Plusieurs A peuvent être associés à plusieurs B.
```

Exemple :

```text
Un spectacle possède plusieurs tags.
Un tag peut appartenir à plusieurs spectacles.
```

## Représentation

```text
Show N ───────── N Tag
```

## Modèles

```python
class Tag(models.Model):
    tag = models.CharField(max_length=30, unique=True)

    def __str__(self):
        return self.tag
```

Dans `Show` :

```python
tags = models.ManyToManyField(
    'Tag',
    related_name='shows',
    blank=True,
)
```

Une seule déclaration suffit :

```python
show.tags.all()
tag.shows.all()
```

Django crée automatiquement une table intermédiaire ressemblant à :

```text
shows_tags
├── id
├── show_id
└── tag_id
```

## Manipulations

```python
show.tags.add(tag)
show.tags.remove(tag)
show.tags.set([tag1, tag2])
show.tags.clear()
```

Les objets doivent être enregistrés avant de créer l’association :

```python
show.save()
show.tags.add(tag)
```

## Requête

```python
shows = Show.objects.filter(
    tags__tag__iexact='humour',
).distinct()
```

`distinct()` évite les doublons produits par les jointures.

## Template

```django
<ul>
    {% for tag in show.tags.all %}
        <li>{{ tag.tag }}</li>
    {% empty %}
        <li>Aucun mot-clé.</li>
    {% endfor %}
</ul>
```

## Pièges

- créer deux `ManyToManyField` pour la même relation ;
- ajouter inutilement `null=True` ;
- oublier `blank=True` si la relation peut être vide ;
- utiliser `.add()` avant d’enregistrer l’objet principal ;
- oublier `distinct()` dans certaines recherches.

---

# Famille 3 — Many-to-many avec modèle intermédiaire

## Formulation à reconnaître

```text
Plusieurs A sont associés à plusieurs B,
et l’association contient une information supplémentaire.
```

Informations supplémentaires fréquentes :

- niveau ;
- rôle ;
- quantité ;
- date d’association ;
- statut ;
- ordre.

## Exemple artiste-langue

```text
Artist N ───── N Language
         level
```

## Modèle `Language`

```python
class Language(models.Model):
    name = models.CharField(max_length=60, unique=True)

    def __str__(self):
        return self.name
```

## Modèle intermédiaire

```python
class ArtistLanguage(models.Model):
    class Level(models.TextChoices):
        NATIVE = 'native', 'Langue maternelle'
        BEGINNER = 'beginner', 'Débutant'
        INTERMEDIATE = 'intermediate', 'Intermédiaire'
        FLUENT = 'fluent', 'Courant'

    artist = models.ForeignKey(
        'Artist',
        on_delete=models.CASCADE,
        related_name='language_links',
    )
    language = models.ForeignKey(
        Language,
        on_delete=models.PROTECT,
        related_name='artist_links',
    )
    level = models.CharField(
        max_length=20,
        choices=Level.choices,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['artist', 'language'],
                name='unique_artist_language',
            ),
        ]
```

La contrainte interdit deux associations entre le même artiste et la même langue.

## Déclaration de la relation

Dans `Artist` :

```python
languages = models.ManyToManyField(
    'Language',
    through='ArtistLanguage',
    related_name='artists',
    blank=True,
)
```

`through` indique à Django d’utiliser le modèle intermédiaire explicite.

## Accès

Pour obtenir seulement les langues :

```python
artist.languages.all()
```

Pour obtenir la langue et le niveau :

```python
artist.language_links.all()
```

Puis, pour chaque association :

```python
association.language
association.level
association.get_level_display()
```

## Création

```python
ArtistLanguage.objects.create(
    artist=artist,
    language=language,
    level=ArtistLanguage.Level.FLUENT,
)
```

## Formulaire

```python
class ArtistLanguageForm(forms.ModelForm):
    class Meta:
        model = ArtistLanguage
        fields = ['language', 'level']
```

Si l’artiste vient de l’URL :

```python
association = form.save(commit=False)
association.artist = artist
association.save()
```

## Template

```django
<ul>
    {% for association in artist.language_links.all %}
        <li>
            {{ association.language.name }}
            — {{ association.get_level_display }}
        </li>
    {% empty %}
        <li>Aucune langue renseignée.</li>
    {% endfor %}
</ul>
```

## Pièges

- utiliser une table automatique alors que la relation contient une donnée ;
- placer `level` dans `Artist` ou `Language` ;
- oublier `through` ;
- parcourir directement `artist.languages` lorsqu’on a besoin du niveau ;
- oublier l’unicité du couple artiste-langue.

---

# Famille 4 — Validation simple ou composée

## Formulations à reconnaître

```text
empêcher si...
doit être supérieur à...
ne peut pas dépasser...
doit être unique...
ne peut pas être utilisé au même moment...
```

## Exemple : nombre de places positif

La règle porte sur un seul champ :

```python
from django.core.validators import MinValueValidator
```

```python
seats = models.PositiveSmallIntegerField(
    validators=[MinValueValidator(1)],
)
```

Contrainte de base complémentaire :

```python
class Meta:
    constraints = [
        models.CheckConstraint(
            condition=models.Q(seats__gt=0),
            name='room_seats_greater_than_zero',
        ),
    ]
```

## Exemple : salle occupée au même moment

La règle combine :

```text
room + schedule
```

### Contrainte de base

```python
class Meta:
    constraints = [
        models.UniqueConstraint(
            fields=['room', 'schedule'],
            name='unique_room_schedule',
        ),
    ]
```

### Validation du formulaire

```python
class RepresentationForm(forms.ModelForm):
    class Meta:
        model = Representation
        fields = ['show', 'room', 'schedule']

    def clean(self):
        cleaned_data = super().clean()
        room = cleaned_data.get('room')
        schedule = cleaned_data.get('schedule')

        if room and schedule:
            conflicts = Representation.objects.filter(
                room=room,
                schedule=schedule,
            )

            if self.instance.pk:
                conflicts = conflicts.exclude(pk=self.instance.pk)

            if conflicts.exists():
                raise forms.ValidationError(
                    'Cette salle est déjà occupée à ce moment.'
                )

        return cleaned_data
```

`exclude(pk=self.instance.pk)` empêche l’objet modifié d’être considéré comme son propre conflit.

### Template des erreurs générales

```django
<form method="post">
    {% csrf_token %}
    {{ form.non_field_errors }}
    {{ form.as_p }}
    <button type="submit">Enregistrer</button>
</form>
```

## Pourquoi deux protections ?

```text
Formulaire
→ message compréhensible pour l’utilisateur

Contrainte de base
→ protection pour le formulaire, le shell, l’admin, l’API et les scripts
```

## Autres règles composées

```text
start_date <= end_date
requested_quantity <= remaining_seats
room + name doivent être uniques
artist + language doivent être uniques
```

## Pièges

- vérifier seulement dans le template ;
- vérifier uniquement dans le formulaire sans protéger la base ;
- utiliser `unique=True` sur `room` ;
- utiliser `unique=True` sur `schedule` ;
- oublier le cas de modification ;
- ne pas afficher `form.non_field_errors` ;
- confondre validateur et contrainte de base.

---

## 3. Tableau final de reconnaissance

| Phrase rencontrée | Famille | Solution principale |
|---|---|---|
| Un spectacle possède plusieurs vidéos | 1 | `ForeignKey` dans `Video` |
| Un artiste appartient éventuellement à une troupe | 1 | `ForeignKey` facultative dans `Artist` |
| Plusieurs spectacles possèdent plusieurs tags | 2 | `ManyToManyField` |
| Un artiste parle une langue avec un niveau | 3 | Modèle intermédiaire + `through` |
| Le nombre de places doit être supérieur à zéro | 4 | Validateur + `CheckConstraint` |
| Une salle ne peut pas être occupée deux fois au même moment | 4 | `clean()` + `UniqueConstraint` |

---

## 4. Checklist express

```text
[ ] J’ai identifié les modèles concernés
[ ] J’ai lu la relation dans les deux directions
[ ] J’ai déterminé les cardinalités
[ ] J’ai vérifié si la relation est facultative
[ ] J’ai vérifié si l’association contient une information
[ ] J’ai placé la ForeignKey du côté plusieurs
[ ] J’ai déclaré le ManyToManyField une seule fois
[ ] J’ai choisi on_delete consciemment
[ ] J’ai défini un related_name clair
[ ] J’ai identifié les règles portant sur plusieurs champs
[ ] J’ai prévu une validation compréhensible
[ ] J’ai prévu une contrainte de base si nécessaire
[ ] J’ai pensé aux données déjà présentes avant la migration
```
