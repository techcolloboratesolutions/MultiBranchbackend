"""Supabase / Vercel PostgreSQL (SSL + transaction pooler). Used when DJANGO_ENV=production."""

from urllib.parse import unquote, urlparse

from django.core.exceptions import ImproperlyConfigured

from config.env import env


def database_config():
    from_url = _from_database_url()
    if from_url:
        return from_url

    host = _first_env("DB_HOST", "POSTGRES_HOST", "PGHOST")
    if not host:
        raise ImproperlyConfigured(
            "DB_HOST is empty, so Postgres tried a Unix socket instead of Supabase. "
            "In Vercel → Settings → Environment Variables, set DB_HOST, DB_USER, "
            "DB_PASSWORD, DB_NAME, DB_PORT (or DATABASE_URL) for Production AND Preview. "
            "Use the Transaction pooler host (port 6543), not localhost."
        )

    return _postgres(
        name=_first_env("DB_NAME", "POSTGRES_DATABASE", "PGDATABASE") or "postgres",
        user=_first_env("DB_USER", "POSTGRES_USER", "PGUSER"),
        password=_first_env("DB_PASSWORD", "POSTGRES_PASSWORD", "PGPASSWORD"),
        host=host,
        port=_first_env("DB_PORT", "POSTGRES_PORT", "PGPORT") or "6543",
        sslmode=_first_env("DB_SSLMODE") or "require",
    )


def _first_env(*keys: str) -> str:
    for key in keys:
        value = env(key).strip()
        if value:
            return value
    return ""


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
    name = str(name or "postgres").strip()
    user = str(user or "").strip()
    password = str(password or "").strip()
    host = str(host or "").strip()
    port = str(port or "6543").strip()
    sslmode = str(sslmode or "require").strip().lower()
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
            "connect_timeout": 8,
            "gssencmode": "disable",
        },
    }
