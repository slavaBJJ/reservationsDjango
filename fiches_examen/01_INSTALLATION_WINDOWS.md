# Fiche 01 — Installer un projet Django sur Windows

> Objectif : récupérer un projet Django sur un nouvel ordinateur Windows,
> recréer son environnement et le démarrer rapidement.

Cette fiche utilise principalement **PowerShell**. Les commandes Django appellent
directement `.venv\Scripts\python.exe` : il n'est donc pas nécessaire d'activer
l'environnement virtuel.

## 1. Vérifications avant l'examen

### Checklist du dépôt

```text
[ ] Le code source est présent
[ ] requirements.txt est présent et à jour
[ ] Toutes les migrations sont enregistrées
[ ] Les fixtures ou commandes de seed sont présentes
[ ] .env.example est présent si une configuration est nécessaire
[ ] Aucune dépendance n'existe uniquement dans .venv
[ ] Aucune modification utile ne reste non commitée
[ ] La branche d'examen existe sur GitHub
[ ] Aucun secret réel n'est suivi par Git
```

### Contrôles Git

```powershell
git status
git branch
git remote -v
git log -1 --oneline
```

| Commande | Utilité |
|---|---|
| `git status` | Affiche les fichiers modifiés, indexés ou non suivis. |
| `git branch` | Affiche les branches locales et marque la branche active avec `*`. |
| `git remote -v` | Affiche les adresses du dépôt distant. |
| `git log -1 --oneline` | Affiche le dernier commit local. |

### Enregistrement, index, commit et push

| État | Signification |
|---|---|
| Fichier enregistré | Le fichier existe sur le disque, mais Git ne l'a pas forcément pris en compte. |
| `git add` effectué | La version actuelle est placée dans l'index pour le prochain commit. |
| Commit local | Un instantané est enregistré dans le dépôt de l'ordinateur. |
| Commit poussé | Le commit a été envoyé sur GitHub avec `git push`. |

Un commit local n'est pas automatiquement disponible sur GitHub.

## 2. Vérifier les outils sur Windows

```powershell
py --version
git --version
```

- `py --version` affiche la version Python choisie par le lanceur Windows.
- `git --version` confirme que Git est installé et accessible dans le terminal.

Pour voir toutes les versions Python détectées :

```powershell
py --list
```

| Résultat | Diagnostic |
|---|---|
| `py is not recognized` | Python ou le lanceur `py` est absent du PATH. |
| `git is not recognized` | Git est absent du PATH. |
| Plusieurs versions sont affichées | Utiliser `py -3.12` pour imposer Python 3.12. |
| Une commande est inconnue | Vérifier l'installation, fermer puis rouvrir le terminal. |

### Version du projet Réservations

Le projet utilise **Python 3.12** et **Django 5.2.8**. Utiliser Python 3.12 pour
rester cohérent avec les dépendances et la documentation.

## 3. Récupérer le projet avec Git

### Procédure générique

```powershell
git clone <URL_HTTPS_DU_DEPOT>
cd <DOSSIER_DU_PROJET>
git switch <NOM_DE_BRANCHE>
```

- `git clone` télécharge le dépôt et son historique.
- `cd` entre dans le dossier téléchargé.
- `git switch` sélectionne la branche à utiliser.

Préférer une URL **HTTPS** sur l'ordinateur de l'examen : une URL SSH comme
`git@github.com:...` nécessite une clé SSH personnelle déjà configurée.

### Vérifier ou retrouver une branche

```powershell
git branch --show-current
git branch -a
git fetch --all
git branch -a
```

- `git branch --show-current` affiche la branche active.
- `git branch -a` affiche les branches locales et distantes connues.
- `git fetch --all` actualise les références distantes sans modifier le code.

Si la branche apparaît sous `remotes/origin/<NOM_DE_BRANCHE>`, créer la branche
locale avec :

```powershell
git switch --track origin/<NOM_DE_BRANCHE>
```

### Exemple Réservations

La branche `categorie_prépa_exam` existe actuellement sur le dépôt distant :

```powershell
git clone https://github.com/slavaBJJ/reservationsDjango.git
cd reservationsDjango
git switch categorie_prépa_exam
git branch --show-current
```

## 4. Récupérer le projet sans Git

Solution de secours avec une archive ZIP :

1. Ouvrir `<URL_DU_DEPOT>` dans le navigateur.
2. Sélectionner `<NOM_DE_BRANCHE>` dans la liste des branches.
3. Cliquer sur **Code → Download ZIP**.
4. Enregistrer puis extraire complètement l'archive.
5. Ouvrir PowerShell dans le dossier extrait contenant `manage.py`.

Ne jamais exécuter le projet directement depuis l'intérieur du ZIP : Python ne
pourra pas créer correctement `.venv`, `db.sqlite3` et les fichiers temporaires.

Exemple : après extraction, le dossier peut s'appeler
`reservationsDjango-categorie_prépa_exam`.

## 5. Identifier la racine Django

Les commandes doivent être exécutées dans le dossier contenant :

```text
manage.py
requirements.txt
catalogue/
reservations/
```

Afficher le contenu du dossier courant :

```powershell
Get-ChildItem
```

Si `manage.py` n'est pas affiché, entrer dans le sous-dossier approprié :

```powershell
cd <SOUS_DOSSIER_CONTENANT_MANAGE_PY>
```

Erreur typique :

```text
python: can't open file 'manage.py': [Errno 2] No such file or directory
```

Cause : la commande est lancée depuis le mauvais dossier. Utiliser
`Get-ChildItem`, puis rejoindre la véritable racine Django avec `cd`.

## 6. Créer l'environnement virtuel

```powershell
py -3.12 -m venv .venv
```

Cette commande crée un environnement Python 3.12 isolé dans `.venv`.

- `.venv` sépare les dépendances du projet des paquets installés globalement.
- Un `.venv` créé sur macOS contient des exécutables incompatibles avec Windows.
- Il doit être recréé sur chaque ordinateur à partir de `requirements.txt`.
- Il ne doit normalement pas être envoyé sur GitHub.

### Méthode A — avec activation

```powershell
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

- `Activate.ps1` place temporairement le Python de `.venv` en tête du PATH.
- La première commande `pip` met l'outil d'installation à jour.
- La deuxième installe les dépendances du projet.

Quitter ensuite l'environnement avec :

```powershell
deactivate
```

### Méthode B — sans activation, recommandée

```powershell
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Le chemin explicite garantit que `pip` appartient au bon environnement, même si
un autre Python est actif dans le terminal.

### Blocage `ExecutionPolicy`

Si PowerShell refuse `Activate.ps1`, ne pas modifier inutilement la politique de
tout l'ordinateur. Deux solutions sûres :

1. utiliser directement la méthode B, sans activation ;
2. autoriser les scripts uniquement dans la fenêtre actuelle :

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
```

`-Scope Process` limite le changement à la session PowerShell actuelle. La
politique précédente est retrouvée à la fermeture du terminal.

## 7. Comprendre `requirements.txt`

`requirements.txt` décrit les paquets nécessaires à l'application.

- `Django==5.2.8` signifie : installer exactement la version 5.2.8.
- `==` améliore la reproductibilité entre deux ordinateurs.
- Copier `.venv` est incorrect : ses exécutables dépendent du système et du
  chemin où il a été créé.

### Erreurs typiques

```text
ModuleNotFoundError: No module named 'django'
ModuleNotFoundError: No module named 'rest_framework'
ModuleNotFoundError: No module named 'dj_database_url'
```

Deux causes principales :

1. la dépendance n'a pas été installée ;
2. la commande utilise le mauvais Python.

### Diagnostic

```powershell
.venv\Scripts\python.exe -m pip --version
.venv\Scripts\python.exe -m pip list
.venv\Scripts\python.exe -c "import django; print(django.get_version())"
```

- La première commande doit afficher un chemin situé dans `.venv`.
- La deuxième liste les paquets réellement installés.
- La troisième confirme que Django est importable et affiche sa version.

## 8. Configuration locale et `.env`

Un fichier `.env` contient des variables locales : clé Django, choix de base,
identifiants ou réglages de sécurité. Il est généralement ignoré par Git pour
éviter la publication de secrets.

`.env.example` est un modèle sans secret. Il documente les noms des variables à
configurer. Render fournit ses propres variables depuis son interface et sa
configuration d'hébergement : elles ne proviennent pas du `.env` local.

### Variables importantes

| Variable | Rôle |
|---|---|
| `DJANGO_SECRET_KEY` | Signe les sessions, jetons et données sensibles de Django. |
| `DJANGO_DEBUG` | Active ou désactive les informations détaillées de débogage. |
| `DATABASE_URL` | Décrit une connexion complète à une base, notamment sur Render. |
| `POSTGRES_*` | Décrit séparément une connexion PostgreSQL locale. |

Une clé locale de démonstration est connue et non sécurisée. Elle ne doit jamais
être utilisée en production.

### Projet exigeant un `.env`

Procédure générique :

```powershell
Copy-Item .env.example .env
notepad .env
```

- `Copy-Item` crée la configuration locale depuis l'exemple.
- `notepad` ouvre le fichier pour compléter uniquement des valeurs fictives ou
  des secrets locaux.

Exemple fictif :

```dotenv
DJANGO_SECRET_KEY=cle-locale-fictive-ne-pas-utiliser-en-production
DJANGO_DEBUG=True
```

Dans l'Explorateur Windows, afficher les extensions de fichiers. Un fichier
nommé `.env.txt` n'est pas chargé comme `.env`.

### Cas réel du projet Réservations

En local, le projet fonctionne **sans `.env`** :

- clé de développement non sécurisée fournie automatiquement ;
- `DEBUG=True` par défaut hors Render ;
- `localhost` et `127.0.0.1` autorisés ;
- SQLite sélectionné si aucune configuration PostgreSQL n'est présente.

Il ne faut donc pas créer de `.env` pour l'installation rapide de l'examen.

## 9. Choisir la base de données

### SQLite pour un examen local

- aucun serveur séparé à installer ;
- données stockées dans `db.sqlite3` ;
- structure reconstruite avec les migrations ;
- adapté à une démonstration locale rapide.

### PostgreSQL

- nécessite un serveur PostgreSQL accessible ;
- nécessite une base, un utilisateur, un mot de passe, un hôte et un port ;
- utilise généralement `POSTGRES_*` ou `DATABASE_URL` ;
- peut faire perdre du temps si le serveur n'est pas préparé sur le PC.

### Priorité réelle dans Réservations

```text
1. DATABASE_URL si elle existe
2. PostgreSQL si DJANGO_DATABASE=postgresql ou si POSTGRES_* est configuré
3. SQLite dans db.sqlite3 dans les autres cas
```

Pour l'examen, ne pas définir `DATABASE_URL`, `DJANGO_DATABASE` ou
`POSTGRES_*`. Le projet choisira SQLite automatiquement.

## 10. Créer la structure de la base

```powershell
.venv\Scripts\python.exe manage.py migrate
```

`migrate` exécute les migrations enregistrées et crée ou met à jour les tables.

### Différence entre les deux commandes

```powershell
.venv\Scripts\python.exe manage.py makemigrations
.venv\Scripts\python.exe manage.py migrate
```

- `makemigrations` fabrique des fichiers de migration après un changement de
  modèle ;
- `migrate` applique les fichiers de migration à la base.

Lors d'une installation neuve, les migrations doivent déjà être dans Git : on
exécute normalement `migrate`, pas `makemigrations`.

### Contrôles

```powershell
.venv\Scripts\python.exe manage.py showmigrations
.venv\Scripts\python.exe manage.py makemigrations --check
```

- `[X]` signifie que la migration est appliquée dans la base actuelle.
- `[ ]` signifie qu'elle reste à appliquer.
- `makemigrations --check` vérifie qu'aucun changement de modèle n'est oublié.

## 11. Charger les données de démonstration

### Fixture

Une fixture est un fichier JSON contenant des objets Django :

```powershell
.venv\Scripts\python.exe manage.py loaddata <FIXTURE>
```

Exemple réel sans mot de passe :

```powershell
.venv\Scripts\python.exe manage.py loaddata categories
```

Les fixtures liées par des clés étrangères doivent être chargées dans le bon
ordre. Le dépôt contient notamment des localités, lieux, types, artistes,
catégories, tarifs, spectacles, représentations, réservations et avis.

Ordre logique si un chargement manuel complet est réellement nécessaire :

```text
1. auth_user puis user_meta
2. localities puis locations
3. types, ArtistFixtures puis artist_type
4. categories et prices
5. shows
6. price_show et artist_type_shows
7. representations
8. reservations puis representation_reservations
9. reviews
```

Ce chargement manuel est plus fragile et peut provoquer des doublons ou des
conflits de clés primaires si les données existent déjà.

### Seeder Django

Un seeder est généralement une commande personnalisée qui crée les données par
du code :

```powershell
.venv\Scripts\python.exe manage.py <COMMANDE_SEEDER>
```

`get_or_create()` réutilise un objet existant ou le crée. `update_or_create()`
le crée ou actualise ses valeurs. Ces méthodes rendent un seeder plus sûr à
relancer qu'une série de fixtures avec des clés fixes.

### Ordre recommandé pour Réservations

```powershell
.venv\Scripts\python.exe manage.py create_demo_accounts
```

Cette commande :

- crée les comptes et groupes locaux de démonstration ;
- appelle automatiquement `seed_demo_catalogue` ;
- crée les catégories, lieux, tarifs, spectacles et représentations ;
- crée les réservations passées nécessaires aux avis ;
- peut être relancée sans recréer les mêmes spectacles.

Ne pas exécuter ensuite `seed_demo_catalogue` : ce serait inutile. Pour créer
uniquement le catalogue sans les comptes, utiliser à la place :

```powershell
.venv\Scripts\python.exe manage.py seed_demo_catalogue
```

| Type de données | Usage |
|---|---|
| Données locales | Manipulations personnelles dans `db.sqlite3`. |
| Données de test | Créées dans une base temporaire par `manage.py test`. |
| Données de démonstration | Créées pour présenter les fonctionnalités à l'examen. |

Ne pas utiliser `create_demo_accounts` sur Render : la commande refuse de
s'exécuter lorsque `DEBUG=False`.

## 12. Vérifier le projet

```powershell
.venv\Scripts\python.exe manage.py check
.venv\Scripts\python.exe manage.py test
```

- `check` inspecte la configuration Django, les modèles, les URLs et plusieurs
  incohérences structurelles ;
- `test` exécute les scénarios automatisés et utilise une base de test séparée.

Un serveur qui démarre prouve seulement que Django peut se lancer. Il ne garantit
pas que l'inscription, les réservations, les permissions ou l'API fonctionnent.
Un test en échec doit être lu : relever le premier message `FAIL` ou `ERROR`, le
nom du test et la dernière exception. Ne jamais masquer l'échec.

Commande ciblée validée pour Réservations :

```powershell
.venv\Scripts\python.exe manage.py test accounts.tests catalogue.tests catalogue.tests_api --settings=reservations.test_settings
```

## 13. Démarrer le serveur

```powershell
.venv\Scripts\python.exe manage.py runserver
```

Ouvrir ensuite :

```text
http://127.0.0.1:8000/
```

- le terminal doit rester ouvert pendant l'utilisation du site ;
- arrêter le serveur avec `Ctrl + C` ;
- ne pas ouvrir un template avec `file:///...` : les balises Django nécessitent
  le serveur, le routage et le contexte de l'application.

## 14. Erreurs fréquentes

| Erreur | Cause probable | Vérification rapide | Correction courte |
|---|---|---|---|
| `git is not recognized` | Git absent du PATH. | `git --version` | Installer Git puis rouvrir PowerShell. |
| `py is not recognized` | Python ou le lanceur absent. | Rechercher Python dans les applications. | Installer Python 3.12 avec le lanceur `py`. |
| `manage.py not found` | Mauvais dossier courant. | `Get-ChildItem` | Entrer dans le dossier contenant `manage.py`. |
| `No module named ...` | Paquet absent ou mauvais Python. | `.venv\Scripts\python.exe -m pip list` | Réinstaller `requirements.txt` avec le Python explicite. |
| `KeyError: DJANGO_SECRET_KEY` | Clé exigée mais absente. | Examiner `settings.py` et `.env`. | Créer `.env` si le projet l'exige; Réservations n'en exige pas en local. |
| Connexion PostgreSQL refusée | Variables PostgreSQL actives ou serveur arrêté. | Vérifier `.env` et `$Env:DATABASE_URL`. | Pour l'examen, retirer ces variables et utiliser SQLite. |
| Migrations non appliquées | `migrate` n'a pas été exécuté. | `manage.py showmigrations` | Exécuter `manage.py migrate`. |
| `no such table` / table inexistante | Base vide ou migration absente. | `showmigrations` | Vérifier la branche puis lancer `migrate`. |
| Port 8000 occupé | Un autre serveur utilise le port. | Regarder les terminaux ouverts. | Arrêter l'autre serveur ou utiliser `runserver 8001`. |
| Mauvaise branche Git | Branche attendue non active. | `git branch --show-current` | `git fetch --all`, puis `git switch <NOM_DE_BRANCHE>`. |
| `.env.txt` au lieu de `.env` | Windows a masqué l'extension. | `Get-ChildItem -Force` | Afficher les extensions et renommer le fichier. |

### Diagnostic minimal

```powershell
Get-Location
Get-ChildItem -Force
git branch --show-current
.venv\Scripts\python.exe --version
.venv\Scripts\python.exe -m pip check
.venv\Scripts\python.exe manage.py check
```

## 15. Procédure express

### A. Installation avec Git

```powershell
# 1. Télécharger et sélectionner la branche
git clone <URL_HTTPS_DU_DEPOT>
cd <DOSSIER_DU_PROJET>
git switch <NOM_DE_BRANCHE>

# 2. Créer Python localement et installer les dépendances
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt

# 3. Préparer et contrôler l'application
.venv\Scripts\python.exe manage.py migrate
.venv\Scripts\python.exe manage.py <COMMANDE_DE_DONNEES>
.venv\Scripts\python.exe manage.py check

# 4. Démarrer
.venv\Scripts\python.exe manage.py runserver
```

Exemple Réservations :

```powershell
git clone https://github.com/slavaBJJ/reservationsDjango.git
cd reservationsDjango
git switch categorie_prépa_exam
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe manage.py migrate
.venv\Scripts\python.exe manage.py create_demo_accounts
.venv\Scripts\python.exe manage.py check
.venv\Scripts\python.exe manage.py runserver
```

### B. Installation depuis un ZIP

```powershell
# Après téléchargement et extraction complète du ZIP
cd <DOSSIER_EXTRAIT_CONTENANT_MANAGE_PY>
Get-ChildItem
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe manage.py migrate
.venv\Scripts\python.exe manage.py <COMMANDE_DE_DONNEES>
.venv\Scripts\python.exe manage.py check
.venv\Scripts\python.exe manage.py runserver
```

Pour Réservations, remplacer `<COMMANDE_DE_DONNEES>` par
`create_demo_accounts`.

## 16. Checklist finale

```text
[ ] Bonne branche récupérée
[ ] manage.py trouvé
[ ] .venv créé
[ ] Dépendances installées
[ ] Configuration locale correcte
[ ] Migrations appliquées
[ ] Données injectées
[ ] Django check réussi
[ ] Tests examinés
[ ] Serveur démarré
[ ] Pages principales vérifiées
```

### Pages Réservations à contrôler rapidement

```text
http://127.0.0.1:8000/
http://127.0.0.1:8000/accounts/login/
http://127.0.0.1:8000/catalogue/show/
http://127.0.0.1:8000/catalogue/category/
http://127.0.0.1:8000/catalogue/api/docs/
http://127.0.0.1:8000/catalogue/rss/representations/
http://127.0.0.1:8000/admin/
```
