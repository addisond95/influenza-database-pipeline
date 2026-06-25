"""SQL query definitions for the report endpoints.

All queries are static (no user-supplied values are interpolated), so they are
safe from injection by construction. The application schema name comes from
configuration, not from request input.
"""

from __future__ import annotations

from sqlalchemy import text

from flu_pipeline.config import APP_SCHEMA

WEEKLY_TRENDS = text(
    f"""
    SELECT
        t.week_end,
        t.epiweek_id,
        i.respiratory_illness_type,
        AVG(i.county_ili_percent) AS avg_percent_positive,
        COUNT(DISTINCT i.county_id) AS counties_reporting
    FROM {APP_SCHEMA}.temporal t
    LEFT JOIN {APP_SCHEMA}.illness i ON t.epiweek_id = i.epiweek_id
    WHERE i.respiratory_illness_type IS NOT NULL
    GROUP BY t.week_end, t.epiweek_id, t.season, i.respiratory_illness_type
    HAVING AVG(i.county_ili_percent) IS NOT NULL
    ORDER BY t.week_end DESC, i.respiratory_illness_type
    LIMIT 20
    """
)

HEALTHCARE_IMPACT = text(
    f"""
    SELECT
        cr.ach_region,
        COUNT(DISTINCT cr.county_id) AS counties_in_region,
        AVG(h.population_density_2020) AS avg_population_density,
        AVG(h.hospitalization_percent) AS avg_hospitalization_percent,
        AVG(h.er_visit_percent) AS avg_er_visit_percent,
        AVG(h.hospital_to_er_ratio) AS avg_hospital_to_er_ratio
    FROM {APP_SCHEMA}.healthcare h
    JOIN {APP_SCHEMA}.county_region cr ON h.county_id = cr.county_id
    WHERE h.hospitalization_percent > 0 OR h.er_visit_percent > 0
    GROUP BY cr.ach_region
    ORDER BY avg_hospitalization_percent DESC NULLS LAST
    """
)

HISTORICAL_SUMMARY = text(
    f"""
    SELECT
        year,
        decade_year,
        peak_week_id,
        peak_ili_percent,
        average_wili_percent,
        peak_vs_avg_diff
    FROM {APP_SCHEMA}.historics
    ORDER BY year DESC
    """
)
