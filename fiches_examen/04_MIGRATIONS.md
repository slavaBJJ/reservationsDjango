# 04 — Migrations Django

## Quand utiliser cette fiche ?

Après toute création ou modification de modèle, avant d'écrire les vues. Une migration versionne la **structure** de la base ; elle ne transporte ni la base locale ni automatiquement les données métier.

## Étapes dans l’ordre

```text
1. Modifier/créer le modèle
2. Rendre le modèle découvrable
3. check
4. makemigrations
5. Lire le fichier généré
6. migrate
7. Vérifier showmigrations et les données
8. Commiter modèle + migration
```

## Rôle des migrations

```powershell
.venv\Scripts\python.exe manage.py makemigrations
.venv\Scripts\python.exe manage.py migrate
```

- `makemigrations` compare les modèles aux migrations connues et **génère des instructions Python** dans `application/migrations/`.
- `migrate` **applique** les migrations non appliquées à la base sélectionnée dans `settings.py`.
- Une migration appartient au code : je la relis puis je la commite avec le modèle.
- Une migration crée ou transforme le schéma ; elle ne contient pas mon fichier SQLite ni ma base PostgreSQL.
- Les données métier demandent une fixture, un seeder ou une migration de données explicite.

## Commandes essentielles

```powershell
.venv\Scripts\python.exe manage.py check
.venv\Scripts\python.exe manage.py makemigrations catalogue
.venv\Scripts\python.exe manage.py migrate
.venv\Scripts\python.exe manage.py showmigrations
.venv\Scripts\python.exe manage.py makemigrations --check
.venv\Scripts\python.exe manage.py sqlmigrate catalogue <NUMERO>
```

- `check` détecte des erreurs de configuration, champs et relations sans modifier la base.
- `makemigrations catalogue` crée les migrations de l'application `catalogue`.
- `migrate` applique les migrations dans l'ordre de leurs dépendances.
- `showmigrations` affiche le plan ; `[X]` signifie appliquée, `[ ]` signifie non appliquée.
- `makemigrations --check` renvoie un échec si les modèles nécessitent encore une migration. À utiliser lorsque les migrations attendues existent déjà.
- `sqlmigrate catalogue <NUMERO>` affiche le SQL d'une migration, par exemple remplacer `<NUMERO>` par `0025`.

## Lire une migration

```python
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('catalogue', '0025_alter_show_category'),
    ]
    operations = [
        migrations.AddField(
            model_name='show',
            name='example',
            field=models.CharField(max_length=60, null=True),
        ),
    ]
```

- L'import fournit les opérations et champs historiques.
- `dependencies` impose ce qui doit être appliqué avant cette migration.
- `operations` est la liste ordonnée des transformations.
- `AddField` ajoute ici une colonne temporairement nullable.

Opérations à reconnaître :

- `migrations.CreateModel` : crée une table et ses champs.
- `migrations.AddField` : ajoute un champ/une relation.
- `migrations.RemoveField` : supprime une colonne et potentiellement ses données.
- `migrations.AlterField` : change la définition d'un champ.
- `migrations.AddConstraint` : ajoute une contrainte nommée.

## Ajouter une table simple

```text
Créer le modèle
→ l’importer dans catalogue/models/__init__.py
→ check
→ makemigrations catalogue
→ lire la migration
→ migrate
→ vérifier avec showmigrations
```

Dans ce projet, les modèles sont séparés dans `catalogue/models/`. Un nouveau `Room` doit être exposé par `catalogue/models/__init__.py`, idéalement avec `from .room import Room`.

## Ajouter un champ facultatif

```python
room = models.ForeignKey(
    'Room',
    on_delete=models.PROTECT,
    null=True,
    blank=True,
)
```

- `null=True` permet aux anciennes lignes de rester provisoirement sans salle.
- `blank=True` rend le champ facultatif dans la validation Django.
- Après remplissage des données, une migration suivante peut retirer ces options si la relation devient obligatoire.

## Ajouter un champ obligatoire

Trois stratégies :

1. **Valeur ponctuelle proposée par Django** : convient seulement si une même valeur existante est correcte pour toutes les anciennes lignes. Elle ne devient pas forcément le défaut futur.
2. **`default` dans le modèle** : convient si une vraie valeur métier par défaut doit aussi s'appliquer aux créations futures. Éviter un faux objet « par défaut » uniquement pour satisfaire la migration.
3. **Plusieurs étapes et migration de données** : recommandée quand la valeur dépend de chaque ligne : ajouter nullable, convertir, vérifier, rendre obligatoire.

## Migration de données

```python
def forwards(apps, schema_editor):
    Model = apps.get_model('application', 'Model')
    Model.objects.filter(example__isnull=True).update(example='valeur')


class Migration(migrations.Migration):
    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
```

- `apps.get_model()` récupère la **version historique** du modèle correspondant à cette migration.
- Importer le modèle courant pourrait casser une ancienne migration après de futures modifications.
- `schema_editor` représente l'éditeur de schéma, même s'il n'est pas utilisé ici.
- `RunPython` exécute `forwards` à l'aller.
- `migrations.RunPython.noop` rend le retour structurellement possible sans annuler les données ; pour une vraie réversibilité, écrire une fonction inverse.

**À renommer :** `application`, `Model`, `example`, la valeur et les dépendances.

## Remplacer une relation existante

Cas Réservations :

```text
Representation.location
→ création de Room
→ Representation.room
→ suppression de Representation.location
```

Ordre sûr :

1. créer `Room` avec sa relation vers `Location` ;
2. ajouter `Representation.room` temporairement nullable ;
3. créer ou retrouver une salle pour chaque lieu existant ;
4. affecter une salle à chaque représentation avec une migration de données ;
5. vérifier qu'aucune représentation n'a `room=None` ;
6. rendre `room` obligatoire ;
7. supprimer seulement alors `location`.

Ne pas fusionner aveuglément ces étapes : conserver la donnée source jusqu'à validation de la conversion.

## Corriger une migration déjà appliquée

Une migration partagée/appliquée représente l'historique. Je corrige normalement le **modèle**, puis je génère une **nouvelle migration**.

```python
blank='True'  # valeur historique incorrecte : chaîne
blank=True    # valeur correcte : booléen
```

Le projet possède précisément ce cas : `0024` contient la chaîne, puis `0025` corrige le champ. Ne pas réécrire `0024` sur une branche déjà utilisée.

## Retour en arrière

```powershell
.venv\Scripts\python.exe manage.py migrate catalogue <MIGRATION_PRECEDENTE>
```

Cette commande ramène l'application à l'état indiqué. Elle peut supprimer des tables/colonnes et donc des données. Vérifier d'abord le plan, sauvegarder la base et lire les opérations. Une `RunPython` sans fonction inverse peut rendre une migration irréversible.

## Fusion de migrations

Deux branches peuvent créer deux migrations ayant la même dépendance finale. Après fusion Git, Django voit deux feuilles concurrentes et peut proposer une migration de fusion. Vérifier que les opérations ne se contredisent pas avant `makemigrations --merge`, puis commiter le fichier de fusion.

## Exemples prêts à adapter

```powershell
# Après ajout de catalogue/models/video.py et de son import
.venv\Scripts\python.exe manage.py check
.venv\Scripts\python.exe manage.py makemigrations catalogue
.venv\Scripts\python.exe manage.py sqlmigrate catalogue <NOUVEAU_NUMERO>
.venv\Scripts\python.exe manage.py migrate
.venv\Scripts\python.exe manage.py showmigrations catalogue
```

Remplacer `<NOUVEAU_NUMERO>` par le numéro généré. Les lignes commençant par `#` sont des commentaires PowerShell.

## Erreurs fréquentes

- Modifier manuellement la base sans migration : les autres installations ne reproduisent pas le changement.
- Oublier de commiter la migration avec le modèle.
- Supprimer une migration déjà appliquée ou partagée.
- Ajouter une FK obligatoire sans traiter les lignes existantes.
- Confondre `makemigrations` (génère) et `migrate` (applique).
- Modifier une ancienne migration partagée au lieu d'en créer une nouvelle.
- Déclarer une mauvaise dépendance ou appliquer un ordre incohérent.
- Croire que `migrate` charge les fixtures.
- Accepter une valeur ponctuelle arbitraire sans vérifier les données.

## Vérifications

```powershell
.venv\Scripts\python.exe manage.py check
.venv\Scripts\python.exe manage.py makemigrations --check
.venv\Scripts\python.exe manage.py showmigrations catalogue
```

Puis inspecter le fichier créé avec Git avant commit. Cette fiche ne demande d'exécuter aucune migration sur le projet actuel.

## Checklist express

```text
[ ] Modèle importé et valide
[ ] check réussi
[ ] Migration générée
[ ] Dépendances vérifiées
[ ] Opérations relues
[ ] Données existantes prises en compte
[ ] migrate réussi sur la bonne base
[ ] [X] visible dans showmigrations
[ ] Modèle et migration prêts à être commités ensemble
```
