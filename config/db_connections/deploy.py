"""Supabase / Vercel PostgreSQL (SSL + transaction pooler). Used when DJANGO_ENV=production."""


def database_config(env):
    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DB_NAME", default="postgres"),
        "USER": env("DB_USER", default="postgres.wozkhxrdaecpuhgccyfq"),
        "PASSWORD": env("DB_PASSWORD", default="Techy321#@!"),
        "HOST": env("DB_HOST", default="aws-0-ap-northeast-2.pooler.supabase.com"),
        "PORT": env("DB_PORT", default="6543"),
        "CONN_MAX_AGE": 0,
        "DISABLE_SERVER_SIDE_CURSORS": True,
        "OPTIONS": {
            "sslmode": env("DB_SSLMODE", default="require"),
        },
    }
