"""Table 1: ``county_region`` — county reference with ACH region and density."""

from __future__ import annotations

import pandas as pd


def build_county_region(census: pd.DataFrame, rhino: pd.DataFrame) -> pd.DataFrame:
    """Build the county reference table.

    Args:
        census: Raw census frame with ``County Name`` and
            ``Population Density 2020`` columns.
        rhino: County-exploded RHINO frame with ``county`` and ``Location``.

    Returns:
        Columns: ``county_id``, ``county_name``, ``ach_region``,
        ``population_density_2020``. One row per county; counties belonging to
        multiple ACH regions get a comma-joined ``ach_region``; counties with no
        region are labeled ``Unassigned``.
    """
    counties = (
        census[["County Name", "Population Density 2020"]]
        .drop_duplicates()
        .sort_values("County Name")
        .reset_index(drop=True)
    )

    regions = rhino[["county", "Location"]].drop_duplicates()
    merged = counties.merge(
        regions, left_on="County Name", right_on="county", how="left"
    )

    grouped = (
        merged.groupby(["County Name", "Population Density 2020"], dropna=False)[
            "Location"
        ]
        .apply(lambda s: ", ".join(sorted(s.dropna().unique())))
        .reset_index()
    )
    grouped["Location"] = grouped["Location"].replace(r"^\s*$", "Unassigned", regex=True)
    grouped["county_id"] = grouped.index + 1

    result = grouped.rename(
        columns={
            "County Name": "county_name",
            "Location": "ach_region",
            "Population Density 2020": "population_density_2020",
        }
    )
    return result[
        ["county_id", "county_name", "ach_region", "population_density_2020"]
    ]
