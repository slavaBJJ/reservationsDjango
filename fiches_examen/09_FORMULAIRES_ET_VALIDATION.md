# 09 — Formulaires et validation Django

## Quand utiliser cette fiche ?

Pour recevoir et valider des données HTML avant de créer ou modifier une instance. Une validation de formulaire améliore l'interface ; une contrainte de base protège toutes les écritures.

## Étapes dans l’ordre

```text
1. Choisir Form ou ModelForm
2. Déclarer les champs autorisés
3. Configurer les listes déroulantes
4. Ajouter les validations de champ
5. Ajouter la validation croisée
6. Protéger la vue
7. Appeler is_valid puis save
8. Afficher toutes les erreurs
9. Ajouter une contrainte de base si nécessaire
```

## `forms.Form` ou `forms.ModelForm` ?

| Type | Usage | Sauvegarde |
|---|---|---|
| `forms.Form` | recherche, confirmation, import, données sans modèle direct | logique manuelle |
| `forms.ModelForm` | création/modification d'une instance de modèle | `form.save()` |

Une classe de formulaire décrit la validation ; une instance `form` contient les données d'une requête précise.

## ModelForm minimal

```python
from django import forms

from application.models import ModelName


class ModelNameForm(forms.ModelForm):
    class Meta:
        model = ModelName
        fields = ['name', 'description']
```

- `forms` fournit les classes de formulaires.
- `model` indique l'entité créée/modifiée.
- `fields` est une liste blanche : ne pas utiliser aveuglément tous les champs sensibles.

**À renommer :** application, modèle, classe et champs.

## Listes déroulantes avec `ModelChoiceField`

```python
class ArtistTroupeForm(forms.Form):
    troupe = forms.ModelChoiceField(
        queryset=Troupe.objects.order_by('name'),
        empty_label='Non affilié',
        required=False,
    )
```

- `queryset` définit les instances acceptées, pas seulement affichées.
- `empty_label` nomme le choix vide.
- `required=False` le rend facultatif côté formulaire.
- `__str__()` de `Troupe` fournit les libellés.

Filtrage dynamique sans requête au chargement du module :

```python
def __init__(self, *args, user=None, **kwargs):
    super().__init__(*args, **kwargs)
    self.fields['room'].queryset = Room.objects.filter(active=True)
```

La vue passe `user=request.user` si les choix dépendent de l'utilisateur. Ne jamais se fier uniquement aux options visibles : le queryset du champ valide aussi la valeur reçue.

## Formulaire de représentation

```python
class RepresentationForm(forms.ModelForm):
    schedule = forms.DateTimeField(
        label='Date et heure',
        input_formats=['%Y-%m-%dT%H:%M'],
        widget=forms.DateTimeInput(
            format='%Y-%m-%dT%H:%M',
            attrs={'type': 'datetime-local'},
        ),
    )
    show = forms.ModelChoiceField(queryset=Show.objects.order_by('title'))
    room = forms.ModelChoiceField(queryset=Room.objects.order_by('name'))

    class Meta:
        model = Representation
        fields = ['show', 'room', 'schedule']
```

- Les `ModelChoiceField` produisent des listes et renvoient des **instances**, pas de simples identifiants.
- `datetime-local` impose un format compris par le navigateur ; Django valide la valeur.
- Le projet réel possède déjà une variante avec `schedule` et `location`; adapter à `room` seulement après création de ce modèle et migration.

## Validation d’un champ

```python
def clean_field_name(self):
    value = self.cleaned_data['field_name']
    if not value:
        raise forms.ValidationError('Valeur invalide.')
    return value
```

- Le nom doit être `clean_<nom_exact_du_champ>`.
- La valeur nettoyée vient de `cleaned_data`.
- Toujours retourner la valeur acceptée, éventuellement normalisée.

Exemple réel inspiré de `RepresentationForm` : une nouvelle représentation doit être future. La vue de modification doit décider si une date passée inchangée reste autorisée.

## Validation portant sur plusieurs champs

```python
def clean(self):
    cleaned_data = super().clean()
    room = cleaned_data.get('room')
    schedule = cleaned_data.get('schedule')

    if room and schedule:
        conflict = Representation.objects.filter(
            room=room,
            schedule=schedule,
        ).exclude(pk=self.instance.pk)
        if conflict.exists():
            raise forms.ValidationError(
                'Cette salle est déjà occupée à cet horaire.'
            )

    return cleaned_data
```

- `super().clean()` exécute d'abord les validations individuelles.
- `.get()` évite une seconde erreur si un champ est déjà invalide.
- Le queryset cherche le même couple salle-horaire.
- `.exclude(pk=self.instance.pk)` retire l'objet en cours pendant une modification ; sinon il entrerait en conflit avec lui-même.
- Pour une création, `self.instance.pk` vaut normalement `None`, et l'exclusion est sans effet utile.
- La `ValidationError` générale apparaît dans `form.non_field_errors`.

Cette validation offre un bon message, mais une `UniqueConstraint(fields=['room', 'schedule'], ...)` reste nécessaire contre les écritures concurrentes et les chemins qui contournent le formulaire.

## Quatre niveaux de validation

| Niveau | Exemple | Déclenchement | Limite |
|---|---|---|---|
| Validateur de champ | `MinValueValidator(1)` | formulaire / `full_clean()` | peut être contourné |
| `Form.clean()` | conflit salle-horaire | `form.is_valid()` | concerne ce formulaire |
| `Model.clean()` | règle métier multi-champs | `full_clean()` | `save()` ne l'appelle pas toujours |
| Contrainte de base | `UniqueConstraint` | toute écriture en base | message parfois moins convivial |

## Vues create et update

Création :

```python
form = FormClass(request.POST or None)
if request.method == 'POST' and form.is_valid():
    object = form.save()
    return redirect('catalogue:object-show', object_id=object.pk)
```

Modification :

```python
object = get_object_or_404(Model, pk=object_id)
form = FormClass(request.POST or None, instance=object)
if request.method == 'POST' and form.is_valid():
    object = form.save()
    return redirect('catalogue:object-show', object_id=object.pk)
```

- `request.POST or None` crée un formulaire non lié en GET et lié en POST.
- `instance=object` est indispensable pour modifier plutôt que créer une nouvelle ligne.
- `is_valid()` remplit `cleaned_data` et les erreurs.
- Rediriger après succès évite une resoumission au rafraîchissement.

## Sécurité

```python
from django.contrib.auth.decorators import permission_required

@permission_required('catalogue.add_room', raise_exception=True)
def create(request):
    ...
```

La permission doit protéger la **vue**. Un `{% if perms... %}` dans le template améliore l'interface, mais un utilisateur peut appeler l'URL directement.

## Exemples prêts à adapter

```python
class VideoForm(forms.ModelForm):
    class Meta:
        model = Video
        fields = ['title', 'video_url']

    def clean_video_url(self):
        url = self.cleaned_data['video_url'].strip()
        if not url.startswith(('https://', 'http://')):
            raise forms.ValidationError('URL HTTP(S) requise.')
        return url
```

`URLField` du modèle/formulaire est généralement préférable à ce test simplifié. **À renommer :** modèle, champs et règle selon le sujet.

## Erreurs fréquentes

- Oublier `form.is_valid()` avant `cleaned_data` ou `save()`.
- Construire le formulaire seulement en POST et ne rien afficher en GET.
- Oublier `instance` en modification et créer un doublon.
- Oublier `form.save()` après validation.
- Dupliquer une validation de formulaire sans contrainte de base nécessaire.
- Oublier `.exclude(pk=self.instance.pk)` pendant une modification.
- Exposer une liste déroulante non filtrée selon les droits métier.
- Oublier `form.non_field_errors` dans le template.
- Confondre `required=False` du formulaire et `blank=True/null=True` du modèle.
- Inclure dans `fields` une propriété que l'utilisateur ne doit pas contrôler.

## Vérifications

```powershell
.venv\Scripts\python.exe manage.py check
.venv\Scripts\python.exe manage.py test
```

Tester GET vide, POST valide, POST invalide, doublon, modification sans faux conflit et utilisateur sans permission.

## Checklist express

```text
[ ] Form ou ModelForm choisi consciemment
[ ] fields est une liste blanche
[ ] QuerySets des listes filtrés
[ ] clean_<field> retourne la valeur
[ ] clean appelle super
[ ] modification exclut self.instance.pk
[ ] is_valid avant save
[ ] instance fournie en update
[ ] vue protégée
[ ] non_field_errors affichées
[ ] contrainte de base ajoutée si nécessaire
```
