"""WA DOH RHINO respiratory-illness surveillance source.

RHINO reports are published per ACH (Accountable Community of Health) region.
This module downloads the report, drops aggregate rows, maps each ACH region to
its member counties, and explodes the data to one row per county.
"""

from __future__ import annotations

import logging

import pandas as pd

from flu_pipeline.config import RHINO_URL

logger = logging.getLogger(__name__)

# Trailing space in the source column name is intentional — it matches the file.
PERCENT_COLUMN = "1-Week Percent "
CLEAN_PERCENT_COLUMN = "1_week_percent_clean"

# Aggregate rows that must be removed before exploding to counties.
AGGREGATE_LOCATIONS = ["Statewide", "Unassigned ACH Region"]

# Official mapping of ACH region -> member counties (WA county names, exact).
ACH_TO_COUNTIES: dict[str, list[str]] = {
    "Better Health Together": ["Spokane", "Stevens", "Pend Oreille", "Ferry"],
    "Cascade Pacific Action Alliance": [
        "Thurston",
        "Mason",
        "Grays Harbor",
        "Pacific",
        "Lewis",
    ],
    "Elevate Health": ["Yakima", "Kittitas"],
    "Greater Health Now": ["Spokane"],
    "Healthier Here": ["King"],
    "North Sound": ["Whatcom", "Skagit", "Snohomish", "San Juan", "Island"],
    "Olympic Community of Health": ["Clallam", "Jefferson", "Kitsap"],
    "Southwest Washington": [
        "Clark",
        "Skamania",
        "Klickitat",
        "Cowlitz",
        "Wahkiakum",
    ],
    "Thriving Together NCW": ["Chelan", "Douglas", "Grant", "Okanogan"],
}


def clean_percentage(value) -> float | None:
    """Convert blank/invalid percentage cells to ``None``; keep numeric values."""
    if pd.isna(value):
        return None
    if isinstance(value, str) and value.strip() == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def explode_to_counties(df: pd.DataFrame) -> pd.DataFrame:
    """Drop aggregate rows and expand each ACH region to one row per county."""
    df = df[~df["Location"].isin(AGGREGATE_LOCATIONS)].copy()
    df["county_list"] = df["Location"].map(ACH_TO_COUNTIES)
    exploded = df.explode("county_list").reset_index(drop=True)
    exploded = exploded.rename(columns={"county_list": "county"})
    exploded = exploded.dropna(subset=["county"])
    exploded[CLEAN_PERCENT_COLUMN] = exploded[PERCENT_COLUMN].apply(clean_percentage)
    return exploded


def fetch_rhino(url: str | None = None) -> pd.DataFrame:
    """Download and normalize WA DOH RHINO data to county-level granularity."""
    url = url or RHINO_URL
    logger.info("Downloading RHINO data from %s", url)
    raw = pd.read_csv(url)
    raw["source"] = "WA_DOH_RHINO"
    exploded = explode_to_counties(raw)
    logger.info(
        "RHINO: %d source rows -> %d county rows (%d counties)",
        len(raw),
        len(exploded),
        exploded["county"].nunique(),
    )
    return exploded
