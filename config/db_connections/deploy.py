"""Supabase / Vercel PostgreSQL (SSL + transaction pooler). Used when DJANGO_ENV=production."""

from urllib.parse import unquote, urlparse

from django.core.exceptions import ImproperlyConfigured

from config.env import env


def database_config():
    from_url = _from_database_url()
    if from_url:
        return from_url

    host = env("DB_HOST").strip()
    if not host:
        raise ImproperlyConfigured(
            "DB_HOST is empty, so Postgres tried a Unix socket instead of Supabase. "
            "In Vercel → Settings → Environment Variables, set DB_HOST, DB_USER, "
            "DB_PASSWORD, DB_NAME, DB_PORT (or DATABASE_URL) for Production AND Preview. "
            "Use the Transaction pooler host (port 6543), not localhost."
        )

    return _postgres(
        name=env("DB_NAME", "postgres"),
        user=env("DB_USER"),
        password=env("DB_PASSWORD"),
        host=host,
        port=env("DB_PORT", "6543"),
        sslmode=env("DB_SSLMODE", "require"),
    )


def _from_database_url():
    raw = (
        env("DATABASE_URL")
        or env("POSTGRES_URL")
        or env("POSTGRES_PRISMA_URL")
    ).strip()
    if not raw:
        return None

    parsed = urlparse(raw)
    if not parsed.hostname:
        raise ImproperlyConfigured("DATABASE_URL has no host.")

    sslmode = "require"
    if parsed.query:
        for part in parsed.query.split("&"):
            key, _, value = part.partition("=")
            if key == "sslmode" and value:
                sslmode = unquote(value)

    return _postgres(
        name=unquote(parsed.path.lstrip("/") or "postgres"),
        user=unquote(parsed.username or ""),
        password=unquote(parsed.password or ""),
        host=parsed.hostname,
        port=str(parsed.port or 6543),
        sslmode=sslmode,
    )


def _postgres(*, name, user, password, host, port, sslmode):
    if not user or not password:
        raise ImproperlyConfigured(
            "Supabase user and password are required (DB_USER / DB_PASSWORD or DATABASE_URL)."
        )
    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": name or "postgres",
        "USER": user,
        "PASSWORD": password,
        "HOST": host,
        "PORT": port or "6543",
        "CONN_MAX_AGE": 0,
        "DISABLE_SERVER_SIDE_CURSORS": True,
        "OPTIONS": {
            "sslmode": sslmode or "require",
        },
    }
