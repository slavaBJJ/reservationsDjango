# 11 — JavaScript asynchrone avec Django

## Quand utiliser cette fiche ?

Quand une action doit modifier une donnée sans recharger toute la page : modération, association, changement d'état ou suppression.

```text
clic utilisateur
→ fetch()
→ URL Django
→ vue backend
→ validation et sauvegarde
→ réponse JSON
→ mise à jour du DOM
```

JavaScript améliore l'expérience ; Django reste responsable de l'authentification, des permissions, de la validation et des contraintes métier.

## Étapes dans l’ordre

```text
1. Créer la route POST
2. Protéger la vue et valider les objets
3. Retourner du JSON cohérent
4. Générer l'URL dans le template
5. Stocker URL/action dans data-*
6. Lire le CSRF
7. Appeler fetch
8. Vérifier response.ok
9. Mettre à jour le DOM après succès
10. Gérer erreur et état d'attente
```

## Exemple générique complet

### 1. HTML et attributs `data-*`

```django
<button
    type="button"
    class="js-status-button"
    data-object-id="{{ object.pk }}"
    data-url="{% url 'catalogue:object-status' object.pk %}"
    data-status="approved"
>
    Approuver
</button>
<p id="status-message-{{ object.pk }}" role="status" aria-live="polite"></p>
```

- Le bouton ne soumet pas automatiquement un formulaire.
- Django génère l'URL ; JavaScript ne la code pas en dur.
- `data-*` expose seulement des données d'interface, jamais une preuve d'autorisation.
- La zone `role="status"` annonce le résultat aux technologies d'assistance.

### 2. Lire le cookie CSRF

```javascript
function getCookie(name) {
    const cookies = document.cookie ? document.cookie.split(';') : [];
    for (const cookie of cookies) {
        const trimmed = cookie.trim();
        if (trimmed.startsWith(`${name}=`)) {
            return decodeURIComponent(trimmed.slice(name.length + 1));
        }
    }
    return null;
}

const csrfToken = getCookie('csrftoken');
```

- La fonction parcourt les cookies accessibles.
- `decodeURIComponent` restitue la valeur encodée.
- Le cookie CSRF doit avoir été créé ; inclure `{% csrf_token %}` dans la page ou employer une stratégie Django documentée.

### 3. Fonction `fetch()` complète

```javascript
async function changeStatus(button) {
    const message = document.querySelector(
        `#status-message-${button.dataset.objectId}`,
    );
    const originalText = button.textContent;

    button.disabled = true;
    button.textContent = 'Enregistrement…';
    message.textContent = '';

    try {
        const body = new URLSearchParams({status: button.dataset.status});
        const response = await fetch(button.dataset.url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body,
        });
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Échec de la requête.');
        }

        message.textContent = data.message;
        button.dataset.status = data.status;
    } catch (error) {
        message.textContent = error.message;
    } finally {
        button.disabled = false;
        button.textContent = originalText;
    }
}

document.querySelectorAll('.js-status-button').forEach((button) => {
    button.addEventListener('click', () => changeStatus(button));
});
```

- `async/await` attend les opérations réseau et JSON.
- Le bouton est désactivé pour éviter les doubles clics.
- `URLSearchParams` produit des données lisibles via `request.POST`.
- `X-CSRFToken` permet la vérification CSRF de Django.
- `response.ok` couvre les statuts HTTP 200–299 ; une réponse JSON 403 reste une erreur.
- Le DOM n'est mis à jour qu'après confirmation backend.
- `catch` affiche l'erreur ; `finally` restaure toujours le bouton.

### 4. Route

```python
path(
    'object/<int:object_id>/status/',
    views.object_status,
    name='object-status',
)
```

Le nom `object_id` doit correspondre à la signature de vue.

### 5. Vue Django

```python
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST


@login_required
@require_POST
def object_status(request, object_id):
    object = get_object_or_404(Model, pk=object_id)

    if not request.user.has_perm('catalogue.change_model'):
        return JsonResponse(
            {'success': False, 'error': 'Accès interdit.'},
            status=403,
        )

    status = request.POST.get('status')
    allowed_statuses = {'approved', 'rejected'}
    if status not in allowed_statuses:
        return JsonResponse(
            {'success': False, 'error': 'État invalide.'},
            status=400,
        )

    object.status = status
    object.save(update_fields=['status'])
    return JsonResponse({
        'success': True,
        'status': object.status,
        'message': 'État enregistré.',
    })
```

- Les décorateurs exigent connexion et POST.
- `get_object_or_404` ne fait pas confiance à l'ID reçu.
- La permission est recalculée côté serveur.
- La valeur est comparée à une liste autorisée.
- `update_fields` limite les colonnes sauvegardées.
- Le JSON contient un indicateur stable et les valeurs nécessaires à l'interface.

**À renommer :** `Model`, `object`, `status`, permission, route, textes et valeurs autorisées.

## Envoi JSON

JavaScript :

```javascript
const response = await fetch(url, {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken,
    },
    body: JSON.stringify({status: 'approved'}),
});
```

Django classique :

```python
import json

try:
    data = json.loads(request.body)
except json.JSONDecodeError:
    return JsonResponse({'success': False, 'error': 'JSON invalide.'}, status=400)
```

`request.POST` n'est pas rempli automatiquement par un corps JSON ; il faut lire `request.body`. Limiter la taille, vérifier les types et gérer le JSON invalide.

## POST, PATCH et DELETE

| Méthode | Usage courant | Django classique |
|---|---|---|
| POST | action/création, très compatible avec formulaires | `request.POST` si encodage formulaire |
| PATCH | modification partielle | lire souvent `request.body`; DRF le gère mieux |
| DELETE | suppression | lire souvent `request.body`; CSRF toujours requis avec session |

Un endpoint Django classique peut utiliser POST pour une action nommée. Une API REST utilisera plus naturellement PATCH/DELETE. La méthode seule n'assure aucune autorisation.

## Sécurité backend obligatoire

La vue vérifie toujours :

```text
[ ] utilisateur connecté
[ ] permission ou propriété de l'objet
[ ] méthode HTTP
[ ] existence de chaque objet
[ ] type et valeur des données
[ ] contrainte métier
[ ] conflit de base éventuel
```

## Réponses JSON

```python
return JsonResponse({'success': True, 'count': 4})
return JsonResponse(
    {'success': False, 'error': 'Valeur invalide.'},
    status=400,
)
```

Conserver une structure et des statuts HTTP cohérents. Ne pas renvoyer une page HTML de connexion si le code appelle immédiatement `response.json()` ; prévoir une stratégie adaptée pour les endpoints AJAX.

## Exemples prêts à adapter

### Changement de catégorie

```text
Envoyer category_id → vérifier change_show → charger Category → show.category = category → JSON avec nom.
```

### Modération d’un avis

```text
Envoyer action=approve/reject → vérifier staff ou producteur du spectacle → modifier moderation_status.
```

Le projet possède déjà `review.moderate`, une vue POST JSON utilisant `request.POST`.

### Association d’un tag

```text
Envoyer tag_id → vérifier add/change_show → show.tags.add(tag) → renvoyer la liste ou le compteur.
```

### Changement de troupe

```text
Envoyer troupe_id vide ou entier → charger Troupe si fourni → artist.troupe = troupe/None → sauvegarder.
```

### Suppression asynchrone

```text
POST vers une route delete → permission delete → objet.delete() → JSON → retirer la ligne après succès.
```

### Actualisation d’un compteur

```javascript
document.querySelector('#tag-count').textContent = data.count;
```

Le compteur doit provenir de la réponse serveur après modification.

## UX

- Désactiver le contrôle pendant la requête.
- Afficher « Enregistrement… ».
- Empêcher les doubles clics.
- Ne modifier définitivement le DOM qu'après succès.
- Restaurer l'interface en cas d'erreur.
- Utiliser `role="status"` et `aria-live="polite"`.
- Garder une solution HTML normale lorsque la consigne ou l'accessibilité l'exige.

## Erreurs fréquentes

- Oublier CSRF.
- Sécuriser seulement en JavaScript ou dans le template.
- Faire confiance aux IDs ou au rôle envoyés par le navigateur.
- Ne pas vérifier `response.ok`.
- Oublier ou déclarer un mauvais `Content-Type`.
- Retourner HTML alors que JavaScript attend JSON.
- Modifier le DOM avant confirmation backend.
- Coder une URL en dur alors que `{% url %}` peut la produire.
- Ne pas gérer JSON invalide ou erreur réseau.
- Laisser le bouton désactivé après une exception.

## Vérifications

```powershell
.venv\Scripts\python.exe manage.py test
.venv\Scripts\python.exe manage.py runserver
```

Dans le navigateur : console et onglet Réseau, statuts 200/400/403/404, réponse JSON, CSRF, double clic et restauration après erreur.

## Checklist express

```text
[ ] URL générée par Django
[ ] data-* contient seulement des données d'interface
[ ] CSRF transmis
[ ] méthode HTTP vérifiée
[ ] permission vérifiée côté backend
[ ] données et objets validés
[ ] réponse JSON et statut cohérents
[ ] response.ok vérifié
[ ] DOM modifié après succès
[ ] erreur et double clic gérés
```
