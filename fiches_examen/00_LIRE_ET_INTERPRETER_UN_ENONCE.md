# 00 — Lire et interpréter un énoncé Django

> Objectif : transformer un cahier des charges inconnu en tâches Django vérifiables **avant de coder**.
> Projet de référence : Réservations, sous Django **5.2.8**.

## 1. Comprendre le rôle du cahier des charges

Un énoncé décrit principalement :

```text
ce que l’application doit permettre
```

Il ne donne pas toujours :

```text
les fichiers exacts et les lignes de code à écrire
```

Je traduis donc le besoin par étapes :

```text
Besoin exprimé
→ données concernées
→ relations
→ règle métier
→ page ou action
→ composants Django
→ vérifications
```

Je distingue dès le départ :

- **besoin fonctionnel** : résultat visible attendu, par exemple consulter des vidéos ;
- **règle métier** : condition propre au domaine, par exemple une salle indisponible au même horaire ;
- **exigence technique** : moyen imposé, par exemple une route paramétrée ou une liste déroulante ;
- **choix du développeur** : nom interne d'une fonction, organisation d'un template, message précis ;
- **erreur probable de copier-coller** : description incompatible avec le titre de la table et le reste du sujet.

## 2. Comprendre les préfixes F1, F2 et A1

Les anciens documents ne définissent pas officiellement les lettres. Leur usage observable est cependant régulier :

- `F1`, `F2`, etc. désignent généralement des fonctionnalités de consultation ou d'utilisation ;
- `A1`, `A2`, etc. désignent généralement des actions administratives.

Je conserve cette hypothèse comme aide de lecture, pas comme définition universelle.

| Formulation | Ce qu’il faut rechercher |
|---|---|
| Un utilisateur consulte… | Vue de lecture, requête ORM, template |
| Un utilisateur recherche… | Formulaire GET, filtres ORM, résultats |
| Un administrateur ajoute… | Formulaire POST, création ou association, permission |
| Un administrateur modifie… | Formulaire avec `instance`, mise à jour, permission |
| Un administrateur supprime… | Requête POST, confirmation, règle `on_delete` |

Une même fonctionnalité peut demander plusieurs composants : afficher un formulaire seulement à l'administrateur ne dispense jamais de protéger sa vue backend.

## 3. Repérer les noms et les verbes

Je surligne mentalement :

- les **noms** : modèles ou données (`Representation`, `Show`, `Room`) ;
- les **verbes** : opérations (`afficher`, `ajouter`, `associer`) ;
- les **quantités** : cardinalités (`un seul`, `plusieurs`) ;
- les **conditions** : validations (`si la salle est libre`) ;
- les **rôles** : autorisations (`administrateur connecté`).

Exemple :

```text
Un administrateur ajoute une représentation
pour un spectacle dans une salle.
```

Analyse :

```text
Rôle : administrateur
Action : ajouter
Objet créé : représentation
Relations nécessaires : spectacle et salle
Traitement HTTP probable : POST
Formulaire : spectacle, salle, horaire
Protection : permission backend
```

La phrase ne dit pas encore le nom des fichiers, le `related_name`, le comportement `on_delete` ou la redirection : ce sont des décisions à documenter ou des précisions à retrouver ailleurs dans l'énoncé.

## 4. Transformer une fonctionnalité en CRUD

```text
Create → créer
Read   → lire
Update → modifier
Delete → supprimer
```

| Verbe du sujet | CRUD probable |
|---|---|
| consulter, afficher, rechercher | Read |
| ajouter, créer | Create |
| affecter, associer, modifier | Update ou création d’association |
| retirer, désaffilier | Update ou suppression d’association |
| supprimer | Delete |

> « Ajouter un artiste à une troupe » ne signifie pas nécessairement créer un nouvel artiste.

Cela peut vouloir dire :

```text
modifier la relation de l’artiste existant
```

En revanche :

```text
Ajouter une vidéo à un spectacle
```

implique généralement la création d'une nouvelle instance `Video`, liée au `Show` existant.

## 5. Distinguer création d’objet et création d’association

Question de décision :

```text
L’objet existe-t-il déjà ?
    Oui → probablement associer ou modifier
    Non → probablement créer un nouvel objet
```

Cas fréquents :

```text
Ajouter une vidéo à un spectacle
→ créer Video avec une ForeignKey vers Show

Ajouter un artiste à une troupe
→ modifier artist.troupe

Ajouter un mot-clé pour un spectacle
→ créer ou retrouver Tag, puis créer l’association

Ajouter une langue avec un niveau
→ créer une ligne dans le modèle intermédiaire
```

Je vérifie aussi si le formulaire doit proposer des objets existants ou permettre d'en créer un. Une liste déroulante suggère souvent la sélection d'une instance existante.

## 6. Analyser le tableau des données

Traduction indicative :

| Indication | Traduction Django probable | Question à vérifier |
|---|---|---|
| `Texte (60)` | `models.CharField(max_length=60)` | vide autorisé ? |
| `Entier court` | `SmallIntegerField` ou variante positive | négatif/zéro autorisé ? |
| `Null interdit` | `null=False` | formulaire obligatoire aussi ? |
| `Unique` | `unique=True` ou `UniqueConstraint` | champ seul ou combinaison ? |
| `> 0` | validateur + `CheckConstraint` | zéro vraiment interdit ? |
| `Clé primaire` | `id` automatique dans la plupart des cas | type imposé ? |
| `Clé étrangère` | `ForeignKey` | cible, nullabilité et `on_delete` ? |

Checklist :

```text
[ ] Nom du champ
[ ] Type Django
[ ] Taille
[ ] Obligatoire ou facultatif
[ ] Valeur unique
[ ] Valeur par défaut
[ ] Validateur
[ ] Contrainte de base
[ ] Relation éventuelle
```

Le tableau peut être incomplet. Exemple :

```text
Room contient id, name et seats dans le tableau,
mais le texte impose aussi une relation vers Location.
```

La relation `Room.location` doit alors être déduite de la partie backend, même si `location_id` manque dans le tableau. Je vérifie toujours le tableau **et** les phrases métier.

## 7. Détecter les erreurs de copier-coller

Exemples manifestement suspects :

```text
Room.id décrit comme « Id du média »
Room.name décrit comme « Mot-clé »
```

Méthode :

1. lire le titre de la table ;
2. lire les fonctionnalités F/A ;
3. lire toute la partie backend ;
4. comparer les formulations entre elles ;
5. identifier la donnée isolée et incohérente ;
6. retenir l'interprétation la plus cohérente avec l'ensemble ;
7. noter l'ambiguïté dans la remise si elle influence réellement la solution.

Je ne suis pas aveuglément une description copiée d'un autre sujet. Le titre, les champs, les fonctionnalités et les relations répétées ont plus de poids qu'un libellé isolé manifestement erroné.

## 8. Déduire les modèles et relations implicites

| Phrase métier | Déduction |
|---|---|
| Un spectacle possède plusieurs vidéos | `Video` porte une `ForeignKey` vers `Show` |
| Un artiste appartient à une troupe | `Artist` porte une `ForeignKey` vers `Troupe` |
| Un spectacle possède plusieurs tags et inversement | `ManyToManyField` |
| Un artiste parle plusieurs langues avec un niveau | Modèle intermédiaire |
| Un lieu possède plusieurs salles | `Room` porte une `ForeignKey` vers `Location` |
| Une représentation se donne dans une salle | `Representation` porte une `ForeignKey` vers `Room` |

La clé étrangère d'une relation one-to-many se place normalement du côté « plusieurs ». Les minimums `0` ou `1`, `on_delete` et les contraintes supplémentaires doivent encore être déterminés.

Voir `02_ANALYSER_RELATIONS.md` pour les cardinalités détaillées.

Particularité actuelle : Réservations possède `Representation.location`; le modèle `Room` et `Representation.room` sont des évolutions possibles d'examen, pas l'état présent.

## 9. Déduire les pages à modifier

> « Afficher X d’un Y » signifie généralement modifier la page de détail de Y.

| Consigne | Vue existante probable | ORM | Contexte/template | Cas vide |
|---|---|---|---|---|
| Afficher les vidéos d’un spectacle | vue détail `Show` | `show.videos.all()` | `show/show.html` | « Aucune vidéo » |
| Afficher les salles d’un lieu | vue détail `Location` | `location.rooms.all()` | `location/show.html` | « Aucune salle » |
| Afficher la troupe d’un artiste | vue détail `Artist` | `artist.troupe` | `artist/show.html` | « Non affilié » |
| Afficher les représentations d’un spectacle | vue détail `Show` | `show.representations.all()` | `show/show.html` | « Aucune représentation » |

Je vérifie avant modification : la vue existe-t-elle, quel nom de contexte utilise-t-elle, la relation est-elle déjà préchargée et le template possède-t-il déjà une section adaptée ?

Dans le projet réel, les vues de détail `show`, `location` et `artist` existent. `Show.representations` existe également ; `videos`, `rooms` et `troupe` restent hypothétiques tant que leurs modèles ne sont pas créés.

## 10. Déduire les composants Django

| Exigence | Composants probables |
|---|---|
| Nouvelle table | modèle, import, migration |
| Données de test | fixture ou seeder |
| Affichage | vue, ORM, contexte, template |
| Formulaire | module de formulaire, vue GET/POST, template |
| Action administrateur | permission, formulaire, vue |
| Route paramétrée | `urls.py`, vue, template |
| Recherche | formulaire GET, ORM, compteur |
| Modification asynchrone | HTML, JavaScript, route, vue JSON |
| Contrainte métier | formulaire, modèle, base, tests |

Checklist de fichiers possibles — ils ne sont pas tous toujours nécessaires :

```text
[ ] catalogue/models/<modele>.py
[ ] catalogue/models/__init__.py
[ ] catalogue/migrations/<numero>_*.py
[ ] catalogue/forms/<Formulaire>.py
[ ] catalogue/forms/__init__.py
[ ] catalogue/views/<vue>.py
[ ] catalogue/views/__init__.py
[ ] catalogue/urls.py
[ ] catalogue/templates/<dossier>/<page>.html
[ ] catalogue/static/catalogue/js/<script>.js
[ ] catalogue/fixtures/<donnees>.json
[ ] catalogue/management/commands/<commande>.py
[ ] catalogue/tests.py ou tests dédiés
```

Le projet utilise effectivement une organisation en sous-modules pour modèles, formulaires et vues. Je ne crée un fichier que si l'organisation actuelle et la fonctionnalité le justifient.

## 11. Interpréter « générer »

Certains sujets emploient un vocabulaire venant de Laravel, Symfony ou Spring :

| Terme du sujet | Django |
|---|---|
| Entité | Modèle |
| Contrôleur | Vue |
| Mapping | Relation ORM |
| Seeder | Commande personnalisée ou fixture |
| Route | `path()` |
| Génération de structure | Commandes Django + création manuelle selon le composant |

Django sait générer une application (`startapp`) et des migrations (`makemigrations`), mais ne possède pas nécessairement de générateur natif créant automatiquement chaque modèle, vue, formulaire et template. « Générez le modèle » signifie donc souvent « créez correctement le modèle dans le framework ».

Je réponds au résultat technique demandé, sans inventer une commande inexistante.

## 12. Lire « affichez »

Pour toute consigne d'affichage, je réponds à :

```text
Quelle page ?
Quel objet principal ?
Quelles relations charger ?
Quel ordre ?
Quels champs ?
Quel cas vide ?
Quels liens ?
Qui peut voir ?
```

Exemples :

- « affichez les vidéos dans la fiche d'un spectacle » : page détail `Show`, collection de vidéos, titre/lecteur, message vide ;
- « affichez le nom et le logo de la troupe » : relation facultative depuis `Artist`, alternative « Non affilié », URL d'image validée ;
- « affichez les langues et le niveau » : parcourir les objets du modèle intermédiaire, pas seulement `artist.languages` ;
- « affichez le nombre de résultats » : calculer un compteur correspondant au queryset filtré.

## 13. Lire « ajoutez »

Pour toute consigne d'ajout :

```text
Quel objet est créé ou modifié ?
Quels champs saisir ?
Quelles listes déroulantes ?
Quelle relation enregistrer ?
Quelle méthode HTTP ?
Quelle permission ?
Quelle redirection ?
Quel message de succès ?
Quelles validations ?
```

Je distingue : création d'une `Video`, modification de `artist.troupe`, ajout d'une association `Show–Tag`, ou création de `ArtistLanguage` avec son niveau.

Une action d'ajout comporte généralement un affichage GET du formulaire et un traitement POST. Si elle est asynchrone, le backend reste une vue protégée et validée.

## 14. Lire « empêchez »

Ce verbe signale une règle métier ou de sécurité :

| Consigne | Traitement probable |
|---|---|
| Empêcher si la salle est occupée | validation métier + contrainte de base |
| Empêcher si l’utilisateur n’est pas administrateur | autorisation backend |
| Empêcher les doublons | validation + contrainte unique |
| Empêcher la suppression d’un parent utilisé | `on_delete=PROTECT` ou `RESTRICT` |

Une condition JavaScript, un champ caché ou un bouton invisible ne constitue jamais une protection : l'URL peut être appelée directement. La vue et, lorsque possible, la base doivent faire respecter la règle.

## 15. Lire « route personnalisée et paramétrée »

Méthode :

1. identifier le paramètre métier ;
2. choisir `int`, `slug` ou `str` ;
3. déclarer la route ;
4. utiliser exactement le même nom de paramètre dans la vue ;
5. récupérer l'objet ou renvoyer 404 ;
6. appliquer la requête ORM ;
7. utiliser `distinct()` si une jointure multiple peut dupliquer les lignes ;
8. transmettre le résultat au template ;
9. gérer le cas vide.

Patrons de réflexion :

| Paramètre donné | Choix fréquent | Recherche probable |
|---|---|---|
| salle | `<int:room_id>` ou `<slug:slug>` | représentations/spectacles liés |
| langue | `<slug:slug>` de préférence, sinon `<str:name>` | artistes + niveau filtré |
| artiste | `<int:artist_id>` | spectacles puis vidéos |
| tag | `<slug:slug>` ou `<str:tag>` | spectacles liés ou exclus |
| catégorie | `<slug:category_slug>` | catégorie et `shows` |

Le projet utilise déjà `category/<slug:category_slug>/` et plusieurs identifiants entiers. Un nom avec accents ou espaces est moins stable qu'un slug ou une PK.

Voir `07_ROUTES_PARAMETREES.md` pour le code détaillé.

## 16. Repérer les validations cachées dans le texte

| Formulation | Déduction probable |
|---|---|
| déjà occupée au même moment | validation multi-champs + unicité salle/horaire en base |
| nom unique | `unique=True` ou contrainte composée selon la portée |
| strictement supérieur à zéro | validateur Python + `CheckConstraint` |
| seulement si l’artiste est comédien | condition métier/filtre sur le type d'artiste |
| zéro ou plusieurs | collection facultative, par exemple M2M `blank=True` |
| une et une seule | relation obligatoire avec maximum un |
| administrateur connecté | authentification + autorisation backend |

Nuance : une unicité `room + schedule` interdit deux instants exactement égaux ; elle ne détecte pas automatiquement deux plages qui se chevauchent si les représentations ont une durée.

## 17. Distinguer exigence et choix personnel

| Exigences imposées | Choix généralement laissés au développeur |
|---|---|
| nom limité à 60 | nom exact de la fonction de vue |
| unicité | nom du template |
| nombre supérieur à zéro | nom interne de la route |
| liste déroulante | organisation des fichiers |
| administrateur seulement | mise en page |
| route avec paramètre | message précis |
| comportement de suppression explicite | identifiant ou slug si non imposé |

Un choix personnel doit rester cohérent dans le modèle, la vue, la route, le template et les tests. Si je choisis `room_id`, je n'emploie pas soudain `id_room` dans la signature de vue.

## 18. Construire le plan avant de coder

### Exemple court rempli — affiliation d'un artiste existant

```text
Fonctionnalité : affilier un artiste
Acteur : administrateur connecté
Action : sélectionner ou retirer une troupe
Objet principal : Artist existant
Objet créé ou modifié : Artist modifié
Modèles concernés : Artist, Troupe
Relation : ForeignKey facultative sur Artist
Champs : troupe
Contraintes : troupe valide ; absence autorisée si « Non affilié »
Vue existante à modifier : détail Artist pour afficher
Nouvelle vue : action d’affiliation si séparée
Formulaire : ModelChoiceField facultatif
Template : fiche artiste ou fragment de formulaire
Route : artiste + identifiant
Paramètre : artist_id entier
Permission : backend administrateur
Données de test : artistes affilié et non affilié
Tests : affichage, POST autorisé, refus utilisateur normal
```

Ce plan ne constitue pas un corrigé complet : `on_delete`, le nom des fichiers et le droit exact doivent être confirmés par l'énoncé et le projet.

Modèle vide à copier :

```text
Fonctionnalité :
Acteur :
Action :
Objet principal :
Objet créé ou modifié :
Modèles concernés :
Relation :
Champs :
Contraintes :
Vue existante à modifier :
Nouvelle vue :
Formulaire :
Template :
Route :
Paramètre :
Permission :
Données de test :
Tests :
```

## 19. Créer une matrice de traçabilité

Tableau vierge :

| N° | Exigence | Fichier(s) | Vérification | Terminé |
|---|---|---|---|---|
| | | | | `[ ]` |

Exemple de préparation, sans solution propre à un sujet :

| N° | Exigence | Fichier(s) probable(s) | Vérification | Terminé |
|---|---|---|---|---|
| F1 | Consultation | vue + template | page remplie et vide | `[ ]` |
| F2 | Recherche | vue + template | filtre et compteur | `[ ]` |
| A1 | Action admin | formulaire + vue + template | normal refusé, admin autorisé | `[ ]` |
| Backend 1 | Nouvelle donnée/relation | modèle + migration | `check`, migration relue | `[ ]` |
| Route personnalisée | Filtre paramétré | `urls.py` + vue + template | valide, 404, vide | `[ ]` |
| Données de test | Démonstration | fixture ou commande | réexécution contrôlée | `[ ]` |

Cette matrice évite de terminer le CRUD principal en oubliant la route personnalisée, le jeu de données ou une condition de sécurité.

## 20. Ordre recommandé d’implémentation

```text
1. Lire tout l’énoncé
2. Identifier modèles et relations
3. Vérifier le projet existant
4. Créer/modifier les modèles
5. Créer les migrations
6. Traiter les données existantes
7. Ajouter les données de test
8. Implémenter les lectures F1/F2
9. Implémenter l’action A1
10. Ajouter les validations
11. Ajouter les autorisations
12. Créer la route paramétrée
13. Tester chaque exigence
14. Produire le dump et le ZIP
```

Je valide progressivement : modèle avec `check`, migration relue, données visibles, vue en lecture, action autorisée/refusée, puis route spéciale. Tout tester à la fin mélange les causes et consomme davantage de temps.

## 21. Exemples d’analyse complète

Ces analyses identifient les tâches sans fournir leur implémentation complète.

### Exemple A — Salles

```text
Ce qui est explicite : consulter les salles d’un lieu ; champs de Room éventuels
Ce qui est implicite : relation Location–Room et cas sans salle
Objet créé ou modifié : Room si une action d’ajout est demandée
Relation : one-to-many ; FK portée par Room
Pages concernées : détail Location
Formulaire : Room avec lieu si création demandée
Validation : places positives, nom/unicité selon l’énoncé
Autorisation : lecture publique ; écriture selon l’acteur
Route : lieu identifié par id ou slug
Données de test : lieu avec salles et lieu vide
Tests minimums : relation, affichage, vide, contrainte
```

### Exemple B — Vidéos

```text
Ce qui est explicite : consulter et ajouter une vidéo à un spectacle
Ce qui est implicite : création de Video liée au Show existant
Objet créé ou modifié : nouvelle Video
Relation : FK obligatoire sur Video
Pages concernées : détail Show
Formulaire : titre et URL ; spectacle fixé par la route ou sélectionné
Validation : URL et éventuelle unicité
Autorisation : ajout réservé à l’administrateur
Route : Show identifié ; éventuelle route filtrée par artiste
Données de test : spectacle avec et sans vidéos
Tests minimums : affichage, création admin, refus normal, URL invalide
```

### Exemple C — Troupe

```text
Ce qui est explicite : afficher et affilier un artiste à une troupe
Ce qui est implicite : l’artiste existe probablement déjà
Objet créé ou modifié : Artist modifié, pas forcément Troupe créée
Relation : FK sur Artist ; facultativité à confirmer avec « Non affilié »
Pages concernées : détail Artist
Formulaire : liste déroulante de Troupe
Validation : choix appartenant au queryset
Autorisation : affiliation réservée à l’administrateur
Route : Artist identifié
Données de test : artiste affilié et non affilié
Tests minimums : affichage des deux cas, POST autorisé/refusé
```

### Exemple D — Tags

```text
Ce qui est explicite : rechercher par mot-clé et associer un tag
Ce qui est implicite : relation many-to-many et distinct possible
Objet créé ou modifié : Tag créé/retrouvé puis association ajoutée
Relation : ManyToManyField simple
Pages concernées : liste/recherche Show et détail Show
Formulaire : GET pour chercher ; POST pour associer
Validation : tag unique, association non dupliquée
Autorisation : recherche publique ; association administrateur
Route : tag en paramètre pour le filtre demandé
Données de test : tags partagés, spectacle sans tag
Tests minimums : résultats, compteur, doublons, permission
```

### Exemple E — Langues avec niveau

```text
Ce qui est explicite : langues d’un artiste et niveau de maîtrise
Ce qui est implicite : le niveau appartient à la relation
Objet créé ou modifié : nouvelle association ArtistLanguage
Relation : many-to-many avec modèle intermédiaire
Pages concernées : détail Artist
Formulaire : Language + level en listes
Validation : couple Artist–Language unique ; niveau autorisé
Autorisation : ajout administrateur
Route : langue paramétrée pour filtrer les artistes courants
Données de test : plusieurs niveaux et langues partagées
Tests minimums : niveau affiché, doublon refusé, filtre, permission
```

## 22. Exercices d’interprétation

Lire seulement la consigne, préparer son plan, puis ouvrir la correction.

### Exercice 1

> Un gestionnaire affecte un tarif existant à plusieurs spectacles.

<details><summary>Correction</summary>

- Composants probables : relation M2M existante, formulaire de sélection, vue POST, permission, template et tests.
- Ambiguïté : un ou plusieurs spectacles par soumission ? création de tarif autorisée ou non ?
- Interprétation raisonnable : sélectionner un tarif et des spectacles existants puis créer les associations, sans recréer les objets.

</details>

### Exercice 2

> Un utilisateur consulte les prochaines représentations d’un lieu.

<details><summary>Correction</summary>

- Composants probables : route de lieu, vue GET, filtre `schedule` futur, ORM, template et cas vide.
- Ambiguïté : « prochaines » signifie après l'instant actuel ; ordre et limite non précisés.
- Interprétation raisonnable : filtrer après maintenant et trier chronologiquement.

</details>

### Exercice 3

> Un administrateur désactive les réservations d’un spectacle.

<details><summary>Correction</summary>

- Composants probables : champ booléen existant `Show.bookable`, formulaire/action POST, permission, message et test.
- Ambiguïté : les réservations existantes sont-elles annulées ?
- Interprétation raisonnable : modifier seulement l'ouverture des nouvelles réservations, conserver les anciennes sauf consigne contraire.

</details>

### Exercice 4

> Une salle ne peut recevoir plus de réservations que son nombre de places.

<details><summary>Correction</summary>

- Composants probables : agrégation des quantités, validation backend, transaction/verrou si concurrence, tests.
- Ambiguïté : capacité par représentation ou par journée ? réservations annulées comptées ?
- Interprétation raisonnable : capacité vérifiée pour chaque représentation, en excluant les statuts non actifs définis par le métier.

</details>

### Exercice 5

> Rechercher les artistes dont le nom commence par la valeur fournie.

<details><summary>Correction</summary>

- Composants probables : formulaire GET, `__istartswith`, vue de liste, compteur et template.
- Ambiguïté : prénom, nom de famille ou nom complet ? casse et accents ?
- Interprétation raisonnable : préciser les deux champs recherchés et conserver la requête dans le formulaire.

</details>

### Exercice 6

> Ajouter une catégorie par défaut aux spectacles sans catégorie.

<details><summary>Correction</summary>

- Composants probables : modèle/contrainte cible, migration de données, éventuellement seeder et tests.
- Ambiguïté : catégorie existante ou à créer ? défaut seulement pour l'historique ou aussi le futur ?
- Interprétation raisonnable : migration par étapes, catégorie stable identifiée, vérification avant FK obligatoire.

</details>

### Exercice 7

> Un producteur modère uniquement les avis de ses spectacles.

<details><summary>Correction</summary>

- Composants probables : authentification, rôle `PRODUCER`, association `Show.producers`, filtre ORM, autorisation par objet, POST/JSON et tests.
- Ambiguïté : le staff conserve-t-il un droit global ?
- Interprétation raisonnable : vérifier rôle **et** association au spectacle ; appliquer la même portée à la liste et à l'action.

</details>

### Exercice 8

> Supprimer un lieu seulement s’il n’est utilisé par aucune représentation.

<details><summary>Correction</summary>

- Composants probables : `on_delete=PROTECT/RESTRICT`, vue POST protégée, gestion de l'exception et tests.
- Ambiguïté : les salles ou spectacles liés doivent-ils également bloquer ?
- Interprétation raisonnable : empêcher la suppression dès qu'une relation protégée existe et afficher un message explicite.

</details>

### Exercice 9

> Afficher un badge lorsqu’un spectacle possède au moins une représentation future.

<details><summary>Correction</summary>

- Composants probables : annotation `Exists` ou préchargement, contexte et condition de template.
- Ambiguïté : fuseau horaire et représentation exactement à l'instant courant.
- Interprétation raisonnable : comparer à `timezone.now()` côté vue et transmettre un booléen clair.

</details>

## 23. Questions à se poser avant chaque fichier

### Avant le modèle

```text
[ ] Quels champs ?
[ ] Quelles relations ?
[ ] Quelles contraintes ?
[ ] Quelles anciennes données ?
```

### Avant la vue

```text
[ ] Lecture ou modification ?
[ ] GET ou POST ?
[ ] Quel objet principal ?
[ ] Quelle permission ?
[ ] Quelle réponse ?
```

### Avant le template

```text
[ ] Quelles variables de contexte ?
[ ] Quelle collection ?
[ ] Quel cas vide ?
[ ] Quels liens ?
[ ] Quelle visibilité ?
```

### Avant la route

```text
[ ] Quel paramètre ?
[ ] Quel convertisseur ?
[ ] Quel nom ?
[ ] La vue utilise-t-elle le même nom ?
```

## 24. Checklist express d’analyse

À remplir en moins de deux minutes :

```text
[ ] J’ai identifié F1/F2/A1
[ ] J’ai identifié les acteurs
[ ] J’ai identifié les objets créés et modifiés
[ ] J’ai identifié les modèles
[ ] J’ai déterminé les relations
[ ] J’ai traduit le tableau en champs
[ ] J’ai repéré les contraintes métier
[ ] J’ai repéré les autorisations
[ ] J’ai identifié les pages existantes à modifier
[ ] J’ai identifié les nouveaux fichiers
[ ] J’ai identifié la route et son paramètre
[ ] J’ai prévu les données de test
[ ] J’ai prévu les tests
[ ] J’ai noté les ambiguïtés
```

Si une case reste incertaine, je note explicitement l'hypothèse choisie et son impact avant de coder. Je consulte ensuite la fiche spécialisée correspondante plutôt que d'improviser sous pression.
