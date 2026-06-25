"""API entrypoint.

Exposes a module-level ``app`` for production WSGI servers (e.g. gunicorn via
``api.app:app``) and supports ``python -m api.app`` for local development.
Debug mode is never enabled by default.
"""

from __future__ import annotations

import os

from api import create_app

app = create_app()


def main() -> None:
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "5000"))
    debug = os.getenv("API_DEBUG", "false").lower() == "true"
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    main()
