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

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]
