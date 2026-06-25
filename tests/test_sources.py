"""Tests for the RHINO source cleaning and explosion logic (no network)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from flu_pipeline.sources.rhino import (
    CLEAN_PERCENT_COLUMN,
    PERCENT_COLUMN,
    clean_percentage,
    explode_to_counties,
)


def test_clean_percentage_handles_blanks_and_invalid():
    assert clean_percentage("3.5") == 3.5
    assert clean_percentage(2.0) == 2.0
    assert clean_percentage("") is None
    assert clean_percentage("   ") is None
    assert clean_percentage(np.nan) is None
    assert clean_percentage("not-a-number") is None


def test_explode_drops_aggregates_and_expands_counties():
    raw = pd.DataFrame(
        {
            "Location": ["Statewide", "North Sound", "Healthier Here"],
            PERCENT_COLUMN: ["", "3.0", "1.5"],
        }
    )
    result = explode_to_counties(raw)

    # Statewide aggregate row is removed.
    assert "Statewide" not in result["Location"].values
    # North Sound expands to its five member counties; Healthier Here to King.
    assert set(result.loc[result["Location"] == "North Sound", "county"]) == {
        "Whatcom",
        "Skagit",
        "Snohomish",
        "San Juan",
        "Island",
    }
    assert (result.loc[result["Location"] == "Healthier Here", "county"] == "King").all()
    # Cleaned percentage column is added.
    assert CLEAN_PERCENT_COLUMN in result.columns
