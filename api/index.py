import os
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.chdir(ROOT)
os.environ.setdefault("DJANGO_ENV", "production")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")


def _crash_app(message: bytes):
    def app(environ, start_response):
        start_response("500 Internal Server Error", [("Content-Type", "text/plain; charset=utf-8")])
        return [message]

    return app


try:
    from django.core.wsgi import get_wsgi_application

    application = get_wsgi_application()
    app = application
except Exception:
    app = application = _crash_app(traceback.format_exc().encode("utf-8"))
