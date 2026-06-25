#!/usr/bin/env python3
"""Seed the database directly from the committed processed CSV files.

Useful for a quick demo or for local testing of the API without running the full
Airflow pipeline (which requires live network access to the data sources).

    python scripts/seed_database.py
"""

from __future__ import annotations

import logging

from flu_pipeline.db.load import load_all_tables
from flu_pipeline.db.schema import create_schema_and_tables

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")


def main() -> None:
    create_schema_and_tables()
    counts = load_all_tables()
    print("\nLoaded row counts:")
    for table, count in counts.items():
        print(f"  {table:<16} {count:>6}")


if __name__ == "__main__":
    main()
