"""Pick local vs deploy database settings from DJANGO_ENV / Vercel."""

import os
import sys

from .deploy import database_config as deploy_database
from .local import database_config as local_database


def current_env_name() -> str:
    if os.environ.get("VERCEL"):
        return "production"
    name = os.environ.get("DJANGO_ENV", "local").strip().lower()
    if name in {"production", "prod", "deploy", "vercel"}:
        return "production"
    return "local"


def get_databases():
    if "test" in sys.argv:
        return {
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": ":memory:",
            }
        }

    builder = deploy_database if current_env_name() == "production" else local_database
    return {"default": builder()}
