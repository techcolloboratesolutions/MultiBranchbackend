"""Local PostgreSQL (no SSL). Used when DJANGO_ENV=local."""


def database_config(env):
    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DB_NAME", default="multibranches"),
        "USER": env("DB_USER", default="postgres"),
        "PASSWORD": env("DB_PASSWORD", default=""),
        "HOST": env("DB_HOST", default="localhost"),
        "PORT": env("DB_PORT", default="5432"),
        "CONN_MAX_AGE": 60,
        "OPTIONS": {
            "sslmode": env("DB_SSLMODE", default="disable"),
        },
    }
