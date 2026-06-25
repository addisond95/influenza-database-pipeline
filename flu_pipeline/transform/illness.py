"""Table 3: ``illness`` — county vs. state ILI comparison by week."""

from __future__ import annotations

import pandas as pd

from flu_pipeline.sources.rhino import CLEAN_PERCENT_COLUMN
from flu_pipeline.transform.temporal import add_epiweek_id


def build_illness(
    rhino: pd.DataFrame,
    county_region: pd.DataFrame,
    fluview: pd.DataFrame,
) -> pd.DataFrame:
    """Build the per-county weekly illness comparison table.

    Joins county ids from the reference table and the statewide ILI percentage
    from FluView, then computes each county's deviation from the state average.

    Returns:
        Columns: ``epiweek_id``, ``county_id``, ``respiratory_illness_type``,
        ``care_type``, ``county_ili_percent``, ``state_ili_percent``,
        ``deviation_from_state_average``.
    """
    base = add_epiweek_id(rhino)[
        [
            "epiweek_id",
            "county",
            "Respiratory Illness Category",
            "Care Type",
            CLEAN_PERCENT_COLUMN,
        ]
    ].copy()

    base = base.merge(
        county_region[["county_id", "county_name"]],
        left_on="county",
        right_on="county_name",
        how="left",
    ).drop(columns=["county", "county_name"])

    base["epiweek_id"] = base["epiweek_id"].astype(int)
    base = base.merge(
        fluview[["epiweek", "wili"]],
        left_on="epiweek_id",
        right_on="epiweek",
        how="left",
    ).rename(columns={"wili": "state_ili_percent"}).drop(columns=["epiweek"])

    base = base.drop_duplicates(
        subset=["epiweek_id", "county_id", "Respiratory Illness Category", "Care Type"]
    )

    base["deviation_from_state_average"] = (
        base[CLEAN_PERCENT_COLUMN] - base["state_ili_percent"]
    )

    result = base.rename(
        columns={
            "Respiratory Illness Category": "respiratory_illness_type",
            "Care Type": "care_type",
            CLEAN_PERCENT_COLUMN: "county_ili_percent",
        }
    )
    return result[
        [
            "epiweek_id",
            "county_id",
            "respiratory_illness_type",
            "care_type",
            "county_ili_percent",
            "state_ili_percent",
            "deviation_from_state_average",
        ]
    ]
