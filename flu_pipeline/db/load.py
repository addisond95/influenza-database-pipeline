"""Idempotent CSV loading via staging tables and ``INSERT ... ON CONFLICT``.

Each table is loaded by COPYing the processed CSV into a temporary staging table
and then inserting new rows into the target. ``ON CONFLICT DO NOTHING`` makes the
load safe to re-run without creating duplicates.
"""

from __future__ import annotations

import logging
import os

from flu_pipeline.config import PROCESSED_DIR
from flu_pipeline.db.engine import get_psycopg2_connection
from flu_pipeline.db.schema import TABLES, TableSpec

logger = logging.getLogger(__name__)


def load_table(table: TableSpec, processed_dir: str | None = None) -> int:
    """Load a single table's CSV into the database. Returns rows in target."""
    processed_dir = processed_dir or PROCESSED_DIR
    csv_path = os.path.join(processed_dir, table.csv_filename)
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Processed file not found: {csv_path}")

    staging = f"staging_{table.name}"
    column_list = ", ".join(table.columns)
    conflict = ", ".join(table.conflict_columns)

    conn = get_psycopg2_connection()
    try:
        with conn, conn.cursor() as cur:
            cur.execute(f"DROP TABLE IF EXISTS {staging};")
            cur.execute(f"CREATE TEMP TABLE {staging} ({table.staging_ddl});")

            with open(csv_path, "r", encoding="utf-8") as fh:
                cur.copy_expert(
                    f"COPY {staging} FROM STDIN WITH (FORMAT CSV, HEADER TRUE)", fh
                )

            cur.execute(
                f"INSERT INTO {table.qualified_name} ({column_list}) "
                f"SELECT {column_list} FROM {staging} "
                f"ON CONFLICT ({conflict}) DO NOTHING;"
            )
            cur.execute(f"SELECT COUNT(*) FROM {table.qualified_name};")
            count = cur.fetchone()[0]
        logger.info("Loaded %s -> %d rows", table.qualified_name, count)
        return count
    finally:
        conn.close()


def load_all_tables(processed_dir: str | None = None) -> dict[str, int]:
    """Load every registered table in dependency order. Returns row counts."""
    return {table.name: load_table(table, processed_dir) for table in TABLES}
