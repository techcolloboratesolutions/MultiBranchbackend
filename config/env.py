"""Stdlib env helpers. Avoid django-environ so Vercel does not need that package."""

from __future__ import annotations

import os
from pathlib import Path


def load_env_file(path: Path) -> None:
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if key:
            os.environ.setdefault(key, value)


def env(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


def env_required(*keys: str) -> None:
    missing = [key for key in keys if not os.environ.get(key, "").strip()]
    if not missing:
        return
    from django.core.exceptions import ImproperlyConfigured

    raise ImproperlyConfigured(
        "These database variables are not defined: "
        + ", ".join(f"{key}" for key in missing)
        + ". For local: backend/.env.local (DB_NAME=multibranches). "
        "For production: backend/.env.deploy (DB_NAME=postgres) or the same names on Vercel."
    )


def env_bool(key: str, default: bool = False) -> bool:
    value = os.environ.get(key)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(key: str, default: list[str] | None = None) -> list[str]:
    value = os.environ.get(key)
    if not value:
        return list(default or [])
    return [part.strip() for part in value.split(",") if part.strip()]
