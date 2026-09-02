# 03 — Créer et modifier des modèles Django

> Projet Réservations — fiche de révision compatible avec **Django 5.2.8**.
> Vocabulaire des sujets : **modèle Django = entité** ; relations entre modèles = **mapping relationnel** ; une vue Django joue généralement le rôle de **contrôleur**.

## 1. Où créer un modèle ?

### Organisation simple

Une petite application peut regrouper ses modèles dans un seul fichier :

```text
application/models.py
```

Django charge automatiquement ce module lorsque l'application figure dans `INSTALLED_APPS`.

### Organisation en paquet

Une application plus grande peut répartir ses modèles :

```text
application/models/
    __init__.py
    room.py
    video.py
```

Le projet Réservations utilise cette organisation dans `catalogue/models/` : un fichier par modèle. Le fichier `catalogue/models/__init__.py` importe ensuite les modèles afin que Django les découvre.

Pour un nouveau modèle `Room`, préférer un import explicite :

```python
from .room import Room
```

- `.` désigne le paquet courant `catalogue.models`.
- `room` est le fichier `room.py`.
- `Room` est la classe rendue accessible lorsque Django importe `catalogue.models`.

Le projet contient historiquement des imports globaux comme :

```python
from .room import *
```

Cette ligne importe tous les noms publics de `room.py`. Elle fonctionnerait avec l'organisation actuelle, mais `from .room import Room` est plus clair et limite les collisions de noms. Oublier l'import dans `__init__.py` peut empêcher Django de charger le modèle et donc de proposer sa migration.

> **À vérifier après création :** fichier présent, classe correctement nommée et import explicite ajouté dans `catalogue/models/__init__.py`.

## 2. Structure minimale d’un modèle

```python
from django.db import models


class ModelName(models.Model):
    name = models.CharField(max_length=60)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'table_name'
```

Explication des lignes importantes :

- `from django.db import models` importe les classes de champs et la classe de base de Django.
- `class ModelName(models.Model)` déclare une entité persistante. **À renommer :** `ModelName` en nom singulier PascalCase, par exemple `Room`.
- Django crée automatiquement une clé primaire `id` si aucune clé primaire n'est déclarée.
- `name = ...` crée une colonne texte obligatoire de 60 caractères au maximum.
- `__str__()` fournit un libellé lisible dans l'administration, le shell et les listes de choix.
- `return self.name` renvoie une chaîne ; il faut choisir un champ toujours exploitable.
- `class Meta` regroupe les options du modèle et les contraintes de table.
- `db_table` impose le nom SQL. **À renommer :** `'table_name'`, par exemple `'rooms'`.

Conventions utiles :

- classe : singulier en PascalCase, par exemple `PressReview` ;
- champ : minuscules avec `_`, par exemple `video_url` ;
- table : convention cohérente avec le projet. Réservations emploie notamment des noms pluriels explicites (`artists`, `shows`, etc.).

`db_table` est facultatif : sans lui, Django construit généralement `<application>_<modèle>`.

## 3. Choisir un type de champ

| Champ | Usage et exemple | Paramètres fréquents | Erreur fréquente |
|---|---|---|---|
| `models.CharField` | texte court : `name = models.CharField(max_length=60)` | `max_length`, `unique`, `choices` | oublier `max_length` |
| `models.TextField` | texte long : `description = models.TextField(blank=True)` | `blank`, `null` rarement utile | fixer une longueur sans besoin réel |
| `models.IntegerField` | entier signé : `rank = models.IntegerField()` | `default`, validateurs | l'utiliser pour un prix |
| `models.PositiveIntegerField` | entier positif ou nul : `stock = models.PositiveIntegerField()` | `default`, validateurs | croire que zéro est interdit |
| `models.PositiveSmallIntegerField` | petit entier positif ou nul : `seats = models.PositiveSmallIntegerField()` | validateurs | croire qu'il garantit `> 0` |
| `models.DecimalField` | montant exact : `price = models.DecimalField(max_digits=8, decimal_places=2)` | `max_digits`, `decimal_places` | utiliser `FloatField` pour de l'argent |
| `models.BooleanField` | oui/non : `active = models.BooleanField(default=True)` | `default` | écrire `default='False'` |
| `models.DateField` | date sans heure : `opening_date = models.DateField()` | `auto_now`, `auto_now_add` | l'utiliser lorsqu'une heure compte |
| `models.DateTimeField` | date et heure : `schedule = models.DateTimeField()` | `auto_now`, `auto_now_add` | fournir une date naïve avec les fuseaux actifs |
| `models.URLField` | URL validée : `video_url = models.URLField(max_length=255)` | `max_length`, `unique` | limiter une URL réaliste à 30 caractères |
| `models.EmailField` | adresse e-mail validée | `max_length`, `unique` | croire que la validation interdit toute adresse inexistante |
| `models.SlugField` | fragment d'URL : `slug = models.SlugField(unique=True)` | `max_length`, `unique`, `db_index` | oublier de générer/renseigner le slug |
| `models.ForeignKey` | plusieurs enfants vers un parent | `on_delete`, `related_name`, `null` | placer la clé du côté « un » |
| `models.ManyToManyField` | plusieurs objets de chaque côté | `related_name`, `blank`, `through` | mettre `null=True` |
| `models.OneToOneField` | au maximum un objet de chaque côté | `on_delete`, `related_name` | l'utiliser pour une relation one-to-many |

### Comparaisons à connaître

- **`CharField` / `TextField`** : `CharField` convient aux valeurs courtes et exige `max_length`; `TextField` convient aux descriptions longues.
- **`IntegerField` / `PositiveSmallIntegerField`** : le premier accepte les négatifs et une grande plage ; le second exclut les négatifs mais accepte normalement zéro et possède une plage plus petite dépendant de la base.
- **`FloatField` / `DecimalField`** : un flottant est approximatif ; `DecimalField` conserve une précision décimale adaptée aux prix.
- **`CharField` / `URLField`** : les deux stockent du texte, mais `URLField` ajoute une validation d'URL côté Django.
- **`DateField` / `DateTimeField`** : le premier stocke seulement le jour ; le second stocke aussi l'heure, indispensable pour une représentation.

## 4. Paramètres fréquents des champs

### `max_length`

Fixe la longueur maximale et est obligatoire pour `CharField`.

```python
name = models.CharField(max_length=60)
```

### `null`

Contrôle principalement la base : `null=True` permet de stocker SQL `NULL`.

```python
troupe = models.ForeignKey('Troupe', on_delete=models.SET_NULL, null=True)
```

Pour les champs texte, Django recommande généralement une chaîne vide plutôt que deux valeurs d'absence (`''` et `NULL`).

### `blank`

Contrôle principalement la validation Django : `blank=True` autorise une valeur vide dans un formulaire ou lors de `full_clean()`.

```python
description = models.TextField(blank=True)
```

Attention aux booléens :

```python
blank='True'  # incorrect : chaîne de caractères
blank=True    # correct : booléen Python
```

Pour une `ForeignKey` facultative dans la base **et** les formulaires, on utilise habituellement ensemble `null=True, blank=True`.

### `default`

Fournit une valeur lorsqu'aucune valeur n'est transmise.

```python
from django.utils import timezone

created_at = models.DateTimeField(default=timezone.now)
```

- `timezone.now` transmet la fonction : elle sera appelée pour chaque nouvel objet.
- `timezone.now()` appellerait la fonction immédiatement au chargement du module : ce n'est généralement pas souhaité comme valeur par défaut.
- Une valeur fixe reste possible : `active = models.BooleanField(default=True)`.

### `unique`

```python
name = models.CharField(max_length=60, unique=True)
```

`unique=True` crée une contrainte de base pour un champ unique et généralement un index utile aux recherches.

### `db_index`

```python
schedule = models.DateTimeField(db_index=True)
```

Ajoute un index pour accélérer certaines recherches, au prix d'espace disque et d'un coût lors des écritures. Ne pas indexer tous les champs sans mesurer le besoin.

### `editable`

```python
reference = models.CharField(max_length=20, editable=False)
```

Masque normalement le champ des formulaires générés par Django. Ce n'est pas une protection d'autorisation ni une garantie contre une écriture en code.

### `choices`

```python
status = models.CharField(max_length=20, choices=Status.choices)
```

Limite les choix proposés et validés par Django. Une contrainte de base séparée peut être nécessaire si la base doit elle-même refuser toute autre valeur.

### `auto_now` et `auto_now_add`

```python
created_at = models.DateTimeField(auto_now_add=True)
updated_at = models.DateTimeField(auto_now=True)
```

- `auto_now_add=True` renseigne la création une seule fois.
- `auto_now=True` actualise la valeur à chaque `save()`.
- Ces options rendent généralement le champ non éditable. Pour davantage de contrôle, utiliser un `default` appelable.

## 5. Exemple générique : table simple `Room`

```python
from django.db import models


class Room(models.Model):
    name = models.CharField(max_length=60, unique=True)
    seats = models.PositiveSmallIntegerField()

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'rooms'
```

- `Room` représente une salle ; Django ajoutera automatiquement `id`.
- `name` est obligatoire par défaut, limité à 60 caractères et unique dans la base.
- `seats` utilise un petit entier non négatif ; cela ne suffit pas forcément pour interdire zéro.
- `__str__()` affiche le nom de la salle.
- `db_table = 'rooms'` fixe le nom SQL.

Pour imposer strictement au moins une place, ajouter un validateur et/ou une contrainte de base présentés dans les sections 6 et 10.

**À renommer lors d'un copier-coller :** `Room`, `name`, `seats`, `'rooms'` et les longueurs selon le sujet.

## 6. Validateurs

Les validateurs produisent une `ValidationError` lors de la validation Python.

| Validateur | Usage courant |
|---|---|
| `MinValueValidator` | valeur numérique minimale |
| `MaxValueValidator` | valeur numérique maximale |
| `MinLengthValidator` | longueur minimale |
| `MaxLengthValidator` | longueur maximale |
| `RegexValidator` | format conforme à une expression régulière |

Exemple :

```python
from django.core.validators import MinValueValidator
from django.db import models


class Room(models.Model):
    seats = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)],
    )
```

- `MinValueValidator` est importé depuis les validateurs Django.
- `PositiveSmallIntegerField` refuse les négatifs.
- `validators=[MinValueValidator(1)]` impose au moins `1` pendant la validation Django.

Un `ModelForm` appelle la validation du modèle. On peut la déclencher explicitement avec :

```python
room.full_clean()
room.save()
```

- `full_clean()` exécute la validation des champs, du modèle et des contraintes.
- `save()` enregistre l'objet.

`save()` n'appelle pas automatiquement `full_clean()` dans tous les cas. Une écriture directe, certains scripts ou du SQL peuvent donc contourner un validateur Python. Si la règle doit rester vraie quelle que soit l'origine de l'écriture, ajouter aussi une `CheckConstraint` en base.

## 7. Clés étrangères

Bloc obligatoire prêt à adapter :

```python
parent = models.ForeignKey(
    'Parent',
    on_delete=models.PROTECT,
    related_name='children',
)
```

- Le champ est placé sur le modèle enfant, donc du côté « plusieurs ».
- `'Parent'` est une référence différée au modèle cible. **À renommer.**
- `PROTECT` empêche de supprimer un parent encore référencé.
- `related_name='children'` permet `parent.children.all()`. **À renommer et rendre unique.**
- Sans `null=True`, la relation est obligatoire en base.
- Sans `blank=True`, elle est obligatoire lors de la validation Django.

Variante facultative :

```python
parent = models.ForeignKey(
    'Parent',
    on_delete=models.SET_NULL,
    related_name='children',
    null=True,
    blank=True,
)
```

- `SET_NULL` conserve l'enfant et efface seulement sa référence si le parent est supprimé.
- `SET_NULL` exige `null=True`.
- `blank=True` rend le choix facultatif dans les formulaires.

Exemples adaptés aux sujets :

- `Video.show = ForeignKey('Show', PROTECT, related_name='videos')` : chaque vidéo appartient à un spectacle ; supprimer un spectacle utilisé est interdit, conformément au sujet vidéo.
- `Room.location = ForeignKey('Location', PROTECT, related_name='rooms')` : la clé se trouve dans `Room`, côté plusieurs.
- `Representation.room = ForeignKey('Room', PROTECT, related_name='representations')` : une représentation se déroule dans une salle.
- `Artist.troupe = ForeignKey('Troupe', SET_NULL, ..., null=True, blank=True)` : permet « Non affilié ».

> L'ancien sujet troupe dit à la fois qu'un artiste appartient à une seule troupe et qu'il faut proposer « Non affilié ». Il faut demander si la cardinalité minimale vaut `0` ou `1`; l'interface décrite suggère `0..1`.

## 8. Many-to-many simple

```python
tags = models.ManyToManyField(
    'Tag',
    related_name='shows',
    blank=True,
)
```

- Le champ serait placé naturellement sur `Show` : `show.tags.all()`.
- `'Tag'` désigne le modèle des mots-clés. **À renommer si le sujet change.**
- Django crée automatiquement une table intermédiaire contenant les deux clés étrangères.
- `related_name='shows'` permet `tag.shows.all()`.
- `blank=True` autorise un spectacle sans mot-clé dans les formulaires.
- `null=True` n'est normalement pas utilisé : l'absence se traduit par zéro ligne dans la table intermédiaire, pas par `NULL`.

Opérations après sauvegarde :

```python
show = Show.objects.create(title='Exemple')
show.tags.add(tag)
show.tags.remove(tag)
show.tags.set([tag1, tag2])
show.tags.clear()
```

- La première ligne sauvegarde `show` et lui attribue une clé primaire.
- `add()` ajoute une association.
- `remove()` retire une association précise.
- `set()` remplace la collection.
- `clear()` retire toutes les associations.

Une relation many-to-many ne peut pas être utilisée avant que l'objet principal ait une clé primaire : `Show().tags.add(tag)` échoue tant que le spectacle n'est pas sauvegardé.

## 9. Modèle intermédiaire

Un modèle intermédiaire explicite est nécessaire lorsque le mapping possède sa propre donnée.

### Forme générique

```python
class RelationModel(models.Model):
    first = models.ForeignKey(
        'FirstModel',
        on_delete=models.CASCADE,
        related_name='relation_objects',
    )
    second = models.ForeignKey(
        'SecondModel',
        on_delete=models.PROTECT,
        related_name='relation_objects',
    )
    extra_value = models.CharField(max_length=20)


class FirstModel(models.Model):
    seconds = models.ManyToManyField(
        'SecondModel',
        through='RelationModel',
        related_name='firsts',
    )
```

- `RelationModel` devient une véritable entité d'association.
- `first` et `second` sont les deux clés étrangères.
- `extra_value` stocke l'information appartenant au lien et non à un côté isolé.
- `seconds` expose la collection many-to-many.
- `through='RelationModel'` demande à Django d'utiliser cette table au lieu d'en créer une automatique.

**À renommer :** les trois classes, les champs `first`, `second`, `extra_value`, tous les `related_name` et la table éventuelle.

### Exemple `ArtistLanguage` avec niveau

```python
from django.db import models


class ArtistLanguage(models.Model):
    class Level(models.TextChoices):
        NATIVE = 'native', 'Langue maternelle'
        BEGINNER = 'beginner', 'Débutant'
        INTERMEDIATE = 'intermediate', 'Intermédiaire'
        FLUENT = 'fluent', 'Courant'

    artist = models.ForeignKey(
        'Artist',
        on_delete=models.CASCADE,
        related_name='artist_languages',
    )
    language = models.ForeignKey(
        'Language',
        on_delete=models.PROTECT,
        related_name='artist_languages',
    )
    level = models.CharField(
        max_length=20,
        choices=Level.choices,
    )


class Artist(models.Model):
    languages = models.ManyToManyField(
        'Language',
        through='ArtistLanguage',
        related_name='artists',
    )
```

- Chaque membre de `Level` contient la valeur enregistrée en base puis le libellé affiché.
- Exemple : `'fluent'` est stocké ; « Courant » est montré à l'utilisateur.
- `choices=Level.choices` raccorde l'énumération au champ.
- `artist.artist_languages.all()` renvoie les objets d'association avec leur niveau.
- `artist.languages.all()` renvoie directement les langues.
- `association.get_level_display()` renvoie le libellé lisible du niveau.

Création explicite recommandée lorsque `level` est obligatoire :

```python
ArtistLanguage.objects.create(
    artist=artist,
    language=language,
    level=ArtistLanguage.Level.FLUENT,
)
```

Chaque argument renseigne une colonne de l'association. Un simple `artist.languages.add(language)` ne fournit pas naturellement le niveau obligatoire ; créer l'objet intermédiaire rend l'intention claire.

## 10. Contraintes dans `Meta`

Django 5.2.8 accepte la syntaxe moderne `condition=` pour `CheckConstraint`.

### Salle et horaire uniques

```python
class Meta:
    constraints = [
        models.UniqueConstraint(
            fields=['room', 'schedule'],
            name='unique_room_schedule',
        ),
    ]
```

- `constraints` liste les règles imposées par la base.
- `fields` définit la combinaison : une salle peut réapparaître, et un horaire aussi, mais pas le même couple.
- `name` est obligatoire et doit être explicite et unique dans le projet.

### Couple artiste-langue unique

```python
class Meta:
    constraints = [
        models.UniqueConstraint(
            fields=['artist', 'language'],
            name='unique_artist_language',
        ),
    ]
```

Cette contrainte empêche deux associations identiques, même si leur niveau diffère.

### Nombre de places strictement positif

```python
class Meta:
    constraints = [
        models.CheckConstraint(
            condition=models.Q(seats__gt=0),
            name='room_seats_gt_zero',
        ),
    ]
```

- `models.Q(seats__gt=0)` exprime `seats > 0`.
- `condition=` est le paramètre moderne utilisé avec Django 5.2.
- La base refuse une valeur nulle ou négative selon cette condition et la nullabilité du champ.

`unique=True` porte sur un seul champ. `UniqueConstraint(fields=[...])` convient à une combinaison. Les contraintes de base protègent aussi les écritures venant de l'administration, de l'API ou du shell, contrairement à une règle uniquement placée dans un formulaire.

> Une contrainte `room + schedule` interdit deux horaires exactement égaux. Elle ne détecte pas à elle seule deux intervalles qui se chevauchent ; ce problème nécessite une règle plus élaborée selon la base et le modèle de durée.

## 11. Méthodes utiles du modèle

### `__str__()`

```python
def __str__(self):
    return self.name
```

Donne une représentation lisible de l'instance. La méthode doit toujours renvoyer une chaîne.

### `get_absolute_url()`

```python
from django.urls import reverse


def get_absolute_url(self):
    return reverse('room-detail', kwargs={'pk': self.pk})
```

- `reverse()` construit une URL depuis son nom plutôt que de l'écrire en dur.
- `kwargs` transmet la clé primaire attendue par la route.
- Cette méthode indique l'URL canonique d'une instance, utile après une création ou dans certaines vues génériques.

### `clean()`

```python
from django.core.exceptions import ValidationError


def clean(self):
    if self.ends_at <= self.starts_at:
        raise ValidationError({
            'ends_at': "La fin doit être postérieure au début.",
        })
```

- `clean()` convient à une règle Python impliquant plusieurs champs.
- La condition compare les deux valeurs.
- `ValidationError` rattache ici le message à `ends_at`.
- Cette validation ne remplace pas une contrainte de base lorsqu'une contrainte équivalente est nécessaire et possible.

### `save()`

```python
def save(self, *args, **kwargs):
    self.name = self.name.strip()
    super().save(*args, **kwargs)
```

- La méthode normalise ici le nom avant l'enregistrement.
- `*args` et `**kwargs` conservent les paramètres transmis par Django.
- `super().save(...)` est indispensable pour effectuer réellement l'enregistrement.

Une surcharge incorrecte peut provoquer une récursion, ignorer `update_fields`, casser les signaux attendus ou empêcher la sauvegarde. Ne surcharger `save()` que si le besoin est clair.

## 12. Managers et QuerySets

Django ajoute automatiquement :

```python
Model.objects
```

`objects` est le manager par défaut. Il donne accès notamment à :

```python
Model.objects.all()
Model.objects.filter(active=True)
Model.objects.get(pk=1)
```

- `all()` renvoie toutes les lignes sous forme de `QuerySet`.
- `filter()` renvoie zéro, une ou plusieurs lignes.
- `get()` exige exactement une ligne et lève une exception sinon.

Manager personnalisé :

```python
class CustomManager(models.Manager):
    def active(self):
        return self.filter(active=True)


class ModelName(models.Model):
    active = models.BooleanField(default=True)
    objects = CustomManager()
```

- `CustomManager` hérite de `models.Manager` et conserve les méthodes standards.
- `active(self)` est une méthode de manager : elle travaille sur une collection.
- `self.filter(...)` retourne un `QuerySet` chaînable.
- `objects = CustomManager()` remplace le manager nommé `objects`.

Une méthode d'instance, comme `model.get_absolute_url()`, agit sur un objet déjà obtenu. Une méthode de manager, comme `Model.objects.active()`, sert à rechercher des objets.

Si le manager est nommé `catalogue = CustomManager()`, l'appel devient `Model.catalogue.all()` et `Model.objects` n'existe plus, sauf si un autre manager `objects` est aussi déclaré.

## 13. Modification d’un modèle existant

Checklist avant la migration :

```text
[ ] Identifier le fichier du modèle
[ ] Ajouter ou retirer le champ
[ ] Vérifier les imports
[ ] Vérifier null et blank
[ ] Choisir on_delete
[ ] Définir related_name
[ ] Ajouter les contraintes
[ ] Vérifier les données existantes
[ ] Générer ensuite une migration
```

Risques principaux :

- **Champ obligatoire ajouté à une table remplie** : les anciennes lignes n'ont aucune valeur. Prévoir une valeur temporaire, un défaut pertinent ou une migration en plusieurs étapes.
- **Ancienne clé étrangère retirée** : les informations nécessaires à la conversion peuvent être perdues. Copier et vérifier les données avant la suppression.
- **Relation transformée** : passer de `Location` à `Room`, ou d'une FK à une M2M, change la structure et exige souvent une migration de données.
- **Ajout de `unique=True`** : la migration échoue si des doublons existent déjà.
- **Changement de type** : certaines valeurs existantes peuvent être impossibles à convertir ou être tronquées.

La procédure détaillée appartient à la fiche future **`04_MIGRATIONS.md`**. Ne pas improviser une migration destructive pendant l'examen.

## 14. Exemples complets prêts à adapter

Chaque exemple est indépendant : ne pas copier plusieurs classes portant le même nom dans une application.

### 14.1 Table simple avec nom unique

```python
class Tag(models.Model):
    name = models.CharField(max_length=30, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'tags'
```

Le nom est obligatoire et unique ; `__str__()` l'affiche lisiblement.

```text
À renommer :
- nom du modèle : Tag
- nom de la table : tags
- noms des champs : name
- related_name : aucun dans ce bloc
- nom des contraintes : aucune contrainte nommée
```

### 14.2 Enfant obligatoire d’un parent

```python
class Video(models.Model):
    title = models.CharField(max_length=255)
    video_url = models.URLField(max_length=255, unique=True)
    show = models.ForeignKey(
        'Show',
        on_delete=models.PROTECT,
        related_name='videos',
    )
```

`show` est obligatoire et porte la clé du côté plusieurs. `PROTECT` applique l'intention « empêcher la suppression » du sujet 2024-2. Django ne possède pas d'option `ON UPDATE CASCADE` de modèle équivalente au vocabulaire SQL du sujet ; les clés primaires sont normalement stables.

```text
À renommer :
- nom du modèle : Video
- nom de la table : ajouter Meta.db_table si nécessaire
- noms des champs : title, video_url, show
- related_name : videos
- nom des contraintes : unique est ici porté directement par video_url
```

### 14.3 Enfant facultatif

```python
class Artist(models.Model):
    troupe = models.ForeignKey(
        'Troupe',
        on_delete=models.SET_NULL,
        related_name='artists',
        null=True,
        blank=True,
    )
```

L'artiste peut être « Non affilié ». Supprimer une troupe conserve les artistes et met leur FK à `NULL`.

```text
À renommer :
- nom du modèle : Artist et modèle cible Troupe
- nom de la table : définir selon le projet
- noms des champs : troupe
- related_name : artists
- nom des contraintes : aucune
```

### 14.4 Many-to-many simple

```python
class Show(models.Model):
    tags = models.ManyToManyField(
        'Tag',
        related_name='shows',
        blank=True,
    )
```

Django crée le mapping automatique ; un spectacle et un tag peuvent chacun être associés plusieurs fois de l'autre côté, mais un même couple n'est pas dupliqué par la table automatique.

```text
À renommer :
- nom du modèle : Show et modèle cible Tag
- nom de la table : table intermédiaire automatique sauf through/db_table explicite
- noms des champs : tags
- related_name : shows
- nom des contraintes : gérées par la table automatique
```

### 14.5 Many-to-many avec modèle intermédiaire

```python
class ArtistLanguage(models.Model):
    artist = models.ForeignKey('Artist', on_delete=models.CASCADE)
    language = models.ForeignKey('Language', on_delete=models.PROTECT)
    level = models.CharField(max_length=20)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['artist', 'language'],
                name='unique_artist_language',
            ),
        ]


class Artist(models.Model):
    languages = models.ManyToManyField(
        'Language',
        through='ArtistLanguage',
        related_name='artists',
    )
```

`ArtistLanguage` stocke `level`; `through` l'utilise comme mapping ; la contrainte interdit le couple en double.

```text
À renommer :
- nom du modèle : ArtistLanguage, Artist, Language
- nom de la table : ajouter db_table si imposé
- noms des champs : artist, language, level, languages
- related_name : artists et, idéalement, ceux des ForeignKey
- nom des contraintes : unique_artist_language
```

### 14.6 Date et heure

```python
class Representation(models.Model):
    schedule = models.DateTimeField(db_index=True)
```

`DateTimeField` conserve le jour et l'heure ; l'index peut accélérer les recherches chronologiques.

```text
À renommer :
- nom du modèle : Representation
- nom de la table : définir selon le projet
- noms des champs : schedule
- related_name : aucun
- nom des contraintes : aucune
```

### 14.7 Prix avec `DecimalField`

```python
class Price(models.Model):
    amount = models.DecimalField(max_digits=8, decimal_places=2)
```

`max_digits=8` autorise huit chiffres au total ; `decimal_places=2` en réserve deux après la virgule.

```text
À renommer :
- nom du modèle : Price
- nom de la table : définir selon le projet
- noms des champs : amount
- related_name : aucun
- nom des contraintes : éventuellement une contrainte de positivité
```

### 14.8 Champ avec `choices`

```python
class Membership(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Actif'
        INACTIVE = 'inactive', 'Inactif'

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
```

La première valeur est stockée, la seconde est affichée et `default` reçoit une valeur de l'énumération.

```text
À renommer :
- nom du modèle : Membership et énumération Status
- nom de la table : définir selon le projet
- noms des champs : status
- related_name : aucun
- nom des contraintes : aucune contrainte de base explicite
```

### 14.9 Modèle avec contrainte composée

```python
class Representation(models.Model):
    room = models.ForeignKey(
        'Room',
        on_delete=models.PROTECT,
        related_name='representations',
    )
    schedule = models.DateTimeField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['room', 'schedule'],
                name='unique_room_schedule',
            ),
        ]
```

La base interdit deux représentations dans la même salle au même instant exact.

```text
À renommer :
- nom du modèle : Representation et cible Room
- nom de la table : définir selon le projet
- noms des champs : room, schedule
- related_name : representations
- nom des contraintes : unique_room_schedule
```

### 14.10 Modèle avec nombre strictement positif

```python
from django.core.validators import MinValueValidator
from django.db import models


class Room(models.Model):
    seats = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)],
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(seats__gt=0),
                name='room_seats_gt_zero',
            ),
        ]
```

Le validateur améliore les messages de formulaire ; la contrainte protège directement la base.

```text
À renommer :
- nom du modèle : Room
- nom de la table : définir selon le projet
- noms des champs : seats
- related_name : aucun
- nom des contraintes : room_seats_gt_zero
```

## 15. Erreurs fréquentes

- **Oublier d'importer le modèle** dans `catalogue/models/__init__.py` : Django peut ne pas le découvrir.
- **Faute dans l'héritage** : écrire exactement `models.Model`, avec les majuscules.
- **Confondre classe et instance** : `Room.objects.all()` agit via la classe ; `room.name` agit sur une instance.
- **Écrire `models.model`** : incorrect, car la classe se nomme `Model`.
- **Mettre des guillemets autour de booléens** : `blank=True`, jamais `blank='True'`.
- **Oublier `max_length` sur `CharField`** : ce paramètre est requis.
- **Utiliser un entier ou un flottant pour un prix** : préférer `DecimalField` avec précision explicite.
- **Oublier `on_delete`** sur une FK : Django l'exige.
- **Réutiliser un `related_name` incompatible** : `manage.py check` signale les accès inverses en conflit.
- **Choisir `CASCADE` automatiquement** : vérifier si la suppression des enfants est vraiment acceptable.
- **Oublier l'unicité d'un couple** : ajouter une `UniqueConstraint` à l'association.
- **Croire qu'un validateur protège toute écriture SQL** : un validateur Python peut être contourné ; ajouter une contrainte de base si nécessaire.
- **Ajouter une relation obligatoire sans traiter les anciennes lignes** : procéder par étapes et migrer les données.
- **Confondre `null` et `blank`** : le premier vise surtout le stockage, le second la validation.
- **Utiliser `null=True` sur une M2M** : l'absence est déjà représentée par zéro association.
- **Copier un nom de contrainte** : chaque nom de contrainte doit rester unique.

## 16. Commandes de vérification

Depuis le dossier contenant `manage.py`, sous PowerShell :

```powershell
.venv\Scripts\python.exe manage.py check
.venv\Scripts\python.exe manage.py makemigrations --check
```

- La première commande utilise explicitement le Python du nouvel environnement et vérifie la configuration, les modèles, les relations et plusieurs incohérences Django.
- La seconde détecte si les modèles diffèrent des migrations enregistrées. Sans option `--dry-run`, Django 5.2 ne crée pas de fichier si aucun changement n'est requis ; avec `--check`, la commande retourne un statut d'échec lorsque des migrations manquent.

`makemigrations --check` est une **vérification finale** seulement lorsque les migrations attendues ont déjà été créées. Juste après une modification volontaire de modèle, il est normal qu'elle signale d'abord une migration manquante. La prochaine étape est alors la création et l'inspection de la migration, décrites dans `04_MIGRATIONS.md`.

Dans cette fiche, aucune migration n'est exécutée.

## 17. Checklist express

```text
[ ] Classe héritant de models.Model
[ ] Types de champs corrects
[ ] max_length cohérents
[ ] null et blank réfléchis
[ ] relations placées du bon côté
[ ] on_delete choisi consciemment
[ ] related_name unique et clair
[ ] validateurs nécessaires
[ ] contraintes de base nécessaires
[ ] __str__ défini
[ ] modèle importé
[ ] prochaine étape : migration
```

### Repères propres au projet Réservations

- Les modèles actuels sont répartis dans `catalogue/models/` et exposés par `catalogue/models/__init__.py`.
- `Show.category` illustre déjà une FK vers `Category` avec `PROTECT` et `related_name='shows'`.
- `ArtistTypeShow` et `RepresentationReservation` illustrent déjà des modèles intermédiaires avec contrainte d'unicité composée.
- `UserMeta.user` illustre un `OneToOneField`, mais sans `related_name` explicite.
- Les futurs modèles `Room`, `Video`, `Troupe`, `Tag`, `Language` et `ArtistLanguage` montrés ici sont des exemples adaptés aux sujets : ils ne sont pas actuellement tous présents dans l'application.

### Incohérences ou décisions à surveiller dans l'état actuel

- `Location.locality` et `Representation.location` autorisent `NULL` en base mais n'indiquent pas `blank=True` : la relation peut donc rester facultative en base tout en étant requise dans un `ModelForm` automatique.
- Une ancienne migration de catégorie contient `blank='True'` sous forme de chaîne ; une migration suivante le corrige en booléen. Le modèle actuel utilise bien `blank=True`.
- Certains `related_name` historiques (`a_artistTypes`, `t_artistTypes`, `artistTypeShows`) sont valides mais ne suivent pas une convention uniforme en `snake_case`.
- `UserMeta.user` ne définit pas de `related_name`; l'accès inverse utilise donc le nom généré par Django.
- Le modèle actuel `Representation` pointe directement vers `Location` : les modèles `Room` et la contrainte `room + schedule` des variantes d'examen ne sont pas encore implémentés.
- Le sujet troupe combine « un artiste appartient à une seule troupe » avec l'option « Non affilié » : il faut clarifier si la FK doit être obligatoire (`1..1`) ou facultative (`0..1`).
