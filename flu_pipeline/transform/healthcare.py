"""Table 4: ``healthcare`` — average hospitalization and ER utilization."""

from __future__ import annotations

import pandas as pd

from flu_pipeline.sources.rhino import CLEAN_PERCENT_COLUMN

HOSPITALIZATIONS = "Hospitalizations"
EMERGENCY_VISITS = "Emergency Visits"


def build_healthcare(
    county_region: pd.DataFrame,
    rhino: pd.DataFrame,
) -> pd.DataFrame:
    """Build the per-county healthcare-utilization table.

    Computes each county's mean hospitalization and emergency-visit percentages
    across all weeks, then their ratio.

    Returns:
        Columns: ``county_id``, ``population_density_2020``,
        ``hospitalization_percent``, ``er_visit_percent``,
        ``hospital_to_er_ratio``.
    """
    base = county_region[
        ["county_id", "county_name", "population_density_2020"]
    ].copy()

    rates_source = rhino[
        ["county", "Respiratory Illness Category", "Care Type", CLEAN_PERCENT_COLUMN]
    ].drop_duplicates()

    base = base.merge(
        rates_source, left_on="county_name", right_on="county", how="left"
    )

    # Mean utilization rate per county per care type.
    base["rates"] = base.groupby(["county_id", "Care Type"])[
        CLEAN_PERCENT_COLUMN
    ].transform("mean")
    base = base.drop(
        columns=[
            "county",
            CLEAN_PERCENT_COLUMN,
            "county_name",
            "Respiratory Illness Category",
        ]
    ).drop_duplicates().reset_index(drop=True)

    # Split the single rate column into care-type-specific columns.
    base["hospitalization_percent"] = base["rates"].where(
        base["Care Type"] == HOSPITALIZATIONS
    )
    base["er_visit_percent"] = base["rates"].where(
        base["Care Type"] == EMERGENCY_VISITS
    )
    base = base.drop(columns=["Care Type", "rates"])

    # Collapse the per-care-type rows into one row per county. groupby.first()
    # skips NaN, so each county keeps its hospitalization and ER values.
    collapsed = base.groupby(
        ["county_id", "population_density_2020"], as_index=False
    ).first()

    collapsed["hospital_to_er_ratio"] = (
        collapsed["hospitalization_percent"] / collapsed["er_visit_percent"]
    )
    return collapsed.fillna(0)
