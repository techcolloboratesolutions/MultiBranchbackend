"""Local PostgreSQL (no SSL). Used when DJANGO_ENV=local."""

from config.env import env


def database_config():
    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DB_NAME", "multibranches"),
        "USER": env("DB_USER", "postgres"),
        "PASSWORD": env("DB_PASSWORD"),
        "HOST": env("DB_HOST", "localhost"),
        "PORT": env("DB_PORT", "5432"),
        "CONN_MAX_AGE": 60,
        "OPTIONS": {
            "sslmode": env("DB_SSLMODE", "disable"),
        },
    }
