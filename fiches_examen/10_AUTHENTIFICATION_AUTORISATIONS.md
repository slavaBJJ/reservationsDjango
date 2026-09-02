# 10 — Authentification et autorisations

## Quand utiliser cette fiche ?

Dès qu'une page ou action n'est pas publique, particulièrement les formulaires réservés aux administrateurs et les modifications asynchrones.

```text
authentification = qui est l’utilisateur ?
autorisation = a-t-il le droit d’effectuer cette action ?
```

## Étapes dans l’ordre

```text
1. Définir qui peut agir
2. Choisir permission, staff, superuser ou rôle métier
3. Protéger la vue backend
4. Imposer la méthode HTTP de modification
5. Protéger avec CSRF
6. Adapter l'affichage du template
7. Tester anonyme, utilisateur normal et utilisateur autorisé
```

## Protéger une vue fonction

```python
from django.contrib.auth.decorators import (
    login_required,
    permission_required,
    user_passes_test,
)
```

### Connexion requise

```python
@login_required
def profile(request):
    ...
```

Un anonyme est normalement redirigé vers la page de connexion avec un paramètre `next`.

### Test personnalisé

```python
def is_catalogue_admin(user):
    return user.is_authenticated and user.is_staff


@user_passes_test(is_catalogue_admin)
def create_room(request):
    ...
```

Le test reçoit l'utilisateur. Selon la configuration, un échec peut rediriger plutôt que renvoyer 403 ; pour une permission Django précise, préférer le décorateur suivant.

### Permission précise

```python
@permission_required('catalogue.add_room', raise_exception=True)
def create_room(request):
    ...
```

- Le code est `<application>.<codename>`.
- `raise_exception=True` renvoie une réponse 403 à l'utilisateur connecté sans droit.

**À renommer :** application, action, modèle et fonction.

## Quel indicateur utiliser ?

| Test | Signification | Usage |
|---|---|---|
| `user.is_authenticated` | session/utilisateur reconnu | accès réservé aux connectés |
| `user.is_staff` | autorisé à accéder au site d'administration | consigne explicite « staff/admin Django » |
| `user.is_superuser` | possède toutes les permissions | opérations exceptionnelles globales |
| `user.has_perm('catalogue.add_room')` | permission précise, directement ou via groupe | action CRUD ciblée |

Ne pas remplacer automatiquement « administrateur » par `is_superuser`. Demander ce que le sujet attend ; une permission précise est souvent plus sûre.

## Permissions Django

Pour chaque modèle, Django crée normalement :

```text
add_model
change_model
delete_model
view_model
```

Dans un template :

```django
{% if perms.catalogue.add_room %}
    <a href="{% url 'catalogue:room-create' %}">Ajouter une salle</a>
{% endif %}
```

Dans une vue :

```python
if not request.user.has_perm('catalogue.add_room'):
    raise PermissionDenied
```

Le template améliore l'interface ; la vue garantit la sécurité.

## Protection des méthodes HTTP

```python
from django.views.decorators.http import require_POST

@login_required
@permission_required('catalogue.delete_room', raise_exception=True)
@require_POST
def delete_room(request, room_id):
    ...
```

- `require_POST` refuse GET pour cette action.
- Un formulaire navigateur doit inclure `{% csrf_token %}`.
- GET doit normalement rester sans effet de bord.

## Groupes et rôles réels du projet

Le projet possède ces groupes métier :

```text
MEMBER
PRODUCER
CRITIC
AFFILIATE_FREE
AFFILIATE_STARTER
AFFILIATE_PREMIUM
```

Il fournit :

```python
has_role(user, ROLE_PRODUCER)
is_producer_for(user, show)
```

- `has_role` vérifie l'appartenance au groupe ; le superutilisateur est accepté.
- `is_producer_for` exige le rôle `PRODUCER` **et** l'association au spectacle.
- Un groupe métier n'est pas identique à `is_staff`.
- Le projet permet par exemple au staff ou au producteur assigné de modérer certains avis.

Exemple inspiré du projet :

```python
@login_required
def edit_show(request, show_id):
    show = get_object_or_404(Show, pk=show_id)
    allowed = (
        request.user.has_perm('catalogue.change_show')
        or is_producer_for(request.user, show)
    )
    if not allowed:
        raise PermissionDenied
    ...
```

La permission globale et le rôle lié à l'instance sont deux chemins d'autorisation explicites.

## Réponses possibles

- **Redirection connexion** : appropriée pour un anonyme visitant une page HTML avec `login_required`.
- **403 Forbidden** : utilisateur identifié mais non autorisé.
- **JSON 401/403** : endpoint asynchrone/API ; 401 concerne l'absence d'authentification, 403 le droit refusé.
- **Message d'erreur + redirection** : utile pour une règle métier, sans remplacer un vrai refus d'autorisation.

Le comportement exact dépend de l'architecture : les décorateurs Django classiques et DRF ne répondent pas toujours de la même façon.

## Vue et template : les deux niveaux

```django
{% if perms.catalogue.add_room %}
    <form method="post">
        {% csrf_token %}
        {{ form.as_p }}
        <button type="submit">Ajouter</button>
    </form>
{% endif %}
```

```python
@permission_required('catalogue.add_room', raise_exception=True)
def create_room(request):
    ...
```

Un utilisateur peut fabriquer une requête sans le bouton. Seule la seconde protection impose le droit côté serveur.

## Exemples prêts à adapter

Endpoint de modification court :

```python
@login_required
@require_POST
def moderate(request, review_id):
    review = get_object_or_404(Review, pk=review_id)
    if not request.user.is_staff:
        return JsonResponse({'error': 'Accès interdit.'}, status=403)
    # Valider l'action, modifier, sauvegarder, répondre.
```

Le vrai projet possède déjà une version plus fine : staff ou producteur affecté au spectacle. **À renommer :** modèle, permission et règle d'instance.

## Erreurs fréquentes

- Cacher le bouton sans protéger la vue.
- Confondre staff, superutilisateur et groupe métier.
- Modifier/supprimer par GET.
- Oublier CSRF dans un formulaire ou `fetch` authentifié par session.
- Faire confiance à un rôle, utilisateur ou ID envoyé par le navigateur.
- Vérifier seulement `is_authenticated` quand une permission est requise.
- Donner un droit global au lieu de vérifier la propriété de l'objet.
- Retourner une page de connexion HTML alors que JavaScript attend du JSON.

## Vérifications

Tester chaque action avec :

```text
1. utilisateur anonyme
2. utilisateur connecté sans droit
3. utilisateur possédant le rôle mais pas l'objet
4. utilisateur autorisé
5. superutilisateur si pertinent
6. GET sur une action POST
7. POST sans CSRF depuis le navigateur
```

```powershell
.venv\Scripts\python.exe manage.py test
```

## Checklist express

```text
[ ] Authentification distinguée de l'autorisation
[ ] Règle exacte identifiée
[ ] Vue backend protégée
[ ] Template cohérent avec la permission
[ ] POST/PATCH/DELETE pour modifier
[ ] CSRF présent
[ ] Objet et propriété vérifiés
[ ] 403/JSON cohérent
[ ] Anonyme, normal et admin testés
```
