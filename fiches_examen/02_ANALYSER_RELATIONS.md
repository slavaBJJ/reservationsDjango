# 02 — Analyser les relations métier avec Django

> Objectif : transformer une phrase métier en modèles et relations Django sans résoudre un sujet précis.
> Dans les anciens sujets : **entité** = modèle Django ; **mapping** = relation entre modèles ; **contrôleur** = généralement une vue Django.

## 1. Méthode pour analyser une phrase métier

Pour chaque phrase, appliquer toujours les huit étapes suivantes.

1. **Repérer les deux entités** : les noms métier deviennent généralement des modèles au singulier (`Location`, `Room`).
2. **Lire la phrase dans les deux directions** : « un lieu possède des salles » puis « une salle appartient à un lieu ».
3. **Déterminer les cardinalités minimale et maximale** de chaque côté : `0..1`, `1..1`, `0..N` ou `1..N`.
4. **Choisir la relation Django** : `ForeignKey`, `ManyToManyField` ou `OneToOneField`.
5. **Déterminer où placer le champ** : pour une relation one-to-many, la `ForeignKey` se place sur le modèle du côté « plusieurs ».
6. **Choisir si la relation est obligatoire ou facultative** en distinguant la base (`null`) et les formulaires (`blank`).
7. **Choisir le comportement de suppression** avec `on_delete` selon la règle métier.
8. **Chercher les contraintes supplémentaires** : unicité, valeur positive, couple unique, absence de double réservation, etc.

Formulations à reconnaître :

```text
un seul             → maximum 1
plusieurs           → maximum N
zéro ou plusieurs   → minimum 0, maximum N
éventuellement      → minimum 0 : relation facultative
au moins un         → minimum 1
appartient à        → indique souvent le côté qui porte la ForeignKey
possède             → lire aussi la relation dans l'autre direction
peut être associé à → relation souvent facultative ; vérifier le maximum
```

Attention : « plusieurs » ne précise pas toujours si zéro est autorisé. Le cahier des charges, les données et les formulaires doivent permettre de fixer la cardinalité minimale.

## 2. Lire les cardinalités

| Cardinalité | Signification | Traduction Django approximative |
|---|---|---|
| `0..1` | aucun ou un objet | FK/OneToOne facultative : `null=True, blank=True` |
| `1..1` | exactement un objet | FK/OneToOne obligatoire : valeurs par défaut `null=False, blank=False` |
| `0..N` | aucun, un ou plusieurs | collection inverse ou M2M avec `blank=True` |
| `1..N` | au moins un | relation multiple ; minimum souvent contrôlé par validation métier |

- La **cardinalité minimale** répond à « la relation peut-elle être absente ? ».
- La **cardinalité maximale** répond à « combien d'objets au maximum ? ».
- Une relation est **facultative** si son minimum vaut `0`.
- Une relation est **obligatoire** si son minimum vaut `1`.

```python
null=True
blank=True
null=False
blank=False
```

- `null=True` autorise principalement la valeur SQL `NULL` en base.
- `blank=True` autorise principalement une valeur vide pendant la validation des formulaires et du modèle.
- `null=False` et `blank=False` sont les valeurs par défaut de nombreux champs : base et formulaire exigent une valeur.
- Pour une `ForeignKey` facultative, utiliser généralement `null=True, blank=True`.
- Pour une collection, Django ne garantit pas automatiquement « au moins un » au niveau de la colonne : une validation ou une logique métier supplémentaire peut être nécessaire.

## 3. Relation one-to-many avec `ForeignKey`

```python
from django.db import models


class Parent(models.Model):
    name = models.CharField(max_length=60)


class Child(models.Model):
    parent = models.ForeignKey(
        Parent,
        on_delete=models.PROTECT,
        related_name='children',
    )
```

- La première ligne importe les classes de modèles et de champs.
- `Parent` et `Child` héritent de `models.Model` : ce sont les deux entités.
- `name` est un texte court limité à 60 caractères.
- `parent` est placé sur `Child`, le côté « plusieurs » : plusieurs enfants stockent chacun l'identifiant d'un parent.
- `Parent` désigne le modèle référencé.
- `PROTECT` interdit la suppression d'un parent encore utilisé.
- `related_name='children'` nomme l'accès inverse depuis le parent.
- L'absence de `null=True` rend la relation obligatoire en base.

Accès ORM :

```python
child.parent
parent.children.all()
```

- `child.parent` suit la clé étrangère vers l'unique parent.
- `parent.children.all()` suit l'accès inverse vers tous les enfants.

Exemples d'extension du projet Réservations :

- **`Show → Video`** : placer `show = ForeignKey(...)` sur `Video`, car les vidéos sont le côté plusieurs ; accès inverse proposé : `show.videos.all()`.
- **`Location → Room`** : placer `location = ForeignKey(...)` sur `Room` ; accès inverse : `location.rooms.all()`.
- **`Room → Representation`** : placer `room = ForeignKey(...)` sur `Representation` ; accès inverse : `room.representations.all()`.

Ces trois modèles d'extension ne sont pas tous présents actuellement : le projet possède déjà `Show`, `Location` et `Representation`, mais pas encore `Video` ni `Room`.

## 4. Relation facultative

Dans le modèle `Artist`, une affiliation facultative peut s'écrire :

```python
troupe = models.ForeignKey(
    'Troupe',
    on_delete=models.SET_NULL,
    related_name='artists',
    null=True,
    blank=True,
)
```

- Le champ se place sur `Artist`, côté plusieurs : une troupe regroupe plusieurs artistes.
- `'Troupe'` est une référence différée au modèle cible.
- `SET_NULL` conserve l'artiste si sa troupe est supprimée.
- `related_name='artists'` permet `troupe.artists.all()`.
- `null=True` est nécessaire pour stocker l'absence de troupe dans une FK.
- `blank=True` autorise l'absence dans un formulaire.

Une FK absente vaut `None` en Python et `NULL` en base. Ce n'est pas une chaîne vide `''`, qui est une valeur textuelle et non une relation.

`SET_NULL` exige `null=True`, sinon Django ne pourrait pas effacer la référence. Dans un template :

```django
{{ artist.troupe.name|default:"Non affilié" }}
```

Ce filtre affiche un remplacement si aucune troupe n'est liée. Une condition `{% if artist.troupe %}` est préférable si plusieurs éléments, comme le nom et le logo, dépendent de la troupe.

Comparaison :

| Choix | Effet lors de la suppression de la troupe | Usage plausible |
|---|---|---|
| `SET_NULL` | désaffilie les artistes | « Non affilié » doit rester possible |
| `PROTECT` | interdit la suppression tant que des artistes existent | l'affiliation doit être préservée explicitement |

## 5. Relation many-to-many simple

```python
class Tag(models.Model):
    name = models.CharField(max_length=30, unique=True)


class Show(models.Model):
    tags = models.ManyToManyField(
        Tag,
        related_name='shows',
        blank=True,
    )
```

- `Tag` représente l'entité mot-clé.
- `unique=True` empêche deux tags portant exactement le même nom.
- `tags` se place ici sur `Show`, car « les tags d'un spectacle » est une lecture naturelle du domaine.
- Une M2M pourrait techniquement être déclarée sur l'un ou l'autre modèle ; il ne faut la déclarer qu'une fois.
- Django crée automatiquement une table intermédiaire contenant les deux clés étrangères.
- `related_name='shows'` permet l'accès inverse depuis un tag.
- `blank=True` autorise un spectacle sans tag dans la validation.
- `null=True` est inutile sur une M2M : l'absence correspond à zéro ligne d'association, pas à une colonne `NULL`.

Opérations ORM :

```python
show.tags.all()
tag.shows.all()
show.tags.add(tag)
show.tags.remove(tag)
show.tags.set([tag1, tag2])
show.tags.clear()
```

- `all()` lit la collection dans chaque direction.
- `add()` crée une association ; `remove()` en retire une.
- `set()` remplace la collection par la liste fournie.
- `clear()` retire toutes les associations de ce spectacle.

L'objet `show` doit déjà être sauvegardé et posséder une clé primaire avant l'utilisation de sa relation many-to-many.

## 6. Many-to-many avec modèle intermédiaire

Lorsque la relation possède une donnée propre, le mapping devient une entité explicite :

```python
class ArtistLanguage(models.Model):
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
    level = models.CharField(max_length=20)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['artist', 'language'],
                name='unique_artist_language',
            ),
        ]
```

- `ArtistLanguage` matérialise l'association artiste-langue.
- Les deux `ForeignKey` pointent vers les entités liées.
- `level` appartient à la relation : un artiste possède un niveau pour une langue donnée.
- `CASCADE` supprime les associations d'un artiste supprimé ; le choix doit rester métier.
- `PROTECT` interdit ici la suppression d'une langue encore utilisée.
- La contrainte composée interdit deux fois le même couple artiste-langue.
- Le nom de contrainte doit être explicite et unique dans le projet.

Dans le modèle `Artist`, déclarer la collection :

```python
languages = models.ManyToManyField(
    'Language',
    through='ArtistLanguage',
    related_name='artists',
)
```

- `through` demande à Django d'utiliser `ArtistLanguage` au lieu d'une table automatique.
- `artist.languages.all()` renvoie les langues.
- `artist.artist_languages.all()` renvoie les objets d'association ; chaque objet expose `.level`.

Exemple d'accès au niveau :

```python
for association in artist.artist_languages.select_related('language'):
    print(association.language, association.level)
```

Une opération comme `show.tags.add(tag)` suffit pour une M2M simple. Avec un modèle intermédiaire possédant un champ obligatoire comme `level`, il faut aussi fournir cette donnée, généralement en créant explicitement `ArtistLanguage`.

## 7. Relation one-to-one

```python
class Profile(models.Model):
    user = models.OneToOneField(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='profile',
    )
```

- `Profile` porte le champ : le profil dépend ici de l'utilisateur.
- `OneToOneField` autorise au maximum un profil par utilisateur et un utilisateur par profil.
- `CASCADE` supprime le profil lorsque l'utilisateur est supprimé.
- `related_name='profile'` permet `user.profile`.

`ForeignKey(unique=True)` impose une unicité proche en base, mais `OneToOneField` exprime mieux l'intention et fournit un accès inverse à un objet unique plutôt qu'un manager de collection.

Cas pertinent : métadonnées ou profil étendant un utilisateur. Le projet possède actuellement `UserMeta.user` en `OneToOneField`.

`OneToOneField` ne convient pas si un utilisateur peut avoir plusieurs profils, si une salle accueille plusieurs représentations ou si plusieurs spectacles partagent plusieurs tags.

## 8. Choisir `on_delete`

`on_delete` décrit ce qui arrive à **l'objet qui porte la clé étrangère** lorsque **l'objet référencé** est supprimé. Cela ne décrit pas la suppression dans l'autre direction.

| Choix | Comportement | Condition / exemple | Risque |
|---|---|---|---|
| `CASCADE` | supprime aussi les objets porteurs de la FK | supprimer un spectacle pourrait supprimer ses objets strictement dépendants | perte en cascade trop large |
| `PROTECT` | lève `ProtectedError` si une référence existe | empêcher de supprimer une salle utilisée | blocage nécessitant une désassociation préalable |
| `RESTRICT` | lève `RestrictedError`, avec prise en compte du graphe de suppression Django | utilisé actuellement sur plusieurs relations du projet | subtilité lors de cascades simultanées |
| `SET_NULL` | remplace la FK par `NULL` | exige `null=True`; désaffilier un artiste | information d'origine perdue |
| `SET_DEFAULT` | remplace la FK par sa valeur par défaut | exige un `default` valide, par exemple une catégorie de repli | objet par défaut absent ou sémantique trompeuse |
| `DO_NOTHING` | Django ne fait rien | seulement si la base ou une autre stratégie assure l'intégrité | erreur d'intégrité ou référence invalide |

Questions à se poser :

- **Supprimer un spectacle doit-il supprimer ses vidéos ?** L'ancien sujet vidéo demande d'empêcher la suppression : `PROTECT` sur `Video.show` est plausible. `CASCADE` serait un autre choix métier, mais pas celui formulé.
- **Supprimer une salle utilisée doit-il être interdit ?** Souvent oui : `PROTECT` sur `Representation.room`.
- **Supprimer une troupe doit-il désaffilier les artistes ?** Si « Non affilié » est autorisé : `SET_NULL` avec FK nullable ; sinon `PROTECT`.
- **Supprimer une langue utilisée doit-il être interdit ?** `PROTECT` préserve les associations ; `CASCADE` supprimerait les niveaux associés.

## 9. Contraintes métier et contraintes de base

Trois niveaux différents :

- **Validation de formulaire** : messages adaptés à l'interface, mais seulement pour les écritures passant par ce formulaire.
- **Validation de modèle** : validateurs et `clean()`, exécutés notamment par les `ModelForm` ou `full_clean()` ; `save()` seul ne l'appelle pas systématiquement.
- **Contrainte de base** : protection centrale, y compris contre les écritures venant du shell, de l'administration, de l'API ou d'un autre processus.

### Champ unique

```python
name = models.CharField(max_length=60, unique=True)
```

`unique=True` convient à un seul champ, par exemple un nom de salle déclaré globalement unique. Vérifier toutefois si le métier veut plutôt un nom unique seulement à l'intérieur d'un lieu.

### Nombre de sièges supérieur à zéro — Django 5.2

```python
class Meta:
    constraints = [
        models.CheckConstraint(
            condition=models.Q(seats__gt=0),
            name='room_seats_gt_zero',
        ),
    ]
```

- `CheckConstraint` impose une condition en base.
- Django 5.2 utilise la syntaxe moderne `condition=`.
- `models.Q(seats__gt=0)` signifie `seats > 0`.
- La contrainte doit porter un nom explicite et unique.

### Même salle interdite au même horaire

```python
models.UniqueConstraint(
    fields=['room', 'schedule'],
    name='unique_room_schedule',
)
```

La combinaison est unique : la salle ou l'horaire peuvent se répéter séparément, mais pas ensemble. Cette règle traite l'égalité exacte des horaires, pas nécessairement le chevauchement de créneaux avec durée.

### Même artiste-langue interdit deux fois

```python
models.UniqueConstraint(
    fields=['artist', 'language'],
    name='unique_artist_language',
)
```

Une validation uniquement dans le formulaire ne suffit pas : un endpoint API, le shell ou du code d'administration peut employer un autre chemin d'écriture. La contrainte de base reste la dernière protection contre les doublons concurrents.

## 10. Relations inverses et requêtes ORM

Avec les `related_name` proposés :

```python
location.rooms.all()
room.representations.all()
show.videos.all()
tag.shows.all()
artist.artist_languages.all()
```

- Chaque appel part de l'objet « parent » ou propriétaire naturel vers une collection liée.
- Le dernier renvoie les associations et permet de lire `level`, pas uniquement les langues.
- Ces accès `rooms`, `videos` et `artist_languages` supposent les modèles d'extension décrits ; ils ne sont pas tous présents actuellement.

Sans `related_name`, Django génère généralement `<nom_du_modèle>_set`, par exemple `show.video_set.all()`. Sur une `OneToOneField`, l'accès inverse généré correspond généralement au nom du modèle en minuscules. Un nom explicite facilite la lecture et évite certains conflits.

Optimisation :

```python
Representation.objects.select_related('room', 'room__location')
Category.objects.prefetch_related('shows')
```

- `select_related()` effectue des jointures pour les relations vers **un seul objet**, comme une FK ou une one-to-one.
- `'room__location'` suit deux FK successives.
- `prefetch_related()` charge séparément les **collections**, accès inverses et M2M, puis les associe en Python.
- `Category.objects.prefetch_related('shows')` correspond au `related_name='shows'` réel de `Show.category`.

## 11. Modifier une relation existante

Situation :

```text
Representation possède actuellement location
Representation doit maintenant posséder room
Room possède location
```

Dans le projet actuel, `Representation` possède effectivement une FK directe vers `Location`. Supprimer immédiatement cette colonne ferait perdre l'information utile. Ajouter simultanément une FK `room` obligatoire échouerait ou demanderait une valeur arbitraire pour chaque représentation existante.

Ordre conceptuel sûr :

```text
1. Créer le nouveau modèle
2. Ajouter la nouvelle relation temporairement nullable
3. Créer les données nécessaires
4. Convertir les anciennes relations
5. Vérifier les données
6. Supprimer l’ancienne relation
7. Rendre la nouvelle relation obligatoire
```

Chaque étape structurelle doit être représentée par une migration adaptée. La conversion des données doit être vérifiable et réversible autant que possible. Voir la future fiche `04_MIGRATIONS.md` pour la procédure détaillée.

## 12. Arbre de décision

```text
Chaque A possède plusieurs B,
chaque B possède un seul A
→ ForeignKey sur B

Plusieurs A possèdent plusieurs B
→ ManyToManyField

Plusieurs A possèdent plusieurs B
et la relation contient des informations
→ modèle intermédiaire + through

Un seul A correspond à un seul B
→ OneToOneField

La relation peut être absente
→ null=True et blank=True pour une ForeignKey
```

Nuances : « au moins un » demande souvent une validation supplémentaire ; `on_delete` dépend toujours de la règle métier ; une contrainte d'unicité peut compléter la relation.

## 13. Pièges fréquents

- Placer la `ForeignKey` du mauvais côté : elle va normalement sur le modèle du côté « plusieurs ».
- Confondre `null` et `blank` : stockage en base contre validation Django.
- Écrire `blank='True'` au lieu de `blank=True` : la première valeur est une chaîne.
- Mettre `null=True` sur un `ManyToManyField` : zéro association représente déjà l'absence.
- Oublier `related_name` : Django génère un nom, mais il peut être moins clair ou entrer en conflit.
- Utiliser `CASCADE` sans réfléchir : une suppression peut emporter beaucoup de données.
- Ajouter une FK obligatoire à une table remplie : les anciennes lignes n'ont aucune valeur.
- Oublier l'unicité d'un couple dans un modèle intermédiaire.
- Protéger seulement le formulaire : le shell, l'administration ou l'API peuvent suivre un autre chemin.
- Confondre modèle intermédiaire automatique et explicite : un champ comme `level` exige un modèle explicite avec `through`.
- Supposer que « plusieurs » veut toujours dire `1..N` : le minimum peut être zéro.
- Croire que `UniqueConstraint(room, schedule)` détecte tous les chevauchements de plages horaires.

## 14. Exercices d’identification

Lire la phrase, répondre mentalement, puis ouvrir la solution.

### Exercice 1 — Lieu et salle

> Un lieu possède zéro ou plusieurs salles ; une salle appartient à un seul lieu.

<details>
<summary>Voir la réponse</summary>

- Cardinalités : `Location 0..N Room` ; chaque `Room` a `1..1 Location`.
- Relation : one-to-many avec `ForeignKey`.
- Champ : `location` sur `Room`, côté plusieurs.
- Obligation : FK obligatoire (`null=False, blank=False`).
- `on_delete` plausible : `PROTECT` si un lieu utilisé ne peut pas être supprimé.
- Contrainte éventuelle : nom de salle unique par lieu avec `UniqueConstraint(['location', 'name'], ...)`.

</details>

### Exercice 2 — Salle et représentation

> Une salle accueille plusieurs représentations ; chaque représentation se déroule dans une salle.

<details>
<summary>Voir la réponse</summary>

- Cardinalités : salle `0..N` représentations ; représentation `1..1` salle, sauf précision contraire.
- Relation : `ForeignKey`.
- Champ : `room` sur `Representation`.
- Obligation : obligatoire.
- `on_delete` plausible : `PROTECT`.
- Contrainte éventuelle : couple `room + schedule` unique.

</details>

### Exercice 3 — Occupation d’une salle

> Une salle ne peut pas accueillir deux représentations au même moment.

<details>
<summary>Voir la réponse</summary>

- Ce n'est pas une nouvelle relation, mais une règle sur `Representation`.
- Relation préalable : FK `room` portée par `Representation`.
- Contrainte : `UniqueConstraint(fields=['room', 'schedule'], ...)` pour des instants exactement égaux.
- Obligation : `room` et `schedule` doivent être renseignés si la règle vaut sans exception.
- Nuance : des intervalles qui se chevauchent exigent une règle plus riche.

</details>

### Exercice 4 — Spectacle et vidéo

> Un spectacle possède zéro ou plusieurs vidéos ; une vidéo référence un seul spectacle.

<details>
<summary>Voir la réponse</summary>

- Cardinalités : `Show 0..N Video` ; `Video 1..1 Show`.
- Relation : `ForeignKey`.
- Champ : `show` sur `Video`.
- Obligation : la FK est obligatoire.
- `on_delete` plausible : `PROTECT`, conformément à l'ancien sujet qui demande d'empêcher la suppression.
- Contrainte éventuelle : `video_url` unique si le sujet l'impose.

</details>

### Exercice 5 — Catégorie et spectacle

> Une catégorie contient plusieurs spectacles ; un spectacle appartient à une catégorie.

<details>
<summary>Voir la réponse</summary>

- Cardinalités maximales : catégorie vers spectacles `N`, spectacle vers catégorie `1`.
- Minimum : à confirmer ; « appartient à » peut suggérer une FK obligatoire.
- Relation : `ForeignKey`.
- Champ : `category` sur `Show`, côté plusieurs.
- `on_delete` plausible : `PROTECT` pour empêcher la suppression d'une catégorie utilisée.
- État réel : le projet autorise actuellement `Show.category` à être nul et vide, donc `0..1` côté spectacle.

</details>

### Exercice 6 — Troupe et artiste facultatif

> Une troupe regroupe plusieurs artistes ; un artiste appartient éventuellement à une troupe.

<details>
<summary>Voir la réponse</summary>

- Cardinalités : troupe `0..N` artistes ; artiste `0..1` troupe.
- Relation : `ForeignKey`.
- Champ : `troupe` sur `Artist`.
- Obligation : facultative avec `null=True, blank=True`.
- `on_delete` plausible : `SET_NULL` pour obtenir « Non affilié ».
- Contrainte éventuelle : nom de troupe unique si demandé.

</details>

### Exercice 7 — Spectacle et tag

> Un spectacle possède plusieurs tags ; un tag peut appartenir à plusieurs spectacles.

<details>
<summary>Voir la réponse</summary>

- Cardinalités : généralement `0..N` des deux côtés si « zéro » est permis.
- Relation : `ManyToManyField` simple.
- Champ : naturellement `tags` sur `Show`; il pourrait être placé sur l'autre modèle, mais une seule déclaration suffit.
- Obligation : `blank=True` si un spectacle sans tag est autorisé ; pas de `null=True`.
- `on_delete` : non déclaré sur `ManyToManyField`; la table automatique gère ses FK.
- Contrainte éventuelle : `Tag.name` unique.

</details>

### Exercice 8 — Artiste, langue et niveau

> Un artiste parle plusieurs langues ; une langue est parlée par plusieurs artistes ; le niveau doit être enregistré.

<details>
<summary>Voir la réponse</summary>

- Cardinalités : many-to-many entre `Artist` et `Language`.
- Relation : modèle intermédiaire explicite `ArtistLanguage` et `through`.
- Champs : `artist`, `language` et `level` sur `ArtistLanguage`; collection `languages` naturellement sur `Artist`.
- Obligation : les deux FK et `level` sont normalement obligatoires.
- `on_delete` plausible : `CASCADE` pour l'artiste, `PROTECT` pour la langue ; à confirmer métier.
- Contrainte : couple `artist + language` unique.

</details>

### Exercice 9 — Utilisateur et profil

> Un utilisateur possède au maximum un profil et un profil correspond à un seul utilisateur.

<details>
<summary>Voir la réponse</summary>

- Cardinalités : utilisateur `0..1` profil ; profil `1..1` utilisateur.
- Relation : `OneToOneField`.
- Champ : `user` sur `Profile`, car le profil dépend de l'utilisateur.
- Obligation : obligatoire côté profil ; l'utilisateur peut exister sans profil.
- `on_delete` plausible : `CASCADE`.
- Contrainte : l'unicité est fournie par `OneToOneField`.

</details>

### Exercice 10 — Lieu facultatif d’une représentation

> Une représentation peut être associée directement à un lieu.

<details>
<summary>Voir la réponse</summary>

- Cardinalités : représentation `0..1` lieu ; lieu `0..N` représentations.
- Relation : `ForeignKey` facultative.
- Champ : `location` sur `Representation`.
- Obligation : `null=True, blank=True` si l'absence doit être permise en base et formulaire.
- `on_delete` plausible : `SET_NULL` si la représentation doit survivre, ou `PROTECT` si le lieu doit être conservé.
- État réel : le projet possède cette FK avec `RESTRICT` et `null=True`, mais sans `blank=True`.

</details>

### Exercice 11 — Spectacle et artiste avec rôle

> Un spectacle réunit plusieurs artistes et leur type de participation dépend du spectacle.

<details>
<summary>Voir la réponse</summary>

- Cardinalités : plusieurs spectacles et plusieurs artistes.
- Relation : modèle intermédiaire si le rôle/type appartient au lien.
- Champ : les FK vers le spectacle et l'artiste/type sont portées par le modèle d'association.
- Obligation : associations et rôle normalement obligatoires.
- `on_delete` plausible : dépend de la conservation attendue ; le projet utilise `ArtistTypeShow` avec `CASCADE`.
- Contrainte : unicité du couple représentant une participation.

</details>

### Exercice 12 — Plusieurs salles au même nom selon le lieu

> Deux lieux différents peuvent avoir une salle « Principale », mais un lieu ne peut pas avoir deux salles de même nom.

<details>
<summary>Voir la réponse</summary>

- Relation : `Room.location` reste une `ForeignKey` obligatoire.
- Champ : `location` sur `Room`.
- `on_delete` plausible : `PROTECT`.
- Contrainte : `UniqueConstraint(fields=['location', 'name'], ...)` sur `Room`.
- Ne pas utiliser `unique=True` sur `Room.name`, car cela interdirait le même nom dans deux lieux différents.

</details>

## 15. Checklist d’examen

```text
[ ] J’ai identifié les deux modèles
[ ] J’ai lu la relation dans les deux directions
[ ] J’ai déterminé les cardinalités
[ ] J’ai choisi ForeignKey, ManyToManyField ou OneToOneField
[ ] J’ai placé le champ du bon côté
[ ] J’ai choisi null et blank
[ ] J’ai choisi on_delete
[ ] J’ai défini related_name
[ ] J’ai identifié les contraintes uniques
[ ] J’ai vérifié l’impact sur les données existantes
```

### Repères et incohérences actuelles du projet

- `Show.category` est une vraie `ForeignKey` vers `Category`, avec `PROTECT` et `related_name='shows'`, mais elle est facultative (`null=True, blank=True`) alors que certaines formulations métier peuvent suggérer une catégorie obligatoire.
- `Representation.location` et `Location.locality` autorisent `NULL` en base sans `blank=True`; un `ModelForm` automatique peut donc les traiter comme obligatoires.
- `Representation` pointe encore directement vers `Location`; `Room`, `Representation.room` et la contrainte `room + schedule` ne sont pas implémentés.
- `Video`, `Troupe`, `Tag`, `Language` et `ArtistLanguage` sont des variantes d'examen, pas des modèles actuels du projet.
- Certains `related_name` historiques (`a_artistTypes`, `t_artistTypes`, `artistTypeShows`) sont valides, mais leur style n'est pas uniforme.
- `UserMeta.user` ne possède pas de `related_name` explicite ; Django utilise donc son accès inverse généré.
- Une ancienne migration de catégorie contient `blank='True'`; la migration suivante et le modèle courant emploient correctement le booléen `blank=True`.
