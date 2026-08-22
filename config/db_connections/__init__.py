"""Pick local vs deploy database settings from DJANGO_ENV / Vercel."""

import os
import sys

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
    except Exception:
        if _skip_live_postgres():
            return dict(_MEMORY_SQLITE)
        raise


def _skip_live_postgres() -> bool:
    argv = sys.argv
    if "test" in argv or "collectstatic" in argv:
        return True
    # Vercel vc_django_settings.py: sys.argv = ["manage.py"] then import settings.
    if argv == ["manage.py"]:
        return True
    argv0 = argv[0] if argv else ""
    return argv0 in {"-c", "-", ""}
