"""Supabase / Vercel PostgreSQL (SSL + transaction pooler). Used when DJANGO_ENV=production."""

from config.env import env


def database_config():
    return {

        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DB_NAME", "postgres"),
        "USER": env("DB_USER",),
        "PASSWORD": env("DB_PASSWORD"),
        "HOST": env("DB_HOST",),
        "PORT": env("DB_PORT", "6543"),
        "CONN_MAX_AGE": 0,
        "DISABLE_SERVER_SIDE_CURSORS": True,
        "OPTIONS": {
            "sslmode": env("DB_SSLMODE", "require"),
        },
    }
