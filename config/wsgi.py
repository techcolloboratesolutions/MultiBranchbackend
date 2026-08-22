"""WSGI config for MultiBranches."""

import os
import traceback

if os.environ.get("VERCEL"):
    os.environ["DJANGO_ENV"] = "production"

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")


def _crash_app(exc: BaseException):
    body = "".join(traceback.format_exception(exc)).encode("utf-8")

    def application(environ, start_response):
        start_response(
            "500 Internal Server Error",
            [("Content-Type", "text/plain; charset=utf-8")],
        )
        return [body]

    return application


try:
    from django.core.wsgi import get_wsgi_application

    application = get_wsgi_application()
except Exception as exc:
    application = _crash_app(exc)

app = application
