# 12 — Tests, débogage, dump SQL et ZIP

## Quand utiliser cette fiche ?

À chaque étape importante, puis avant la remise finale, pour prouver que le projet fonctionne dans une installation reproductible.

## Étapes dans l’ordre

```text
1. check
2. migrations cohérentes
3. tests ciblés
4. suite complète
5. test manuel des profils
6. dump demandé
7. copie propre sans secrets
8. réinstallation de l'archive
9. création du ZIP final
```

## Vérifications Django

```powershell
.venv\Scripts\python.exe manage.py check
.venv\Scripts\python.exe manage.py makemigrations --check
.venv\Scripts\python.exe manage.py showmigrations
.venv\Scripts\python.exe manage.py test
```

- `check` contrôle la configuration et les modèles.
- `makemigrations --check` échoue si un changement de modèle n'a pas sa migration.
- `showmigrations` affiche `[X]` pour les migrations appliquées.
- `test` crée normalement une base temporaire et exécute les tests.

## Tests de modèles

```python
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models.deletion import ProtectedError
from django.test import TestCase


class RoomModelTests(TestCase):
    def setUp(self):
        self.location = Location.objects.create(
            slug='lieu-test',
            designation='Lieu test',
        )

    def test_valid_room(self):
        room = Room.objects.create(name='Studio', seats=10, location=self.location)
        self.assertEqual(room.seats, 10)

    def test_unique_name_in_location(self):
        Room.objects.create(name='Studio', seats=10, location=self.location)
        with self.assertRaises(IntegrityError):
            Room.objects.create(name='Studio', seats=20, location=self.location)

    def test_positive_seats_validation(self):
        room = Room(name='Vide', seats=0, location=self.location)
        with self.assertRaises(ValidationError):
            room.full_clean()

    def test_relation(self):
        room = Room.objects.create(name='Studio', seats=10, location=self.location)
        self.assertEqual(room.location, self.location)

    def test_protected_location(self):
        Room.objects.create(name='Studio', seats=10, location=self.location)
        with self.assertRaises(ProtectedError):
            self.location.delete()
```

- `setUp()` crée le parent nécessaire avant chaque test ; `self.location` est une instance.
- `create` teste une sauvegarde réelle dans la base de test.
- `IntegrityError` vérifie une contrainte de base ; selon le backend, entourer ce test d'un contexte transactionnel adapté si la suite continue.
- `full_clean()` déclenche les validateurs Python.
- `ProtectedError` correspond à `PROTECT`; le projet emploie aussi `RESTRICT`, qui lève `RestrictedError`.

**À renommer :** modèle, champs, contrainte et exception d'après `on_delete`.

## Tests de vues

```python
from django.urls import reverse

response = self.client.get(reverse('catalogue:room-index'))
self.assertEqual(response.status_code, 200)

response = self.client.get(reverse('catalogue:room-show', args=[999999]))
self.assertEqual(response.status_code, 404)

response = self.client.get(reverse('catalogue:room-create'))
self.assertEqual(response.status_code, 302)  # redirection connexion possible

self.client.force_login(self.user_without_permission)
response = self.client.get(reverse('catalogue:room-create'))
self.assertEqual(response.status_code, 403)
```

POST valide/invalide :

```python
response = self.client.post(url, valid_data)
self.assertEqual(response.status_code, 302)
self.assertTrue(Room.objects.filter(name='Studio').exists())

response = self.client.post(url, invalid_data)
self.assertEqual(response.status_code, 200)
self.assertContains(response, 'Ce champ est obligatoire')
```

Un POST invalide réaffiche souvent la page avec code 200 ; vérifier les erreurs et l'absence d'insertion.

## Tests d’autorisations

Tester séparément :

```text
anonyme → redirection ou 403 selon le décorateur
utilisateur normal → 403
administrateur/permission exacte → succès
producteur → seulement ses spectacles si règle d'objet
```

Le projet contient déjà des tests de permissions CRUD, rôles métier, modération et API dans `catalogue/tests.py` et `catalogue/tests_api.py`.

## Tests JavaScript / backend JSON

Tester d'abord la route Django :

```python
response = self.client.post(url, {'action': 'approve'})
self.assertEqual(response.status_code, 200)
self.assertEqual(response.json()['status'], 'approved')
```

Checklist navigateur :

```text
[ ] bouton désactivé pendant l'appel
[ ] requête POST visible dans Réseau
[ ] en-tête CSRF présent
[ ] JSON reçu
[ ] DOM mis à jour après succès
[ ] erreur 400/403 affichée
[ ] double clic empêché
```

## Lire un traceback

Lire de bas en haut :

1. **message final** : description immédiate ;
2. **type d'exception** : famille du problème ;
3. **dernier fichier du projet et numéro de ligne** : point de départ ;
4. remonter les appels pour comprendre la donnée transmise.

| Erreur | Cause fréquente | Première vérification |
|---|---|---|
| `ModuleNotFoundError` | dépendance absente ou mauvais Python | `python -m pip --version` |
| `NoReverseMatch` | route/arguments incorrects | `name`, namespace et paramètres |
| `TemplateDoesNotExist` | chemin ou dossier incorrect | nom dans `render()` |
| `IntegrityError` | FK, unique ou check violé | données et contraintes |
| `OperationalError` | base indisponible/table absente | configuration et migrations |
| `KeyError` | clé dict/variable absente | nom et valeur par défaut |
| `FieldError` | champ/lookup ORM incorrect | modèle et `related_name` |
| `RelatedObjectDoesNotExist` | relation one-to-one absente | cardinalité et test préalable |

Ne pas masquer l'exception : conserver le message exact et isoler le plus petit scénario reproductible.

## Dump SQL PostgreSQL

Si `pg_dump` est installé :

```powershell
pg_dump --host=<HOTE> --port=<PORT> --username=<UTILISATEUR> --dbname=<BASE> --format=plain --file=reservations.sql
```

- Remplacer uniquement les marqueurs.
- La commande demandera le mot de passe ou lira une configuration sécurisée ; ne jamais écrire un vrai mot de passe dans la commande ou la fiche.
- `--format=plain` produit du SQL lisible.

## SQLite : copie ou dump SQL

`db.sqlite3` est une base binaire, pas un dump SQL. Une copie du fichier peut suffire seulement si le sujet accepte une base SQLite. Pour produire du SQL si `sqlite3.exe` est installé :

```powershell
sqlite3.exe db.sqlite3 ".dump" | Set-Content -Encoding utf8 reservations_sqlite.sql
```

Le pipe transmet la sortie de `.dump` à PowerShell. Vérifier le fichier généré et les exigences du professeur.

## Archive ZIP

Inclure :

```text
[ ] code Python
[ ] migrations
[ ] fixtures et/ou seeders
[ ] templates
[ ] fichiers statiques
[ ] requirements.txt
[ ] documentation/fiches demandées
[ ] dump SQL si demandé
```

Exclure normalement :

```text
[ ] .venv
[ ] __pycache__ et *.pyc
[ ] .git si non demandé
[ ] .env et secrets
[ ] fichiers temporaires/logs
```

Depuis le dossier parent d'une copie propre :

```powershell
Compress-Archive -Path .\reservations\* -DestinationPath .\reservations-remise.zip
```

Attention : `*` peut omettre certains fichiers cachés, ce qui aide pour `.git/.env` mais peut aussi omettre un fichier caché requis. Préparer d'abord une copie de remise contrôlée est plus sûr que compresser directement le dossier de travail.

## Recette de réinstallation avant remise

Dans un nouveau dossier temporaire :

```powershell
Expand-Archive .\reservations-remise.zip -DestinationPath .\verification
Set-Location .\verification\reservations
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe manage.py migrate
.venv\Scripts\python.exe manage.py create_demo_accounts
.venv\Scripts\python.exe manage.py check
.venv\Scripts\python.exe manage.py test
.venv\Scripts\python.exe manage.py runserver
```

- Utiliser `py -m venv` si Python 3.12 n'est pas installé sous ce libellé mais qu'une version compatible est disponible.
- `create_demo_accounts` appelle déjà le seeder de catalogue dans ce projet.
- Le serveur reste actif jusqu'à `Ctrl+C`.

## Exemples prêts à adapter

Test ciblé :

```powershell
.venv\Scripts\python.exe manage.py test catalogue.tests.CategoryViewTests
```

Remplacer la classe par le chemin du test concerné, puis exécuter toute la suite avant remise.

## Erreurs fréquentes

- Tester seulement que `runserver` démarre.
- Ignorer un test rouge parce que « la page marche ».
- Exécuter avec un autre Python que `.venv`.
- Confondre validateur Python et contrainte de base.
- Mettre un mot de passe dans `pg_dump` ou le ZIP.
- Appeler `db.sqlite3` un dump SQL.
- Inclure `.venv`, `.git` ou `.env`.
- Créer le ZIP sans le réinstaller.
- Oublier migrations, fixtures ou fichiers statiques non suivis par Git.

## Vérifications

```powershell
.venv\Scripts\python.exe manage.py check
.venv\Scripts\python.exe manage.py makemigrations --check
.venv\Scripts\python.exe manage.py showmigrations
.venv\Scripts\python.exe manage.py test
```

Puis ouvrir le ZIP, vérifier son arborescence et refaire l'installation sans réutiliser l'ancien `.venv` ni les secrets locaux.

## Checklist express

```text
[ ] check passe
[ ] aucune migration manquante
[ ] toutes les migrations appliquées
[ ] tests ciblés et complets exécutés
[ ] permissions testées
[ ] JSON testé côté backend et navigateur
[ ] dump conforme au moteur de base
[ ] ZIP sans .venv/.env/.git
[ ] ZIP réinstallé dans un nouveau dossier
[ ] contenu final relu
```
