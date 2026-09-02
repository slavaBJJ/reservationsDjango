from .settings import *


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    },
}

# The catalogue migration history contains PostgreSQL-specific SQL. Tests use
# Django's model definitions directly so the isolated SQLite schema stays
# portable and never touches the development database.
MIGRATION_MODULES = {
    'catalogue': None,
}

STORAGES = {
    **STORAGES,
    'staticfiles': {
        'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
    },
}

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]
