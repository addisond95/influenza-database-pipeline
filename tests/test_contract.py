"""Contract tests: committed sample CSVs must match the schema registry.

These guard against drift between the processed data files and the table
definitions used to create and load the database.
"""

from __future__ import annotations

import os

import pandas as pd

from flu_pipeline.db.schema import TABLES


def test_processed_files_match_registry_columns(processed_dir):
    for table in TABLES:
        path = os.path.join(processed_dir, table.csv_filename)
        assert os.path.exists(path), f"missing sample file: {table.csv_filename}"
        header = pd.read_csv(path, nrows=0)
        assert list(header.columns) == table.columns, (
            f"{table.csv_filename} columns {list(header.columns)} "
            f"!= registry {table.columns}"
        )


def test_processed_files_non_empty(processed_dir):
    for table in TABLES:
        path = os.path.join(processed_dir, table.csv_filename)
        df = pd.read_csv(path)
        assert len(df) > 0, f"{table.csv_filename} is empty"
