"""Flask application factory for the flu analytics dashboard and JSON API."""

from __future__ import annotations

from flask import Flask
from flask_cors import CORS


def create_app() -> Flask:
    """Build and configure the Flask app."""
    app = Flask(__name__)
    CORS(app)

    from api.routes import bp

    app.register_blueprint(bp)
    return app
