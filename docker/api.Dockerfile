# Lightweight image for the Flask analytics API.
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PROCESSED_DIR=/app/processed_files

# Package metadata and source (psycopg2-binary bundles libpq, so no system deps).
COPY pyproject.toml README.md ./
COPY flu_pipeline ./flu_pipeline
COPY api ./api

RUN pip install ".[api]"

# Sample data and helper scripts for the optional `make seed` demo workflow.
COPY processed_files ./processed_files
COPY scripts ./scripts

EXPOSE 5000

# Serve with gunicorn; debug mode is never enabled in the image.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "60", "api.app:app"]
