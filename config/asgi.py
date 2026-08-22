"""ASGI config for MultiBranches."""

import os

if os.environ.get("VERCEL"):
    os.environ["DJANGO_ENV"] = "production"

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from django.core.asgi import get_asgi_application

application = get_asgi_application()
