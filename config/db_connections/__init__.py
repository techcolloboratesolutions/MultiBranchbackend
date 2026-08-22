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
    if _is_vercel_build_probe():
        return dict(_MEMORY_SQLITE)

    builder = deploy_database if current_env_name() == "production" else local_database
    return {"default": builder()}


def _is_vercel_build_probe() -> bool:
    argv = sys.argv
    if "collectstatic" in argv or "test" in argv:
        return True
    # packages/python/templates/vc_django_settings.py sets this, then imports settings.
    return argv == ["manage.py"]
