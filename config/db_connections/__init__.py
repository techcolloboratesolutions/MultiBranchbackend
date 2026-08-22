"""Pick local vs deploy database settings from DJANGO_ENV / Vercel."""

import os
import sys

from django.core.exceptions import ImproperlyConfigured

from .deploy import database_config as deploy_database
from .local import database_config as local_database

_MEMORY_SQLITE = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}


def current_env_name() -> str:
    if os.environ.get("VERCEL"):
        return "production"
    name = os.environ.get("DJANGO_ENV", "local").strip().lower()
    if name in {"production", "prod", "deploy", "vercel"}:
        return "production"
    return "local"


def get_databases():
    if _skip_live_postgres():
        return dict(_MEMORY_SQLITE)

    builder = deploy_database if current_env_name() == "production" else local_database
    try:
        return {"default": builder()}
    except ImproperlyConfigured:
        # Build-time settings discovery has no (or incomplete) DB env.
        if (
            _is_settings_probe()
            or _skip_live_postgres()
            or (os.environ.get("VERCEL") and not os.environ.get("AWS_LAMBDA_FUNCTION_NAME"))
        ):
            return dict(_MEMORY_SQLITE)
        raise


def _skip_live_postgres() -> bool:
    return "test" in sys.argv or "collectstatic" in sys.argv


def _is_settings_probe() -> bool:
    argv0 = sys.argv[0] if sys.argv else ""
    return argv0 in {"-c", "-", ""} or "<string>" in argv0
