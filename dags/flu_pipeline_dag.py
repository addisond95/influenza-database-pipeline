"""Airflow DAG: Washington State influenza surveillance ETL.

Thin orchestration only — all logic lives in the importable ``flu_pipeline``
package, which keeps the DAG readable and the business logic unit-testable.

Flow::

    collect_rhino  ┐
    collect_census ├─> build_processed_tables -> create_db -> ingest -> end
    collect_fluview┘
"""

from __future__ import annotations

from datetime import datetime, timedelta

from airflow.decorators import task
from airflow.models.dag import DAG
from airflow.operators.empty import EmptyOperator
from airflow.utils.trigger_rule import TriggerRule

from flu_pipeline import pipeline

default_args = {
    "owner": "health_data_team",
    "retries": 2,
    "retry_delay": timedelta(minutes=1),
}


@task
def collect_rhino() -> str:
    return pipeline.collect_rhino()


@task
def collect_census() -> str:
    return pipeline.collect_census()


@task
def collect_fluview() -> str:
    return pipeline.collect_fluview()


@task(multiple_outputs=True)
def build_processed_tables(
    census_path: str, rhino_path: str, fluview_path: str
) -> dict[str, str]:
    return pipeline.build_processed_tables(census_path, rhino_path, fluview_path)


@task
def create_database_objects() -> None:
    pipeline.create_database_objects()


@task
def ingest_processed_tables() -> dict[str, int]:
    return pipeline.ingest_processed_tables()


with DAG(
    dag_id="flu_data_pipeline",
    description="Collect, transform, and load WA flu surveillance data.",
    default_args=default_args,
    start_date=datetime(2025, 1, 1),
    schedule="@daily",
    catchup=False,
    tags=["flu", "etl", "public-health"],
) as dag:
    rhino = collect_rhino()
    census = collect_census()
    fluview = collect_fluview()

    processed = build_processed_tables(
        census_path=census, rhino_path=rhino, fluview_path=fluview
    )
    create_db = create_database_objects()
    ingest = ingest_processed_tables()

    end = EmptyOperator(task_id="end", trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS)

    [rhino, census, fluview] >> processed >> create_db >> ingest >> end
