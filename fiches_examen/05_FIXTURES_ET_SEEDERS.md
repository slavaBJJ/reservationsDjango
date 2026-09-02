# 05 — Fixtures, seeders et données de test

## Quand utiliser cette fiche ?

Après les migrations, pour disposer rapidement de données cohérentes pendant l'examen ou préparer une remise reproductible.

```text
fixture = fichier contenant des données
seeder = code qui crée ou met à jour des données
```

Django utilise principalement les fixtures, les commandes de gestion personnalisées, les migrations de données et les données créées dans les tests.

## Étapes dans l’ordre

```text
1. Appliquer les migrations
2. Identifier les dépendances entre modèles
3. Choisir fixture ou seeder
4. Valider les fichiers
5. Charger dans l'ordre
6. Réexécuter si l'outil est idempotent
7. Vérifier les comptes et relations
```

## Shell Django

```powershell
.venv\Scripts\python.exe manage.py shell
```

Ce shell charge les réglages Django et les modèles. Exemples génériques :

```python
Model.objects.create(name='Exemple')
obj, created = Model.objects.get_or_create(name='Exemple')
obj, created = Model.objects.update_or_create(
    name='Exemple',
    defaults={'description': 'Mise à jour'},
)
```

- `create()` insère toujours et renvoie l'instance ; il peut provoquer un doublon ou une `IntegrityError`.
- `get_or_create()` renvoie `(objet, created)` ; `created` vaut `True` seulement après insertion.
- `update_or_create()` recherche avec les arguments hors `defaults`, crée si absent ou actualise les valeurs de `defaults`.
- `Model` désigne une **classe** ; `obj` est une **instance**.

## Fixtures JSON

```powershell
.venv\Scripts\python.exe manage.py dumpdata application.model --indent=2
.venv\Scripts\python.exe manage.py dumpdata application.model --indent=2 > application\fixtures\data.json
.venv\Scripts\python.exe manage.py loaddata data.json
```

- `dumpdata` sérialise les lignes ; sans redirection, il affiche le JSON.
- `>` appartient à PowerShell : il écrit la sortie dans le fichier indiqué.
- `loaddata` **importe réellement** les données dans la base active ; ce n'est pas une vérification.
- Django recherche le nom demandé dans les dossiers `fixtures` des applications et dans `FIXTURE_DIRS`.

Structure :

```json
[
  {
    "model": "catalogue.category",
    "pk": 1,
    "fields": {
      "name": "Théâtre",
      "slug": "theatre"
    }
  }
]
```

- `model` est `<application>.<modèle>` en minuscules.
- `pk` est la clé primaire ; elle doit éviter les collisions.
- `fields` contient les autres valeurs et références.

Validation de syntaxe JSON sous Windows :

```powershell
py -m json.tool application\fixtures\data.json
```

Cette commande vérifie le JSON, pas les modèles ni les clés étrangères.

## Relations et ordre d’importation

Ordre conceptuel possible :

```text
Location
→ Room
→ Show
→ Representation
→ Reservation
```

Un enfant référençant un parent absent provoque une erreur d'intégrité ou une erreur de désérialisation. Avec les vrais modèles actuels, charger notamment `Locality` avant `Location`, `Location`/`Category` avant `Show`, `Show` avant `Representation`, puis les associations de réservation.

Fixtures existantes utiles : `categories.json`, `localities.json`, `locations.json`, `shows.json`, `representations.json`, `prices.json` et plusieurs tables d'association. Ne pas tout recharger sans comprendre les PK et les dépendances.

## Clés naturelles

```powershell
.venv\Scripts\python.exe manage.py dumpdata catalogue --natural-foreign --natural-primary --indent=2
```

- `--natural-foreign` représente certaines FK avec une clé métier plutôt qu'une PK.
- `--natural-primary` omet la PK si le modèle sait la reconstruire par clé naturelle.
- Elles rendent certaines fixtures plus transportables mais exigent `natural_key()` et `get_by_natural_key()` cohérents.

Le projet en définit notamment pour `Artist`, `Locality`, `Location`, `Price`, `Show` et `Type`. Une clé naturelle modifiée peut rendre une ancienne fixture introuvable.

## Commande de gestion personnalisée

Arborescence obligatoire :

```text
application/
    management/
        __init__.py
        commands/
            __init__.py
            seed_data.py
```

Exemple prêt à adapter :

```python
from django.core.management.base import BaseCommand

from application.models import Model


class Command(BaseCommand):
    help = 'Crée les données de démonstration.'

    def handle(self, *args, **options):
        obj, created = Model.objects.update_or_create(
            name='Exemple',
            defaults={'description': 'Donnée de démonstration'},
        )
        action = 'créé' if created else 'mis à jour'
        self.stdout.write(self.style.SUCCESS(f'{obj} : {action}'))
```

- `BaseCommand` fournit l'infrastructure `manage.py`.
- `help` documente la commande.
- `handle()` est son point d'entrée.
- `update_or_create()` évite le doublon selon `name` et actualise la description.
- `stdout` affiche un résultat testable.

**À renommer :** `application`, `Model`, `seed_data`, les champs et la clé de recherche.

## Réexécution sans doublon : idempotence

| Méthode | Nouvelle exécution | Usage |
|---|---|---|
| `create()` | recrée ou échoue | donnée volontairement nouvelle |
| `get_or_create()` | conserve l'existant | référentiel stable |
| `update_or_create()` | actualise l'existant | démonstration synchronisée |

Une commande idempotente peut être relancée sans multiplier inutilement les catégories, lieux ou comptes. Les contraintes uniques restent nécessaires face aux erreurs et exécutions concurrentes.

## Particularités du projet Réservations

```powershell
.venv\Scripts\python.exe manage.py seed_demo_catalogue
.venv\Scripts\python.exe manage.py create_demo_accounts
```

- `seed_demo_catalogue` utilise des recherches/créations et prépare le catalogue.
- `create_demo_accounts` crée/met à jour les groupes et comptes, appelle déjà `seed_demo_catalogue`, puis assigne les spectacles au producteur.
- Pour une démonstration complète, exécuter **seulement `create_demo_accounts`** évite un appel manuel redondant au seeder.
- Ces commandes refusent l'environnement lorsque `DEBUG=False`, protection prévue contre une exécution de démonstration en production.

## Utilisateurs et mots de passe

Ne jamais écrire directement un mot de passe dans le champ `password` : Django attend un hash.

```python
user.set_password('mot-de-passe-fictif')
user.save(update_fields=['password'])
```

- `set_password()` calcule le hash sécurisé.
- `save()` l'enregistre.
- Employer uniquement une valeur fictive de démonstration, jamais un secret réel.

## Données des tests automatisés

```python
@classmethod
def setUpTestData(cls):
    cls.category = Category.objects.create(
        name='Test',
        slug='test',
    )
```

`manage.py test` crée généralement une base temporaire isolée, charge les données du test et la supprime ensuite. Ces données ne remplissent pas la base locale de démonstration.

## Quand choisir quoi ?

| Besoin | Outil |
|---|---|
| Petit ensemble statique portable | fixture |
| Création conditionnelle, relations ou calculs | commande seeder |
| Donnée indispensable à une évolution de schéma | migration de données |
| Scénario isolé d'un test | `setUpTestData()` ou factory locale |

## Exemples prêts à adapter

```powershell
# Charger seulement les catégories existantes
.venv\Scripts\python.exe manage.py loaddata categories.json

# Préparer toute la démonstration locale du projet
.venv\Scripts\python.exe manage.py create_demo_accounts
```

La première commande modifie la base et peut entrer en conflit avec des données déjà présentes. La seconde est la procédure intégrée prévue par le projet.

## Sécurité

- Aucun mot de passe en clair dans une fixture commitée.
- Aucune donnée personnelle réelle.
- Aucun secret, token, clé API ou URL de production confidentielle.
- Aucun export brut de la table utilisateurs destiné au dépôt public.
- Utiliser `set_password()` ou `create_user()`.
- Vérifier la base active avant `loaddata` ou un seeder.

## Erreurs fréquentes

- Confondre export `dumpdata` et import `loaddata`.
- Croire que `loaddata` ne fait que vérifier.
- Charger les enfants avant leurs parents.
- Réutiliser des PK entrant en conflit.
- Relancer `create()` et produire des doublons.
- Oublier les tables intermédiaires.
- Copier des hashes ou mots de passe réels.
- Exécuter à la fois `seed_demo_catalogue` et une commande qui l'appelle déjà.
- Croire que les données des tests restent dans la base locale.

## Vérifications

```powershell
py -m json.tool catalogue\fixtures\categories.json
.venv\Scripts\python.exe manage.py check
.venv\Scripts\python.exe manage.py shell
```

Dans le shell, utiliser `Model.objects.count()` et vérifier les relations importantes. Quitter avec `exit()`.

## Checklist express

```text
[ ] Migrations appliquées avant les données
[ ] Bonne base sélectionnée
[ ] Parents chargés avant enfants
[ ] JSON valide
[ ] Seeder idempotent
[ ] Couples uniques respectés
[ ] Mots de passe créés avec set_password/create_user
[ ] Aucun secret ou donnée personnelle
[ ] Données visibles dans l'application
```
