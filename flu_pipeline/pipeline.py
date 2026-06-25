"""High-level pipeline steps orchestrating sources, transforms, and loading.

These functions are deliberately thin wrappers so the Airflow DAG stays readable
and every step is independently runnable and testable. Steps that hand data to a
downstream task communicate through CSV file paths (Airflow-XCom friendly).
"""

from __future__ import annotations

import logging
import os

import pandas as pd

from flu_pipeline.config import PROCESSED_DIR, RAW_DIR
from flu_pipeline.db.load import load_all_tables
from flu_pipeline.db.schema import create_schema_and_tables
from flu_pipeline.sources.census import fetch_census
from flu_pipeline.sources.fluview import fetch_fluview
from flu_pipeline.sources.rhino import fetch_rhino
from flu_pipeline.transform import (
    build_county_region,
    build_healthcare,
    build_historics,
    build_illness,
    build_temporal,
)

logger = logging.getLogger(__name__)


def _ensure_dirs() -> None:
    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(PROCESSED_DIR, exist_ok=True)


# --------------------------------------------------------------------------- #
# Collection steps (each returns the path of the raw CSV it wrote)
# --------------------------------------------------------------------------- #


def collect_rhino() -> str:
    _ensure_dirs()
    path = os.path.join(RAW_DIR, "wa_doh_rhino.csv")
    fetch_rhino().to_csv(path, index=False)
    return path


def collect_census() -> str:
    _ensure_dirs()
    path = os.path.join(RAW_DIR, "wa_population_density.csv")
    fetch_census().to_csv(path, index=False)
    return path


def collect_fluview() -> str:
    _ensure_dirs()
    path = os.path.join(RAW_DIR, "wa_fluview_data.csv")
    fetch_fluview().to_csv(path, index=False)
    return path


# --------------------------------------------------------------------------- #
# Transform step
# --------------------------------------------------------------------------- #


def build_processed_tables(
    census_path: str,
    rhino_path: str,
    fluview_path: str,
) -> dict[str, str]:
    """Read raw CSVs, build the five tables, and write them to PROCESSED_DIR."""
    _ensure_dirs()
    census = pd.read_csv(census_path)
    rhino = pd.read_csv(rhino_path)
    fluview = pd.read_csv(fluview_path)

    county_region = build_county_region(census, rhino)
    tables = {
        "county_region": county_region,
        "temporal": build_temporal(rhino),
        "illness": build_illness(rhino, county_region, fluview),
        "healthcare": build_healthcare(county_region, rhino),
        "historic_flu": build_historics(fluview),
    }

    paths: dict[str, str] = {}
    for name, frame in tables.items():
        path = os.path.join(PROCESSED_DIR, f"{name}.csv")
        frame.to_csv(path, index=False)
        paths[name] = path
        logger.info("Wrote %s (%d rows)", path, len(frame))
    return paths


# --------------------------------------------------------------------------- #
# Database steps
# --------------------------------------------------------------------------- #


def create_database_objects() -> None:
    create_schema_and_tables()


def ingest_processed_tables() -> dict[str, int]:
    return load_all_tables()
