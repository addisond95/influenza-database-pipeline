"""Schema definition and the canonical table registry.

A single :data:`TABLES` list drives both DDL creation and CSV loading so the two
can never drift apart. Tables are ordered so that parents (referenced by foreign
keys) are created and loaded before their children.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from flu_pipeline.config import APP_SCHEMA
from flu_pipeline.db.engine import get_psycopg2_connection

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TableSpec:
    """Everything needed to create and load one application table."""

    name: str
    columns: list[str]
    ddl: str
    conflict_columns: list[str]
    csv_filename: str
    staging_ddl: str = field(default="")

    @property
    def qualified_name(self) -> str:
        return f"{APP_SCHEMA}.{self.name}"


TABLES: list[TableSpec] = [
    TableSpec(
        name="county_region",
        columns=["county_id", "county_name", "ach_region", "population_density_2020"],
        conflict_columns=["county_id"],
        csv_filename="county_region.csv",
        ddl=f"""
            CREATE TABLE IF NOT EXISTS {APP_SCHEMA}.county_region (
                county_id INT PRIMARY KEY,
                county_name TEXT,
                ach_region TEXT,
                population_density_2020 FLOAT
            );
        """,
        staging_ddl="""
            county_id INT PRIMARY KEY,
            county_name TEXT,
            ach_region TEXT,
            population_density_2020 FLOAT
        """,
    ),
    TableSpec(
        name="temporal",
        columns=["epiweek_id", "week_start", "week_end", "season"],
        conflict_columns=["epiweek_id"],
        csv_filename="temporal.csv",
        ddl=f"""
            CREATE TABLE IF NOT EXISTS {APP_SCHEMA}.temporal (
                epiweek_id INT PRIMARY KEY,
                week_start DATE,
                week_end DATE,
                season TEXT
            );
        """,
        staging_ddl="""
            epiweek_id INT PRIMARY KEY,
            week_start DATE,
            week_end DATE,
            season TEXT
        """,
    ),
    TableSpec(
        name="illness",
        columns=[
            "epiweek_id",
            "county_id",
            "respiratory_illness_type",
            "care_type",
            "county_ili_percent",
            "state_ili_percent",
            "deviation_from_state_average",
        ],
        conflict_columns=[
            "epiweek_id",
            "county_id",
            "respiratory_illness_type",
            "care_type",
        ],
        csv_filename="illness.csv",
        ddl=f"""
            CREATE TABLE IF NOT EXISTS {APP_SCHEMA}.illness (
                epiweek_id INT,
                county_id INT,
                respiratory_illness_type TEXT,
                care_type TEXT,
                county_ili_percent FLOAT,
                state_ili_percent FLOAT,
                deviation_from_state_average FLOAT,
                PRIMARY KEY (epiweek_id, county_id, respiratory_illness_type, care_type),
                FOREIGN KEY (epiweek_id) REFERENCES {APP_SCHEMA}.temporal(epiweek_id),
                FOREIGN KEY (county_id) REFERENCES {APP_SCHEMA}.county_region(county_id)
            );
        """,
        staging_ddl="""
            epiweek_id INT,
            county_id INT,
            respiratory_illness_type TEXT,
            care_type TEXT,
            county_ili_percent FLOAT,
            state_ili_percent FLOAT,
            deviation_from_state_average FLOAT
        """,
    ),
    TableSpec(
        name="healthcare",
        columns=[
            "county_id",
            "population_density_2020",
            "hospitalization_percent",
            "er_visit_percent",
            "hospital_to_er_ratio",
        ],
        conflict_columns=["county_id"],
        csv_filename="healthcare.csv",
        ddl=f"""
            CREATE TABLE IF NOT EXISTS {APP_SCHEMA}.healthcare (
                county_id INT PRIMARY KEY,
                population_density_2020 FLOAT,
                hospitalization_percent FLOAT,
                er_visit_percent FLOAT,
                hospital_to_er_ratio FLOAT,
                FOREIGN KEY (county_id) REFERENCES {APP_SCHEMA}.county_region(county_id)
            );
        """,
        staging_ddl="""
            county_id INT PRIMARY KEY,
            population_density_2020 FLOAT,
            hospitalization_percent FLOAT,
            er_visit_percent FLOAT,
            hospital_to_er_ratio FLOAT
        """,
    ),
    TableSpec(
        name="historics",
        columns=[
            "year",
            "decade_year",
            "peak_week_id",
            "peak_ili_percent",
            "average_wili_percent",
            "peak_vs_avg_diff",
        ],
        conflict_columns=["year"],
        csv_filename="historic_flu.csv",
        ddl=f"""
            CREATE TABLE IF NOT EXISTS {APP_SCHEMA}.historics (
                year INT PRIMARY KEY,
                decade_year INT,
                peak_week_id INT,
                peak_ili_percent FLOAT,
                average_wili_percent FLOAT,
                peak_vs_avg_diff FLOAT
            );
        """,
        staging_ddl="""
            year INT PRIMARY KEY,
            decade_year INT,
            peak_week_id INT,
            peak_ili_percent FLOAT,
            average_wili_percent FLOAT,
            peak_vs_avg_diff FLOAT
        """,
    ),
]


def create_schema_and_tables() -> None:
    """Create the application schema and all tables if they do not exist."""
    conn = get_psycopg2_connection()
    try:
        with conn, conn.cursor() as cur:
            cur.execute(f"CREATE SCHEMA IF NOT EXISTS {APP_SCHEMA};")
            for table in TABLES:
                cur.execute(table.ddl)
                logger.info("Ensured table %s", table.qualified_name)
    finally:
        conn.close()
