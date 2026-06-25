"""API smoke tests that do not require a live database."""

from __future__ import annotations

import pytest

from api import create_app
from api.routes import EXPORTABLE_TABLES
from flu_pipeline.db.schema import TABLES


@pytest.fixture
def client():
    app = create_app()
    app.config.update(TESTING=True)
    return app.test_client()


def test_home_lists_endpoints(client):
    resp = client.get("/")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] == "running"
    assert "/health" in body["endpoints"]


def test_export_rejects_unknown_table(client):
    resp = client.get("/api/export/csv?table=not_a_table")
    assert resp.status_code == 400
    assert "Invalid table" in resp.get_json()["error"]


def test_export_whitelist_matches_registry():
    assert EXPORTABLE_TABLES == {table.name for table in TABLES}


def test_viewer_renders(client):
    resp = client.get("/viewer")
    assert resp.status_code == 200
    assert b"Flu Data Analytics Dashboard" in resp.data
