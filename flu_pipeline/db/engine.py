"""SQLAlchemy engine and psycopg2 connection factories.

Both read connection parameters from :mod:`flu_pipeline.config`, so credentials
never appear in source. The engine is cached for reuse.
"""

from __future__ import annotations

from functools import lru_cache

import psycopg2
from sqlalchemy import Engine, create_engine

from flu_pipeline.config import get_database_settings


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """Return a cached SQLAlchemy engine for the application database."""
    settings = get_database_settings()
    return create_engine(settings.sqlalchemy_url, pool_pre_ping=True, future=True)


def get_psycopg2_connection() -> "psycopg2.extensions.connection":
    """Open a raw psycopg2 connection (caller is responsible for closing)."""
    settings = get_database_settings()
    return psycopg2.connect(**settings.psycopg2_kwargs)
