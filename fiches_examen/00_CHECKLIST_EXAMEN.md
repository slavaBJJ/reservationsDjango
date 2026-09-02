# 00 — Checklist de l’examen

## Quand utiliser cette fiche ?

Pendant tout l'examen comme tableau de bord. Ouvrir la fiche détaillée indiquée si une étape bloque.

## Avant de coder

```text
[ ] Lire toutes les fonctionnalités
[ ] Identifier les modèles concernés
[ ] Déterminer les cardinalités
[ ] Identifier les champs et contraintes
[ ] Repérer les données existantes à convertir
[ ] Identifier les permissions
[ ] Identifier la route paramétrée
```

Relations : `02_ANALYSER_RELATIONS.md` — modèles : `03_MODELES_DJANGO.md`.

## Étapes dans l’ordre

```text
1. Créer/modifier les modèles
2. Vérifier avec check
3. Créer les migrations
4. Lire les migrations
5. Appliquer les migrations
6. Créer les données de test
7. Créer le formulaire
8. Créer les vues
9. Créer les routes
10. Créer les templates
11. Ajouter les autorisations
12. Ajouter JavaScript si demandé
13. Tester
14. Créer le dump SQL
15. Créer le ZIP
```

Références : `04_MIGRATIONS.md` à `12_TESTS_DEBUG_DUMP_ET_ZIP.md`.

## Commandes express Windows PowerShell

```powershell
# Vérifier l'environnement
.venv\Scripts\python.exe --version
.venv\Scripts\python.exe -m pip install -r requirements.txt

# Vérifier et migrer
.venv\Scripts\python.exe manage.py check
.venv\Scripts\python.exe manage.py makemigrations catalogue
.venv\Scripts\python.exe manage.py migrate
.venv\Scripts\python.exe manage.py showmigrations
.venv\Scripts\python.exe manage.py makemigrations --check

# Données locales de démonstration
.venv\Scripts\python.exe manage.py create_demo_accounts

# Tests et serveur
.venv\Scripts\python.exe manage.py test
.venv\Scripts\python.exe manage.py runserver
```

`create_demo_accounts` appelle déjà `seed_demo_catalogue` dans ce projet. Ne pas relancer inutilement les deux. `makemigrations` crée du code ; relire le fichier avant `migrate`.

## Vérification par critère

| Critère | Contrôle rapide | Fiche |
|---|---|---|
| Nouvelle table | modèle importé, migration `CreateModel` | `03`, `04` |
| Mapping | bon champ, bon côté, `related_name`, `on_delete` | `02`, `03` |
| Données de test | fixture valide ou seeder idempotent | `05` |
| Liste déroulante | `ModelChoiceField`, queryset filtré | `09` |
| Vue personnalisée | ORM, contexte, cas vide/404 | `06` |
| Template personnalisé | variables, `{% empty %}`, URLs | `08` |
| Route paramétrée | convertisseur et argument identiques | `07` |
| Permission administrateur | backend + affichage | `10` |
| Traitement asynchrone | CSRF, JSON, erreur, DOM | `11` |
| Tests | modèles, vues, profils, route JSON | `12` |
| Dump | moteur correct, aucun secret | `12` |
| ZIP | contenu complet, `.venv/.env` exclus | `12` |

## Contrôle de sécurité

```text
[ ] Le formulaire est caché si nécessaire
[ ] La vue est également protégée
[ ] Les modifications utilisent POST/PATCH/DELETE
[ ] CSRF présent
[ ] Contraintes métier vérifiées côté backend
```

Ne pas confondre : authentification = identité ; autorisation = droit. `is_staff`, `is_superuser`, permissions et rôles métier ne sont pas équivalents.

## Exemples prêts à adapter

Patron minimal d'une fonctionnalité :

```text
Phrase métier
→ modèle + contrainte
→ migration relue
→ données idempotentes
→ ModelForm
→ vue protégée
→ route nommée
→ template avec cas vide
→ tests anonyme/normal/admin
```

À renommer systématiquement : modèle, table, champs, `related_name`, contrainte, permission, route, paramètres, template et clés de contexte.

## Erreurs fréquentes

- Coder avant d'avoir fixé les cardinalités.
- Modifier une ancienne migration partagée.
- Oublier d'importer un modèle séparé.
- Charger les données avant les migrations.
- Confondre GET et modification POST.
- Cacher une action sans protéger la vue.
- Oublier CSRF ou une contrainte de base.
- Tester seulement comme superutilisateur.
- Oublier un fichier non suivi dans le ZIP.

## Vérifications finales

```text
[ ] manage.py check passe
[ ] aucune migration manquante
[ ] serveur démarre
[ ] pages principales testées
[ ] utilisateur normal refusé
[ ] administrateur autorisé
[ ] données visibles
[ ] fichier requirements présent
[ ] aucun secret dans le ZIP
[ ] dump SQL présent
```

## Checklist express

```text
[ ] Sujet entièrement relu
[ ] Structure + données prêtes
[ ] GET ne modifie rien
[ ] Permissions backend testées
[ ] Cas vide et erreurs affichés
[ ] Tests passés ou échecs expliqués
[ ] Dump et ZIP contrôlés
[ ] Réinstallation propre effectuée
```
