"""Shared pytest fixtures: synthetic source frames mirroring real schemas."""

from __future__ import annotations

import os

import pandas as pd
import pytest

from flu_pipeline.sources.rhino import CLEAN_PERCENT_COLUMN

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED_DIR = os.path.join(REPO_ROOT, "processed_files")


@pytest.fixture
def census_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "County Name": ["King", "Spokane", "Adams"],
            "Population Density 2020": [1000.0, 100.0, 10.0],
        }
    )


@pytest.fixture
def rhino_df() -> pd.DataFrame:
    """County-exploded RHINO frame as produced by the source layer."""
    return pd.DataFrame(
        {
            "Week": [40, 40, 41, 40],
            "Week Start": [
                "2023-10-01",
                "2023-10-01",
                "2023-10-08",
                "2023-10-01",
            ],
            "Week End": [
                "2023-10-07",
                "2023-10-07",
                "2023-10-14",
                "2023-10-07",
            ],
            "Season": ["2023-2024"] * 4,
            "Location": [
                "Healthier Here",
                "Better Health Together",
                "Healthier Here",
                "Greater Health Now",
            ],
            "county": ["King", "Spokane", "King", "Spokane"],
            "Respiratory Illness Category": ["Flu", "Flu", "Flu", "Flu"],
            "Care Type": [
                "Hospitalizations",
                "Hospitalizations",
                "Emergency Visits",
                "Emergency Visits",
            ],
            CLEAN_PERCENT_COLUMN: [4.0, 6.0, 2.0, 3.0],
        }
    )


@pytest.fixture
def fluview_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "epiweek": [202340, 202341, 202001, 202002, 202101],
            "wili": [1.0, 1.5, 5.0, 7.0, 3.0],
        }
    )


@pytest.fixture
def processed_dir() -> str:
    return PROCESSED_DIR
