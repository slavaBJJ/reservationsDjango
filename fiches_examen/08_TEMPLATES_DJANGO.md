# 08 — Mini-templates Django prêts à adapter

## Quand utiliser cette fiche ?

Quand la vue fonctionne et qu'il faut afficher une liste, une relation, un formulaire, une recherche ou des actions. Le template présente les données ; la vue (contrôleur) conserve la logique métier et la sécurité.

## Étapes dans l’ordre

```text
1. Identifier le template et le layout
2. Noter les variables exactes du contexte
3. Étendre layouts/base.html
4. Afficher le cas normal
5. Ajouter le cas vide/facultatif
6. Générer les URLs par leur nom
7. Protéger les POST avec CSRF
8. Vérifier permissions, HTML et accessibilité
```

## Bases du projet

Le layout réel fournit `title`, `content`, `extra_css` et `extra_js` et charge Bootstrap 5.3.

```django
{% extends 'layouts/base.html' %}

{% block title %}Titre de la page{% endblock %}

{% block content %}
    <main class="container py-4">
        Contenu
    </main>
{% endblock %}
```

- `{% extends %}` doit être la première balise de template utile.
- `block title` remplit le titre du navigateur.
- `block content` remplit la zone principale du layout.
- Le layout réel possède déjà un `<main>` ; utiliser plutôt un `<div>` que créer un second `<main>` :

```django
{% block content %}<div class="container py-4">Contenu</div>{% endblock %}
```

Syntaxe :

```django
{{ variable }}
{% instruction %}
{# commentaire non rendu #}
```

- `{{ ... }}` affiche une valeur échappée.
- `{% ... %}` exécute une instruction de template.
- `{# ... #}` est un commentaire Django.

## Mini-template 1 — Liste simple

```django
<ul>
    {% for object in objects %}
        <li>{{ object }}</li>
    {% empty %}
        <li>Aucune donnée.</li>
    {% endfor %}
</ul>
```

`{% empty %}` évite un test séparé lorsque la collection est vide.

```text
Contexte attendu : objects (QuerySet ou liste)
À remplacer : object, objects, message vide
```

## Mini-template 2 — Liste avec lien de détail

```django
<ul>
    {% for room in rooms %}
        <li>
            <a href="{% url 'catalogue:room-show' room.id %}">
                {{ room.name }}
            </a>
        </li>
    {% empty %}
        <li>Aucune salle.</li>
    {% endfor %}
</ul>
```

`{% url %}` génère la route nommée avec l'identifiant.

```text
Contexte attendu : rooms
À remplacer : room(s), name, namespace et nom de route
```

## Mini-template 3 — Détail d’un objet

```django
<article>
    <h1>{{ object.name }}</h1>
    <p>{{ object.description|default:"Aucune description." }}</p>
    {% if object.website %}
        <a href="{{ object.website }}">Site officiel</a>
    {% endif %}
</article>
```

La condition évite un lien vide. Les URL provenant d'utilisateurs doivent être validées côté formulaire/modèle.

```text
Contexte attendu : object
À remplacer : propriétés et libellés
```

## Mini-template 4 — Relation one-to-many : salles d’un lieu

```django
<h2>Salles de {{ location.designation }}</h2>
<ul>
    {% for room in location.rooms.all %}
        <li>{{ room.name }} — {{ room.seats }} places</li>
    {% empty %}
        <li>Aucune salle pour ce lieu.</li>
    {% endfor %}
</ul>
```

Dans un template Django, écrire `.all` sans parenthèses. Précharger `rooms` dans la vue si la page affiche plusieurs lieux.

```text
Contexte attendu : location avec related_name rooms
À remplacer : rooms, name, seats
```

## Mini-template 5 — Relation many-to-many : tags

```django
<ul class="list-inline">
    {% for tag in show.tags.all %}
        <li class="list-inline-item badge text-bg-secondary">{{ tag.tag }}</li>
    {% empty %}
        <li>Aucun mot-clé.</li>
    {% endfor %}
</ul>
```

La table intermédiaire simple est masquée par `show.tags`. Précharger `tags` dans une liste de spectacles.

```text
Contexte attendu : show avec relation tags
À remplacer : tags, tag.tag, classes CSS
```

## Mini-template 6 — Modèle intermédiaire : langue et niveau

```django
<ul>
    {% for relation in artist.artist_languages.all %}
        <li>
            {{ relation.language.name }} — {{ relation.get_level_display }}
        </li>
    {% empty %}
        <li>Aucune langue renseignée.</li>
    {% endfor %}
</ul>
```

La boucle parcourt les **instances d'association**, car `level` se trouve sur elles. `get_level_display` affiche le libellé d'un champ `choices`.

```text
Contexte attendu : artist ; accès inverse artist_languages
À remplacer : related_name, champ language.name, champ level
```

## Mini-template 7 — Représentations imbriquées

```django
<ul>
    {% for representation in representations %}
        <li>
            {{ representation.schedule|date:"d/m/Y" }}
            à {{ representation.schedule|date:"H:i" }} —
            {{ representation.show.title }} —
            {{ representation.room.name }} —
            {{ representation.room.location.designation }}
        </li>
    {% empty %}
        <li>Aucune représentation.</li>
    {% endfor %}
</ul>
```

La vue devrait utiliser `select_related('show', 'room', 'room__location')`. Actuellement, le projet possède `representation.location`, pas encore `room`.

```text
Contexte attendu : representations
À remplacer : room par la relation réellement implémentée
```

## Mini-template 8 — Affichage conditionnel

```django
{% if artist.troupe %}
    <p>{{ artist.troupe.name }}</p>
{% else %}
    <p>Non affilié</p>
{% endif %}

{% if show.videos.exists %}
    <p>Des vidéos sont disponibles.</p>
{% else %}
    <p>Aucune vidéo.</p>
{% endif %}

{% if shows %}
    <p>{{ shows|length }} spectacle{{ shows|length|pluralize }}.</p>
{% else %}
    <p>Aucun spectacle.</p>
{% endif %}
```

Dans une vraie liste, préférer `{% for %}{% empty %}`. Éviter des appels répétés comme `exists` puis boucle si cela ajoute des requêtes.

```text
Contexte attendu : artist, show, shows
À remplacer : relations et messages
```

## Mini-template 9 — Image de logo

```django
{% if artist.troupe and artist.troupe.logo_url %}
    <img
        src="{{ artist.troupe.logo_url }}"
        alt="Logo de {{ artist.troupe.name }}"
        width="50"
        loading="lazy"
    >
{% else %}
    <span>Aucun logo.</span>
{% endif %}
```

`width="50"` impose la largeur demandée ; l'alternative décrit l'image. Valider l'URL côté backend et ne pas autoriser arbitrairement des schémas dangereux.

```text
Contexte attendu : artist et troupe facultative
À remplacer : logo_url, name et texte alternatif
```

## Mini-template 10 — Vidéo

Fichier HTML5 validé :

```django
{% if video.file_url %}
    <video controls preload="metadata">
        <source src="{{ video.file_url }}" type="video/mp4">
        Votre navigateur ne peut pas lire cette vidéo.
    </video>
{% else %}
    <p>Aucune vidéo.</p>
{% endif %}
```

Lien externe :

```django
{% if video.video_url %}
    <a href="{{ video.video_url }}" rel="noopener noreferrer">
        Voir {{ video.title }}
    </a>
{% else %}
    <p>Aucune vidéo.</p>
{% endif %}
```

Intégration seulement avec une URL transformée et autorisée côté backend :

```django
{% if video.embed_url %}
    <iframe
        src="{{ video.embed_url }}"
        title="{{ video.title }}"
        allowfullscreen
    ></iframe>
{% endif %}
```

Ne jamais injecter directement une URL non fiable dans un `iframe`; utiliser une liste de domaines et une transformation backend.

```text
Contexte attendu : video
À remplacer : champs URL et types MIME
```

## Mini-template 11 — Formulaire POST

```django
<form method="post">
    {% csrf_token %}
    {{ form.as_p }}
    <button type="submit" class="btn btn-primary">Enregistrer</button>
</form>
```

`csrf_token` protège la soumission navigateur ; `form.as_p` affiche champs et erreurs de base.

```text
Contexte attendu : form
À remplacer : libellé, action éventuelle et classes
```

## Mini-template 12 — Liste déroulante manuelle

```django
<label for="id_troupe">Troupe</label>
<select id="id_troupe" name="troupe">
    <option value="">Non affilié</option>
    {% for troupe in troupes %}
        <option
            value="{{ troupe.pk }}"
            {% if selected_troupe_id == troupe.pk %}selected{% endif %}
        >
            {{ troupe.name }}
        </option>
    {% empty %}
        <option value="" disabled>Aucune troupe disponible</option>
    {% endfor %}
</select>
```

Comparer des types cohérents (`int` contre `int`). Un `ModelChoiceField` est préférable lorsqu'un `Form` Django existe : il valide que la PK appartient au queryset autorisé.

```text
Contexte attendu : troupes, selected_troupe_id
À remplacer : noms, champs, id HTML et libellés
```

## Mini-template 13 — Formulaire réservé à l’administrateur

Variante staff :

```django
{% if request.user.is_staff %}
    {% include 'room/_form.html' %}
{% endif %}
```

Variante permission précise :

```django
{% if perms.catalogue.add_room %}
    {% include 'room/_form.html' %}
{% endif %}
```

`is_staff` signifie accès possible à l'administration, pas nécessairement permission métier exacte. `perms.catalogue.add_room` correspond mieux à l'action. **Cacher ne sécurise pas** : la vue doit refaire la vérification.

```text
Contexte attendu : request, perms, form via context processor standard
À remplacer : application, permission et fragment inclus
```

## Mini-template 14 — Recherche GET

```django
<form method="get" role="search">
    <label for="id_q">Mot-clé</label>
    <input id="id_q" name="q" value="{{ query }}">
    <button type="submit">Rechercher</button>
</form>

<p aria-live="polite">{{ result_count }} résultat{{ result_count|pluralize }}</p>

<ul>
    {% for show in shows %}
        <li>{{ show.title }}</li>
    {% empty %}
        <li>Aucun résultat.</li>
    {% endfor %}
</ul>
```

GET convient à une recherche ; `value` conserve le critère. Django échappe automatiquement la variable.

```text
Contexte attendu : query, result_count, shows
À remplacer : champ q, collection et propriétés
```

## Mini-template 15 — Messages Django

```django
{% if messages %}
    <div aria-live="polite">
        {% for message in messages %}
            <div class="alert alert-{{ message.tags|default:'info' }}">
                {{ message }}
            </div>
        {% endfor %}
    </div>
{% endif %}
```

Le layout réel affiche déjà les messages et transforme le tag `error` en classe Bootstrap `danger`. Ne pas dupliquer ce bloc dans les pages qui l'étendent.

```text
Contexte attendu : messages fourni par Django
À remplacer : classes seulement si le layout n'affiche rien
```

## Mini-template 16 — Erreurs de formulaire

```django
{{ form.non_field_errors }}

{% for field in form %}
    <div class="mb-3">
        {{ field.label_tag }}
        {{ field }}
        {% if field.help_text %}<div>{{ field.help_text }}</div>{% endif %}
        {{ field.errors }}
    </div>
{% endfor %}
```

`non_field_errors` affiche les erreurs de `clean()` portant sur plusieurs champs ; `field.errors` affiche celles du champ courant.

```text
Contexte attendu : form lié ou non lié
À remplacer : classes et structure visuelle
```

## Mini-template 17 — Pagination conservant la recherche

```django
<nav aria-label="Pagination">
    {% if page_obj.has_previous %}
        <a href="?q={{ query|urlencode }}&page={{ page_obj.previous_page_number }}">
            Précédente
        </a>
    {% endif %}

    <span>Page {{ page_obj.number }} sur {{ page_obj.paginator.num_pages }}</span>

    {% if page_obj.has_next %}
        <a href="?q={{ query|urlencode }}&page={{ page_obj.next_page_number }}">
            Suivante
        </a>
    {% endif %}
</nav>
```

`urlencode` sécurise le paramètre. Avec plusieurs filtres, reconstruire la query string dans la vue ou via un tag dédié évite d'en oublier.

```text
Contexte attendu : page_obj, query
À remplacer : nom des paramètres conservés
```

Le projet transmet parfois la page sous la clé `shows`; dans ce cas utiliser `shows.has_previous`, etc.

## Mini-template 18 — Boutons CRUD et permissions

```django
<a href="{% url 'catalogue:room-show' room.pk %}">Voir</a>

{% if perms.catalogue.add_room %}
    <a href="{% url 'catalogue:room-create' %}">Ajouter</a>
{% endif %}

{% if perms.catalogue.change_room %}
    <a href="{% url 'catalogue:room-edit' room.pk %}">Modifier</a>
{% endif %}

{% if perms.catalogue.delete_room %}
    <form method="post" action="{% url 'catalogue:room-delete' room.pk %}">
        {% csrf_token %}
        <button type="submit">Supprimer</button>
    </form>
{% endif %}
```

La suppression utilise POST. Les vues doivent appliquer les mêmes permissions.

```text
Contexte attendu : room, perms
À remplacer : modèle, routes et permissions
```

## Mini-template 19 — Confirmation de suppression

```django
<h1>Supprimer {{ object }}</h1>
<p>Cette action peut être irréversible.</p>

<form method="post">
    {% csrf_token %}
    <button type="submit" class="btn btn-danger">Confirmer</button>
    <a href="{% url 'catalogue:object-show' object.pk %}">Annuler</a>
</form>
```

La vue GET affiche la confirmation ; le POST réalise l'action. Une vue décorée strictement `require_POST` peut plutôt utiliser un petit formulaire directement sur la page détail.

```text
Contexte attendu : object
À remplacer : route, modèle et libellés
```

## Mini-template 20 — Préparation JavaScript asynchrone

```django
<button
    type="button"
    data-object-id="{{ review.pk }}"
    data-url="{% url 'catalogue:review-moderate' review.pk %}"
    data-action="approve"
>
    Approuver
</button>

<p id="message-{{ review.pk }}" role="status" aria-live="polite"></p>
```

`data-*` fournit l'identifiant, l'URL résolue et l'action sans coder l'adresse dans JavaScript. Voir `11_JAVASCRIPT_ASYNCHRONE.md`.

```text
Contexte attendu : review
À remplacer : route, action, identifiants et libellé
```

## Mini-template 21 — Tableau accessible

```django
<table class="table">
    <caption>Liste des salles</caption>
    <thead>
        <tr><th scope="col">Nom</th><th scope="col">Places</th></tr>
    </thead>
    <tbody>
        {% for room in rooms %}
            <tr>
                <th scope="row">
                    <a href="{% url 'catalogue:room-show' room.pk %}">{{ room.name }}</a>
                </th>
                <td>{{ room.seats }}</td>
            </tr>
        {% empty %}
            <tr><td colspan="2">Aucune salle.</td></tr>
        {% endfor %}
    </tbody>
</table>
```

Le `caption`, les `th` et `scope` décrivent la structure ; `colspan` correspond au nombre de colonnes.

```text
Contexte attendu : rooms
À remplacer : caption, colonnes, route et propriétés
```

## Mini-template 22 — Cartes Bootstrap

```django
<div class="row g-3">
    {% for show in shows %}
        <div class="col-12 col-md-6 col-lg-4">
            <article class="card h-100">
                <div class="card-body">
                    <h2 class="h5 card-title">{{ show.title }}</h2>
                    <p class="card-text">
                        {{ show.description|default:"Aucune description."|truncatechars:120 }}
                    </p>
                    <a class="btn btn-primary" href="{% url 'catalogue:show-show' show.pk %}">
                        Voir
                    </a>
                </div>
            </article>
        </div>
    {% empty %}
        <p>Aucun spectacle.</p>
    {% endfor %}
</div>
```

Ces classes sont compatibles avec Bootstrap déjà chargé dans `layouts/base.html`.

```text
Contexte attendu : shows
À remplacer : collection, champs et route
```

## Filtres et balises à connaître

```django
{{ value|default:"Valeur de remplacement" }}
{{ value|default_if_none:"Non défini" }}
{{ schedule|date:"d/m/Y H:i" }}
{{ objects|length }}
{{ description|truncatechars:80 }}
{{ active|yesno:"Oui,Non" }}
{{ text|urlize }}
{% load static %}
{% static 'catalogue/img/logo.svg' %}
{% csrf_token %}
{% url 'catalogue:show-show' show.pk %}
```

- `default` remplace une valeur fausse/vide ; `default_if_none` seulement `None`.
- `date`, `length`, `truncatechars`, `yesno`, `urlize` transforment l'affichage.
- `static` résout un fichier statique après `{% load static %}`.
- `csrf_token` protège un formulaire POST.
- `url` résout une route nommée.

## Exemples prêts à adapter

Patron complet minimal :

```django
{% extends 'layouts/base.html' %}

{% block title %}Liste{% endblock %}

{% block content %}
    <div class="container py-4">
        <h1>Liste</h1>
        <ul>
            {% for object in objects %}
                <li>{{ object }}</li>
            {% empty %}
                <li>Aucune donnée.</li>
            {% endfor %}
        </ul>
    </div>
{% endblock %}
```

```text
Contexte attendu : objects
À remplacer : titre, object(s), propriétés, route éventuelle
```

## Erreurs fréquentes

- Ouvrir le fichier avec `file:///` : les balises ne sont interprétées que par Django via `runserver`.
- Écrire `location.rooms.all()` : dans un template, utiliser `location.rooms.all`.
- Oublier `{% csrf_token %}` dans un formulaire POST.
- Utiliser un nom absent du contexte.
- Oublier le namespace `catalogue:`.
- Mettre une requête ou règle métier complexe dans le template.
- Cacher un formulaire sans protéger la vue.
- Laisser une balise HTML ou un bloc Django non fermé.
- Injecter une URL utilisateur non validée dans `iframe`, `src` ou `href`.
- Oublier `{% empty %}` ou le cas facultatif.
- Créer un second élément `<main>` alors que le layout en possède déjà un.

## Vérifications

```powershell
.venv\Scripts\python.exe manage.py check
.venv\Scripts\python.exe manage.py runserver
```

Vérifier dans le navigateur : liste remplie/vide, URL de détail, utilisateur anonyme/autorisé, erreurs de formulaire, HTML responsive et console JavaScript.

## Checklist express

```text
[ ] extends layouts/base.html
[ ] title et content fermés
[ ] Variables identiques au contexte
[ ] {% empty %} ou cas vide
[ ] Relations facultatives testées
[ ] URLs nommées avec namespace
[ ] POST protégé par CSRF
[ ] Permissions visibles et backend protégé
[ ] HTML fermé et accessible
[ ] Pas de logique métier complexe
```
