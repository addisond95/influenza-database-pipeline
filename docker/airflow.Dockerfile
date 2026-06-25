# Airflow image extended with the flu_pipeline package and its runtime deps.
# Building on the official image keeps Airflow's own dependency set intact.
FROM apache/airflow:2.9.3-python3.11

# Install runtime libraries using Airflow's published constraints so the
# existing Airflow dependency tree is never broken, then install the package.
COPY --chown=airflow:root pyproject.toml README.md /opt/airflow/app/
COPY --chown=airflow:root flu_pipeline /opt/airflow/app/flu_pipeline/

RUN pip install --no-cache-dir \
        "pandas>=2.0" "requests>=2.31" "psycopg2-binary>=2.9" "python-dotenv>=1.0" \
        --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.9.3/constraints-3.11.txt" \
    && pip install --no-cache-dir --no-deps /opt/airflow/app
