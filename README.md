# Projet Réservations

Application Django de gestion et de réservation de spectacles, accompagnée
d'une API REST HATEOAS sécurisée.

## Documentation API

Après avoir lancé le serveur :

- Swagger UI : `http://127.0.0.1:8000/catalogue/api/docs/`
- Schéma OpenAPI JSON : `http://127.0.0.1:8000/catalogue/api/schema/`

### Authentification JWT

Obtenir les jetons :

```bash
curl -X POST http://127.0.0.1:8000/catalogue/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"mon-utilisateur","password":"mon-mot-de-passe"}'
```

Utiliser le jeton d'accès :

```bash
curl http://127.0.0.1:8000/catalogue/api/shows/ \
  -H "Authorization: Bearer <access_token>"
```

Rafraîchir le jeton :

```bash
curl -X POST http://127.0.0.1:8000/catalogue/api/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh":"<refresh_token>"}'
```

### Endpoints

- `GET|POST /catalogue/api/artists/`
- `GET|PUT|PATCH|DELETE /catalogue/api/artists/{id}/`
- `GET|POST /catalogue/api/shows/`
- `GET|PUT|PATCH|DELETE /catalogue/api/shows/{id}/`
- `POST /catalogue/api/token/`
- `POST /catalogue/api/token/refresh/`

L'API des artistes applique les permissions Django du modèle. La lecture des
spectacles est réservée aux groupes `AFFILIATE_FREE`, `AFFILIATE_STARTER` et
`AFFILIATE_PREMIUM`. Leur pagination maximale est respectivement de 10, 25 et
100 résultats. Les écritures sont réservées au personnel.

### Recherche, filtre et tri des spectacles

Paramètres acceptés par `/catalogue/api/shows/` :

- `q` : recherche dans le titre et la description ;
- `location` : slug du lieu ;
- `reservable=true|false` : disponibilité réelle ;
- `ordering` : `title`, `created_in`, `duration`, `price` ou `availability` ;
- `page` et `page_size` : pagination plafonnée selon le niveau affilié.

`bookable` indique que l'organisation a ouvert les réservations. `reservable`
est calculé et vaut `true` uniquement lorsque le spectacle est ouvert, possède
un tarif et une représentation future. Le paramètre historique `bookable` reste
accepté comme alias de filtre pour compatibilité.

## CSRF et production

Le mode d'authentification détermine la protection à appliquer :

- JWT dans `Authorization: Bearer ...` n'utilise pas les cookies de session et
  ne nécessite donc pas de jeton CSRF ;
- Basic Authentication n'utilise pas non plus le cookie de session ;
- Session Authentication exige le cookie `csrftoken` et l'en-tête
  `X-CSRFToken` pour `POST`, `PUT`, `PATCH` et `DELETE`.

Le middleware `CsrfViewMiddleware` reste activé. En production HTTPS, définir
au minimum dans `.env` :

```dotenv
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=reservations.example.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://reservations.example.com
DJANGO_CSRF_COOKIE_SECURE=True
DJANGO_SESSION_COOKIE_SECURE=True
DJANGO_SECURE_SSL_REDIRECT=True
```

Activer HSTS uniquement après avoir confirmé que le domaine et ses sous-domaines
sont intégralement servis en HTTPS :

```dotenv
DJANGO_SECURE_HSTS_SECONDS=31536000
DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS=True
DJANGO_SECURE_HSTS_PRELOAD=True
```

## Comptes de démonstration

Ces comptes sont réservés à l'environnement local ou à une instance temporaire
d'évaluation. Ils ne doivent pas être installés sur un site public permanent.

| Profil | Login | Mot de passe temporaire |
|---|---|---|
| Membre | `demo_member` | `DemoMember!2026` |
| Producteur | `demo_producer` | `DemoProducer!2026` |
| Critique | `demo_critic` | `DemoCritic!2026` |
| Affilié Free | `demo_affiliate_free` | `DemoFree!2026` |
| Affilié Starter | `demo_affiliate_starter` | `DemoStarter!2026` |
| Affilié Premium | `demo_affiliate_premium` | `DemoPremium!2026` |
| Administrateur | `demo_admin` | Transmis séparément |

Le compte membre possède des réservations passées permettant de tester les avis.
Le producteur est associé aux sept spectacles de démonstration. Les comptes
affiliés permettent de vérifier les limites de pagination Free, Starter et
Premium.

Pour créer ou remettre à jour ces comptes en développement :

```bash
python3 manage.py create_demo_accounts
```

La commande est refusée lorsque `DJANGO_DEBUG=False`. Lors de sa première
exécution, elle génère le mot de passe temporaire de `demo_admin` et l'affiche
uniquement dans le terminal. Ce mot de passe ne doit pas être ajouté au dépôt.

## Déploiement sur Render

Le dépôt contient un Blueprint `render.yaml` qui crée un service web Django et
une base PostgreSQL. Le script `build.sh` installe les dépendances, rassemble les
fichiers statiques et applique les migrations à chaque déploiement.

1. Commiter et pousser les changements sur GitHub.
2. Dans Render, ouvrir **New > Blueprint** et connecter ce dépôt.
3. Sélectionner `render.yaml`, puis appliquer le Blueprint.
4. Attendre la fin du build et ouvrir l'URL publique `.onrender.com`.
5. Créer l'administrateur depuis le Shell Render :

```bash
python manage.py createsuperuser
```

Render génère `DJANGO_SECRET_KEY`, relie automatiquement `DATABASE_URL` à
PostgreSQL et fournit `RENDER_EXTERNAL_HOSTNAME`. Ce dernier est ajouté par les
réglages Django à `ALLOWED_HOSTS` et `CSRF_TRUSTED_ORIGINS`.

Le plan gratuit convient à une démonstration, mais le service web peut se mettre
en veille après une période d'inactivité et la base PostgreSQL gratuite expire
après 30 jours. Pour une disponibilité durable, choisir une base payante avant
cette échéance.
