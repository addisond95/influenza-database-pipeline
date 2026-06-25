"""Centralized configuration loaded from environment variables.

No credentials are hard-coded. All settings are read from the environment so the
same code runs unchanged in local, Docker, and CI contexts. A local ``.env`` file
is loaded automatically when present (see ``.env.example``).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from urllib.parse import quote_plus

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # python-dotenv is optional at runtime
    pass


# --------------------------------------------------------------------------- #
# Data source endpoints
# --------------------------------------------------------------------------- #

RHINO_URL = os.getenv(
    "RHINO_URL",
    "https://doh.wa.gov/sites/default/files/Data/Auto-Uploads/"
    "Respiratory-Illness/Respiratory_Disease_RHINO_Downloadable_Data.csv",
)

CENSUS_URL = os.getenv(
    "CENSUS_URL",
    "https://data.wa.gov/api/views/e6ip-wkqq/rows.csv?accessType=DOWNLOAD",
)

FLUVIEW_URL = os.getenv("FLUVIEW_URL", "https://api.delphi.cmu.edu/epidata/fluview/")
FLUVIEW_REGION = os.getenv("FLUVIEW_REGION", "wa")
FLUVIEW_EPIWEEKS = os.getenv("FLUVIEW_EPIWEEKS", "202001-202452")


# --------------------------------------------------------------------------- #
# Filesystem layout (inside the container by default)
# --------------------------------------------------------------------------- #

DATA_DIR = os.getenv("DATA_DIR", "/opt/airflow/data")
RAW_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DIR = os.getenv("PROCESSED_DIR", "/opt/airflow/processed_files")

# Database schema that holds the application tables.
APP_SCHEMA = os.getenv("APP_SCHEMA", "flu_schema")


# --------------------------------------------------------------------------- #
# Database connection
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class DatabaseSettings:
    """PostgreSQL connection parameters resolved from the environment."""

    user: str
    password: str
    host: str
    port: str
    name: str

    @property
    def sqlalchemy_url(self) -> str:
        """SQLAlchemy URL with URL-encoded credentials."""
        return (
            f"postgresql+psycopg2://{quote_plus(self.user)}:{quote_plus(self.password)}"
            f"@{self.host}:{self.port}/{self.name}"
        )

    @property
    def psycopg2_kwargs(self) -> dict:
        """Keyword arguments for ``psycopg2.connect``."""
        return {
            "dbname": self.name,
            "user": self.user,
            "password": self.password,
            "host": self.host,
            "port": self.port,
        }


@lru_cache(maxsize=1)
def get_database_settings() -> DatabaseSettings:
    """Return cached application-database settings from the environment."""
    return DatabaseSettings(
        user=os.environ.get("APP_DB_USER", "fluuser"),
        password=os.environ.get("APP_DB_PASSWORD", "flupass"),
        host=os.environ.get("APP_DB_HOST", "postgres"),
        port=os.environ.get("APP_DB_PORT", "5432"),
        name=os.environ.get("APP_DB_NAME", "flu_database"),
    )
