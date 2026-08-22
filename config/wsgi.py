"""WSGI config for MultiBranches."""

import os

if os.environ.get("VERCEL"):
    os.environ["DJANGO_ENV"] = "production"

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
app = application
