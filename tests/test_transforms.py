"""Unit tests for the transform layer using synthetic inputs."""

from __future__ import annotations

import pandas as pd

from flu_pipeline.transform import (
    add_epiweek_id,
    build_county_region,
    build_healthcare,
    build_historics,
    build_illness,
    build_temporal,
)


def test_county_region_assigns_ids_and_regions(census_df, rhino_df):
    result = build_county_region(census_df, rhino_df)

    assert list(result.columns) == [
        "county_id",
        "county_name",
        "ach_region",
        "population_density_2020",
    ]
    # Sorted alphabetically: Adams, King, Spokane -> ids 1, 2, 3.
    assert result["county_name"].tolist() == ["Adams", "King", "Spokane"]
    assert result["county_id"].tolist() == [1, 2, 3]

    by_name = result.set_index("county_name")
    # Adams has no ACH mapping in the RHINO frame.
    assert by_name.loc["Adams", "ach_region"] == "Unassigned"
    assert by_name.loc["King", "ach_region"] == "Healthier Here"
    # Spokane spans two ACH regions -> comma-joined, sorted.
    assert by_name.loc["Spokane", "ach_region"] == (
        "Better Health Together, Greater Health Now"
    )


def test_add_epiweek_id_combines_year_and_week(rhino_df):
    out = add_epiweek_id(rhino_df)
    assert out.loc[0, "epiweek_id"] == "202340"
    assert out.loc[2, "epiweek_id"] == "202341"


def test_temporal_is_deduplicated_and_typed(rhino_df):
    result = build_temporal(rhino_df)

    assert list(result.columns) == ["epiweek_id", "week_start", "week_end", "season"]
    # Four input rows collapse to two distinct epiweeks.
    assert result["epiweek_id"].tolist() == [202340, 202341]
    assert pd.api.types.is_integer_dtype(result["epiweek_id"])
    assert pd.api.types.is_datetime64_any_dtype(result["week_start"])
    assert pd.api.types.is_datetime64_any_dtype(result["week_end"])


def test_illness_joins_ids_and_state_average(census_df, rhino_df, fluview_df):
    county_region = build_county_region(census_df, rhino_df)
    result = build_illness(rhino_df, county_region, fluview_df)

    assert list(result.columns) == [
        "epiweek_id",
        "county_id",
        "respiratory_illness_type",
        "care_type",
        "county_ili_percent",
        "state_ili_percent",
        "deviation_from_state_average",
    ]
    # King hospitalization row in epiweek 202340: county 4.0 vs state wili 1.0.
    king_id = county_region.set_index("county_name").loc["King", "county_id"]
    row = result[
        (result["county_id"] == king_id)
        & (result["epiweek_id"] == 202340)
        & (result["care_type"] == "Hospitalizations")
    ].iloc[0]
    assert row["county_ili_percent"] == 4.0
    assert row["state_ili_percent"] == 1.0
    assert row["deviation_from_state_average"] == 3.0


def test_healthcare_splits_care_types_and_ratio(census_df, rhino_df):
    county_region = build_county_region(census_df, rhino_df)
    result = build_healthcare(county_region, rhino_df)

    assert list(result.columns) == [
        "county_id",
        "population_density_2020",
        "hospitalization_percent",
        "er_visit_percent",
        "hospital_to_er_ratio",
    ]
    king_id = county_region.set_index("county_name").loc["King", "county_id"]
    king = result[result["county_id"] == king_id].iloc[0]
    # King: hospitalization 4.0, ER 2.0 -> ratio 2.0.
    assert king["hospitalization_percent"] == 4.0
    assert king["er_visit_percent"] == 2.0
    assert king["hospital_to_er_ratio"] == 2.0
    # Adams has no RHINO rows -> all metrics filled with 0.
    adams_id = county_region.set_index("county_name").loc["Adams", "county_id"]
    adams = result[result["county_id"] == adams_id].iloc[0]
    assert adams["hospitalization_percent"] == 0
    assert adams["hospital_to_er_ratio"] == 0


def test_historics_computes_peak_and_average(fluview_df):
    result = build_historics(fluview_df)

    assert list(result.columns) == [
        "year",
        "decade_year",
        "peak_week_id",
        "peak_ili_percent",
        "average_wili_percent",
        "peak_vs_avg_diff",
    ]
    by_year = result.set_index("year")
    # 2020: wili 5.0 and 7.0 -> peak 7.0 at week 202002, avg 6.0, diff 1.0.
    assert by_year.loc[2020, "peak_ili_percent"] == 7.0
    assert by_year.loc[2020, "peak_week_id"] == 202002
    assert by_year.loc[2020, "average_wili_percent"] == 6.0
    assert by_year.loc[2020, "peak_vs_avg_diff"] == 1.0
    assert by_year.loc[2020, "decade_year"] == 2020
