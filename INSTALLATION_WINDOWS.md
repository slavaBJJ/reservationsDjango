# Installation locale du projet Réservations sur Windows

Ce guide explique comment installer le projet sur un nouvel ordinateur Windows
à partir du dépôt GitHub. L'installation locale utilise SQLite par défaut. Elle
ne dépend donc ni de la base PostgreSQL utilisée pendant le développement, ni de
l'environnement virtuel présent sur un autre ordinateur.

## 1. Prérequis

Installer les logiciels suivants avant l'examen :

- Git pour Windows : <https://git-scm.com/download/win> ;
- Python 3.12 : <https://www.python.org/downloads/> ;
- un navigateur récent, par exemple Firefox, Chrome ou Edge ;
- facultatif : PyCharm ou Visual Studio Code.

Pendant l'installation de Python, cocher l'option **Add Python to PATH**. La
commande suivante permet ensuite de vérifier que Python 3.12 est disponible :

```powershell
py -3.12 --version
```

Le résultat attendu commence par `Python 3.12`.

## 2. Télécharger le projet

Le guide prend en charge **PowerShell** et **Git Bash**. Les commandes Git sont
identiques dans les deux terminaux. Seul le chemin vers Python dans `.venv`
change selon le terminal.

Ouvrir PowerShell ou Git Bash puis exécuter :

```text
git clone https://github.com/slavaBJJ/reservationsDjango.git
cd reservationsDjango
git switch categorie_prépa_exam
```

Explications :

- `git clone` télécharge une copie complète du dépôt GitHub ;
- `cd reservationsDjango` ouvre le dossier qui contient `manage.py` ;
- `git switch categorie_prépa_exam` sélectionne la branche préparée pour
  l'examen.

La branche `categorie_prépa_exam` doit avoir été poussée sur GitHub avant de
réaliser cette installation. Pour vérifier la branche active :

```text
git branch --show-current
```

## 3. Créer l'environnement virtuel

Créer un environnement Python propre dans le dossier du projet :

```text
py -3.12 -m venv .venv
```

Cette commande crée `.venv` avec Python 3.12. Ce dossier contient uniquement
les dépendances de cette installation et n'est pas envoyé sur GitHub.

Il n'est pas obligatoire d'activer l'environnement virtuel. Pour éviter toute
confusion avec un autre Python installé sur l'ordinateur, les commandes de ce
guide appellent directement son interpréteur.

Dans **PowerShell**, utiliser les antislashs Windows :

```powershell
.venv\Scripts\python.exe --version
```

Dans **Git Bash**, utiliser des barres obliques et commencer le chemin par
`./` :

```bash
./.venv/Scripts/python.exe --version
```

Si Git Bash affiche `bash: .venvScriptspython.exe: command not found`, cela
signifie qu'une commande PowerShell avec des antislashs a été exécutée dans
Bash. La commande Git Bash ci-dessus corrige le problème.

Le chemin affiché doit correspondre au dossier `.venv` du projet.

## 4. Installer les dépendances

Mettre `pip` à jour puis installer les versions définies dans
`requirements.txt`.

Dans **PowerShell** :

```powershell
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Dans **Git Bash** :

```bash
./.venv/Scripts/python.exe -m pip install --upgrade pip
./.venv/Scripts/python.exe -m pip install -r requirements.txt
```

La première commande met à jour l'outil d'installation dans l'environnement
virtuel. La deuxième installe Django, Django REST Framework, SimpleJWT, le pilote
PostgreSQL, WhiteNoise, Gunicorn et les autres dépendances nécessaires.

Vérifier ensuite leur cohérence.

Dans **PowerShell** :

```powershell
.venv\Scripts\python.exe -m pip check
```

Dans **Git Bash** :

```bash
./.venv/Scripts/python.exe -m pip check
```

Le résultat attendu est `No broken requirements found`.

## 5. Configuration locale automatique

Aucun fichier `.env` n'est nécessaire pour l'examen. En son absence, le projet
applique automatiquement la configuration locale suivante :

- `DEBUG=True` ;
- une clé Django locale, publique et non sécurisée ;
- SQLite comme moteur de base de données ;
- base enregistrée dans `db.sqlite3`, à côté de `manage.py` ;
- accès autorisé depuis `localhost` et `127.0.0.1`.

Cette configuration est réservée au développement local. Sur Render, la clé
secrète reste obligatoire, `DEBUG=True` est refusé et `DATABASE_URL` sélectionne
PostgreSQL.

## 6. Créer la base SQLite

Appliquer toutes les migrations :

Dans **PowerShell** :

```powershell
.venv\Scripts\python.exe manage.py migrate
```

Dans **Git Bash** :

```bash
./.venv/Scripts/python.exe manage.py migrate
```

Cette commande crée automatiquement `db.sqlite3` et toutes les tables du projet.
Il n'est pas nécessaire d'installer PostgreSQL pour cette procédure.

Contrôler l'état des migrations :

Dans **PowerShell** :

```powershell
.venv\Scripts\python.exe manage.py showmigrations
.venv\Scripts\python.exe manage.py makemigrations --check
```

Dans **Git Bash** :

```bash
./.venv/Scripts/python.exe manage.py showmigrations
./.venv/Scripts/python.exe manage.py makemigrations --check
```

Dans `showmigrations`, les migrations appliquées sont précédées de `[X]`.
`makemigrations --check` doit afficher `No changes detected`.

## 7. Créer les données de démonstration

Exécuter :

Dans **PowerShell** :

```powershell
.venv\Scripts\python.exe manage.py create_demo_accounts
```

Dans **Git Bash** :

```bash
./.venv/Scripts/python.exe manage.py create_demo_accounts
```

Cette commande réalise automatiquement les opérations suivantes :

- création ou mise à jour des sept comptes de démonstration ;
- création des rôles Django ;
- création des trois catégories ;
- création des sept spectacles et de leurs représentations ;
- création des tarifs ;
- création des réservations passées permettant de tester les avis ;
- association du producteur aux spectacles.

Lors de la première exécution, le mot de passe temporaire de `demo_admin` est
affiché dans le terminal. Il faut le noter sans l'ajouter au dépôt Git.

La commande appelle déjà `seed_demo_catalogue`. Il ne faut donc pas lancer les
deux commandes pendant une installation normale. Pour créer uniquement le
catalogue, sans créer les comptes, utiliser :

Dans **PowerShell** :

```powershell
.venv\Scripts\python.exe manage.py seed_demo_catalogue
```

Dans **Git Bash** :

```bash
./.venv/Scripts/python.exe manage.py seed_demo_catalogue
```

## 8. Vérifier le projet

Exécuter le contrôle Django :

Dans **PowerShell** :

```powershell
.venv\Scripts\python.exe manage.py check
```

Dans **Git Bash** :

```bash
./.venv/Scripts/python.exe manage.py check
```

Le résultat attendu est :

```text
System check identified no issues (0 silenced).
```

Pour exécuter les tests :

Dans **PowerShell** :

```powershell
.venv\Scripts\python.exe manage.py test accounts.tests catalogue.tests catalogue.tests_api --settings=reservations.test_settings
```

Dans **Git Bash** :

```bash
./.venv/Scripts/python.exe manage.py test accounts.tests catalogue.tests catalogue.tests_api --settings=reservations.test_settings
```

Le résultat attendu est `OK` après l'exécution des 80 tests.

## 9. Démarrer le serveur

Lancer Django :

Dans **PowerShell** :

```powershell
.venv\Scripts\python.exe manage.py runserver
```

Dans **Git Bash** :

```bash
./.venv/Scripts/python.exe manage.py runserver
```

Ouvrir ensuite :

- site : <http://127.0.0.1:8000/> ;
- administration : <http://127.0.0.1:8000/admin/> ;
- documentation API : <http://127.0.0.1:8000/catalogue/api/docs/> ;
- flux RSS : <http://127.0.0.1:8000/catalogue/rss/representations/>.

Arrêter le serveur avec `Ctrl+C` dans PowerShell ou Git Bash.

## 10. Comptes de démonstration

| Profil | Login | Mot de passe |
|---|---|---|
| Membre | `demo_member` | `DemoMember!2026` |
| Producteur | `demo_producer` | `DemoProducer!2026` |
| Critique | `demo_critic` | `DemoCritic!2026` |
| Affilié Free | `demo_affiliate_free` | `DemoFree!2026` |
| Affilié Starter | `demo_affiliate_starter` | `DemoStarter!2026` |
| Affilié Premium | `demo_affiliate_premium` | `DemoPremium!2026` |
| Administrateur | `demo_admin` | Affiché lors de sa création |

Ces identifiants sont réservés à une installation locale de démonstration.

## 11. Installation rapide complète

Les commandes suivantes peuvent être exécutées dans l'ordre sur un ordinateur
Windows neuf :

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

### Variante pour Git Bash

Si le terminal affiche une invite Bash, utiliser plutôt :

```bash
git clone https://github.com/slavaBJJ/reservationsDjango.git
cd reservationsDjango
git switch categorie_prépa_exam
py -3.12 -m venv .venv
./.venv/Scripts/python.exe -m pip install --upgrade pip
./.venv/Scripts/python.exe -m pip install -r requirements.txt
./.venv/Scripts/python.exe manage.py migrate
./.venv/Scripts/python.exe manage.py create_demo_accounts
./.venv/Scripts/python.exe manage.py check
./.venv/Scripts/python.exe manage.py runserver
```

La différence concerne uniquement le chemin vers Python : PowerShell accepte
`.venv\Scripts\python.exe`, tandis que Git Bash attend
`./.venv/Scripts/python.exe`.

## 12. Résolution des problèmes courants

### La commande `py -3.12` est introuvable

Python 3.12 n'est pas installé ou le lanceur Python n'est pas accessible.
Réinstaller Python 3.12 depuis python.org en activant l'option d'ajout au PATH.

### `No module named django`

La commande utilise le Python global au lieu de l'environnement virtuel, ou les
dépendances ne sont pas installées.

Dans **PowerShell** :

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Dans **Git Bash** :

```bash
./.venv/Scripts/python.exe -m pip install -r requirements.txt
```

### `Error loading psycopg2 or psycopg module`

Vérifier que la commande utilise `.venv\Scripts\python.exe` dans PowerShell ou
`./.venv/Scripts/python.exe` dans Git Bash, puis réinstaller les dépendances.
`psycopg2-binary` est déjà déclaré dans `requirements.txt`.

### Erreur de connexion PostgreSQL

Pour l'examen local, supprimer ou renommer un éventuel fichier `.env` afin de
revenir à SQLite. Vérifier également qu'aucune variable `DATABASE_URL`,
`DJANGO_DATABASE` ou `POSTGRES_*` n'est définie dans le terminal.

Dans **PowerShell**, retirer temporairement ces variables avec :

```powershell
Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
Remove-Item Env:DJANGO_DATABASE -ErrorAction SilentlyContinue
Remove-Item Env:POSTGRES_DB -ErrorAction SilentlyContinue
Remove-Item Env:POSTGRES_USER -ErrorAction SilentlyContinue
Remove-Item Env:POSTGRES_PASSWORD -ErrorAction SilentlyContinue
Remove-Item Env:POSTGRES_HOST -ErrorAction SilentlyContinue
Remove-Item Env:POSTGRES_PORT -ErrorAction SilentlyContinue
```

Chaque ligne retire uniquement la variable indiquée de la fenêtre PowerShell
actuelle. Elle ne modifie pas le système Windows de manière permanente.

Dans **Git Bash**, utiliser :

```bash
unset DATABASE_URL
unset DJANGO_DATABASE
unset POSTGRES_DB
unset POSTGRES_USER
unset POSTGRES_PASSWORD
unset POSTGRES_HOST
unset POSTGRES_PORT
```

Chaque ligne `unset` retire uniquement la variable indiquée de la session Git
Bash actuelle.

### La branche `categorie_prépa_exam` est introuvable

Mettre à jour les références Git puis réessayer :

```text
git fetch origin
git switch categorie_prépa_exam
```

Si elle reste introuvable, la branche n'a pas encore été poussée sur GitHub.

### Recommencer avec une base locale vide

Arrêter le serveur, supprimer uniquement `db.sqlite3`, puis recréer la base :

Dans **PowerShell** :

```powershell
Remove-Item db.sqlite3
.venv\Scripts\python.exe manage.py migrate
.venv\Scripts\python.exe manage.py create_demo_accounts
```

Dans **Git Bash** :

```bash
rm db.sqlite3
./.venv/Scripts/python.exe manage.py migrate
./.venv/Scripts/python.exe manage.py create_demo_accounts
```

Cette opération supprime toutes les données SQLite locales. Elle n'affecte ni
GitHub, ni PostgreSQL, ni le site déployé sur Render.
