from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import ensure_csrf_cookie


@require_GET
def schema(request):
    document = {
        'openapi': '3.0.3',
        'info': {
            'title': 'API Projet Réservations',
            'version': '1.0.0',
            'description': (
                'API REST HATEOAS du catalogue. Utilisez JWT pour les clients '
                'externes. Les requêtes par session sur les méthodes non sûres '
                'doivent envoyer le jeton CSRF Django.'
            ),
        },
        'servers': [{'url': request.build_absolute_uri('/').rstrip('/')}],
        'tags': [
            {'name': 'Authentification'},
            {'name': 'Artistes'},
            {'name': 'Spectacles'},
        ],
        'paths': {
            '/catalogue/api/token/': {
                'post': {
                    'tags': ['Authentification'],
                    'summary': 'Obtenir une paire de jetons JWT',
                    'security': [],
                    'requestBody': _json_body('TokenRequest'),
                    'responses': {
                        '200': _json_response('Jetons créés', 'TokenPair'),
                        '401': {'description': 'Identifiants invalides'},
                    },
                },
            },
            '/catalogue/api/token/refresh/': {
                'post': {
                    'tags': ['Authentification'],
                    'summary': "Rafraîchir le jeton d'accès",
                    'security': [],
                    'requestBody': _json_body('TokenRefresh'),
                    'responses': {
                        '200': _json_response('Jeton renouvelé', 'AccessToken'),
                        '401': {'description': 'Jeton invalide ou expiré'},
                    },
                },
            },
            '/catalogue/api/artists/': {
                'get': _operation('Artistes', 'Lister les artistes', 'ArtistList'),
                'post': _operation(
                    'Artistes', 'Créer un artiste', 'Artist',
                    request_schema='ArtistInput', permissions=True,
                ),
            },
            '/catalogue/api/artists/{id}/': {
                'parameters': [_id_parameter()],
                'get': _operation('Artistes', 'Consulter un artiste', 'Artist'),
                'put': _operation(
                    'Artistes', 'Remplacer un artiste', 'Artist',
                    request_schema='ArtistInput', permissions=True,
                ),
                'patch': _operation(
                    'Artistes', 'Modifier partiellement un artiste', 'Artist',
                    request_schema='ArtistInput', permissions=True,
                ),
                'delete': _delete_operation('Artistes', 'Supprimer un artiste'),
            },
            '/catalogue/api/shows/': {
                'get': {
                    **_operation('Spectacles', 'Lister les spectacles', 'ShowPage'),
                    'description': (
                        'Accès réservé aux affiliés. Free : 10 résultats, '
                        'Starter : 25, Premium : 100.'
                    ),
                    'parameters': [
                        _query_parameter('q', 'Recherche dans le titre et la description'),
                        _query_parameter('location', 'Slug du lieu'),
                        _query_parameter(
                            'reservable',
                            'Disponibilité réelle : ouverture, tarif et date future',
                        ),
                        _query_parameter(
                            'ordering',
                            'title, created_in, duration, price ou availability ; préfixe - pour décroissant',
                        ),
                        _query_parameter('page', 'Numéro de page', 'integer'),
                        _query_parameter('page_size', 'Taille plafonnée selon le niveau affilié', 'integer'),
                    ],
                },
                'post': _operation(
                    'Spectacles', 'Créer un spectacle', 'Show',
                    request_schema='ShowInput', permissions=True,
                ),
            },
            '/catalogue/api/shows/{id}/': {
                'parameters': [_id_parameter()],
                'get': _operation('Spectacles', 'Consulter un spectacle', 'Show'),
                'put': _operation(
                    'Spectacles', 'Remplacer un spectacle', 'Show',
                    request_schema='ShowInput', permissions=True,
                ),
                'patch': _operation(
                    'Spectacles', 'Modifier partiellement un spectacle', 'Show',
                    request_schema='ShowInput', permissions=True,
                ),
                'delete': _delete_operation('Spectacles', 'Supprimer un spectacle'),
            },
        },
        'components': {
            'securitySchemes': {
                'bearerAuth': {
                    'type': 'http', 'scheme': 'bearer', 'bearerFormat': 'JWT',
                },
                'basicAuth': {'type': 'http', 'scheme': 'basic'},
                'sessionAuth': {
                    'type': 'apiKey', 'in': 'cookie', 'name': 'sessionid',
                    'description': 'Exige X-CSRFToken pour POST, PUT, PATCH et DELETE.',
                },
            },
            'schemas': _schemas(),
        },
        'security': [{'bearerAuth': []}, {'basicAuth': []}, {'sessionAuth': []}],
    }
    return JsonResponse(document)


@require_GET
@ensure_csrf_cookie
def docs(request):
    return render(request, 'api/docs.html')


def _operation(tag, summary, response_schema, request_schema=None, permissions=False):
    operation = {
        'tags': [tag],
        'summary': summary,
        'responses': {
            '200': _json_response('Succès', response_schema),
            '401': {'description': 'Authentification requise'},
            '403': {'description': 'Permission ou niveau affilié insuffisant'},
        },
    }
    if request_schema:
        operation['requestBody'] = _json_body(request_schema)
        operation['responses']['201'] = _json_response('Ressource créée', response_schema)
    if permissions:
        operation['description'] = 'Une permission Django adaptée est nécessaire en écriture.'
    return operation


def _delete_operation(tag, summary):
    return {
        'tags': [tag], 'summary': summary,
        'responses': {
            '204': {'description': 'Ressource supprimée'},
            '401': {'description': 'Authentification requise'},
            '403': {'description': 'Permission insuffisante'},
            '404': {'description': 'Ressource inexistante'},
        },
    }


def _json_body(schema_name):
    return {
        'required': True,
        'content': {'application/json': {'schema': {'$ref': f'#/components/schemas/{schema_name}'}}},
    }


def _json_response(description, schema_name):
    return {
        'description': description,
        'content': {'application/json': {'schema': {'$ref': f'#/components/schemas/{schema_name}'}}},
    }


def _id_parameter():
    return {
        'name': 'id', 'in': 'path', 'required': True,
        'schema': {'type': 'integer'},
    }


def _query_parameter(name, description, value_type='string'):
    return {
        'name': name, 'in': 'query', 'required': False,
        'description': description, 'schema': {'type': value_type},
    }


def _schemas():
    artist_properties = {
        'id': {'type': 'integer', 'readOnly': True},
        'firstname': {'type': 'string', 'maxLength': 60},
        'lastname': {'type': 'string', 'maxLength': 60},
        'links': {'type': 'object', 'readOnly': True},
    }
    show_properties = {
        'id': {'type': 'integer', 'readOnly': True},
        'slug': {'type': 'string', 'maxLength': 60},
        'title': {'type': 'string', 'maxLength': 255},
        'description': {'type': 'string', 'nullable': True},
        'duration': {'type': 'integer', 'nullable': True},
        'created_in': {'type': 'integer'},
        'location': {'type': 'integer', 'nullable': True},
        'location_name': {'type': 'string', 'nullable': True, 'readOnly': True},
        'bookable': {
            'type': 'boolean',
            'description': "Indique si l'organisation a ouvert les réservations.",
        },
        'reservable': {
            'type': 'boolean', 'readOnly': True,
            'description': 'Vrai uniquement avec ouverture, tarif et représentation future.',
        },
        'minimum_price': {'type': 'string', 'nullable': True, 'readOnly': True},
        'links': {'type': 'object', 'readOnly': True},
    }
    return {
        'Artist': {'type': 'object', 'properties': artist_properties},
        'ArtistInput': {
            'type': 'object', 'required': ['firstname', 'lastname'],
            'properties': {key: artist_properties[key] for key in ('firstname', 'lastname')},
        },
        'ArtistList': {
            'type': 'array', 'items': {'$ref': '#/components/schemas/Artist'},
        },
        'Show': {'type': 'object', 'properties': show_properties},
        'ShowInput': {
            'type': 'object', 'required': ['slug', 'title', 'created_in'],
            'properties': {
                key: value for key, value in show_properties.items()
                if not value.get('readOnly')
            },
        },
        'ShowPage': {
            'type': 'object',
            'properties': {
                'count': {'type': 'integer'},
                'next': {'type': 'string', 'nullable': True},
                'previous': {'type': 'string', 'nullable': True},
                'results': {
                    'type': 'array', 'items': {'$ref': '#/components/schemas/Show'},
                },
            },
        },
        'TokenRequest': {
            'type': 'object', 'required': ['username', 'password'],
            'properties': {'username': {'type': 'string'}, 'password': {'type': 'string'}},
        },
        'TokenPair': {
            'type': 'object',
            'properties': {'access': {'type': 'string'}, 'refresh': {'type': 'string'}},
        },
        'TokenRefresh': {
            'type': 'object', 'required': ['refresh'],
            'properties': {'refresh': {'type': 'string'}},
        },
        'AccessToken': {
            'type': 'object', 'properties': {'access': {'type': 'string'}},
        },
    }
