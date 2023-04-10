import os

# for reference:
# 	sqlite = 'django.db.backends.sqlite3',
# 	postgresql = 'django.db.backends.postgresql_psycopg2',


def config():
    return {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": os.getenv("DB_DATABASE"),
        "USER": os.getenv("DB_USERNAME"),
        "PASSWORD": os.getenv("DB_PASSWORD"),
        "HOST": os.getenv("DB_HOST"),
        "PORT": os.getenv("DB_PORT"),
        "ATOMIC_REQUESTS": True,
    }
