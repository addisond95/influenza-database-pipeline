# Washington State Influenza Surveillance Pipeline

An end-to-end data engineering project that ingests respiratory-illness
surveillance data from three public sources, normalizes it into a relational
PostgreSQL schema, and serves it through an analytics API and dashboard. The
whole stack runs locally with a single `docker compose up`.

| | |
| --- | --- |
| **Orchestration** | Apache Airflow (TaskFlow API) |
| **Storage** | PostgreSQL (5 normalized tables) |
| **Transform** | Pure-function pandas pipeline (`flu_pipeline` package) |
| **Serving** | Flask app factory + Gunicorn, JSON reports, CSV export, HTML dashboard |
| **Packaging** | `pyproject.toml`, pytest suite, Docker images, Makefile |

---

## Architecture

```
┌──────────────────────────────────────┐
│             Data Sources             │
│  • WA DOH RHINO (county respiratory) │
│  • WA Census (population density)    │
│  • CDC FluView via Delphi Epidata    │
└───────────────────┬──────────────────┘
                    │  flu_pipeline.sources
                    ▼
┌──────────────────────────────────────┐
│        Transform (pure functions)    │  flu_pipeline.transform
│  county_region · temporal · illness  │
│        healthcare · historics        │
└───────────────────┬──────────────────┘
                    │  orchestrated by Airflow DAG
                    ▼
┌──────────────────────────────────────┐
│      PostgreSQL (flu_schema)         │  flu_pipeline.db
│   COPY → staging → INSERT ON CONFLICT │
└───────────────────┬──────────────────┘
                    │  SQLAlchemy
                    ▼
┌──────────────────────────────────────┐
│       Flask API + Dashboard          │  api/
│  /api/reports/* · /api/export/csv    │
└──────────────────────────────────────┘
```

The pipeline is split into small, independently testable layers. `sources/`
fetches and lightly cleans raw data, `transform/` contains pure functions that
turn raw frames into the five normalized tables, and `db/` owns a single
`TableSpec` registry that drives both the DDL and the bulk CSV loader. The
Airflow DAG and the standalone seed script both call the same
`flu_pipeline.pipeline` orchestration functions, so there is one source of truth
for the data flow.

---

## Quick Start

### Option A — Full stack with Airflow (the real pipeline)

```bash
cp .env.example .env          # adjust credentials if you like
make up                       # docker compose up -d --build
```

This builds and starts:

| Service | URL | Notes |
| --- | --- | --- |
| Airflow webserver | http://localhost:8080 | user `admin` / pass `admin` |
| Flask API + dashboard | http://localhost:5001/viewer | published from container port 5000 |
| PostgreSQL | `localhost:5432` | database `flu_database` |

Give Airflow ~30–60s to initialize, then open the UI, enable the
`flu_data_pipeline` DAG, and trigger a run. It fetches all three sources,
builds the tables, creates the schema, and loads the data automatically (it is
scheduled `@daily` thereafter).

### Option B — Demo with the committed sample data (fastest)

The repo ships a small, real sample of each table in `processed_files/`. To
load it without running Airflow:

```bash
make up        # start the stack
make seed      # docker compose exec api python scripts/seed_database.py
```

Then visit http://localhost:5001/viewer or hit the API directly:

```bash
curl http://localhost:5001/health
curl http://localhost:5001/api/reports/historical-summary
```

---

## Local development (no Docker)

```bash
make install          # python3 -m venv .venv && pip install -e ".[api,dev]"
make test             # run the pytest suite
```

The test suite (`tests/`) covers the transform functions, the source
cleaners, the API routes, and a contract test that asserts the committed sample
CSVs match the column schema declared in the `TableSpec` registry — so the
sample data can never silently drift from the database schema.

---

## Project Layout

```
flu_pipeline/            # installable package — the core ETL logic
  config.py              #   env-based settings (no hardcoded credentials)
  sources/               #   rhino.py · census.py · fluview.py  (fetch + clean)
  transform/             #   one module per output table (pure functions)
  db/                    #   engine.py · schema.py (TableSpec registry) · load.py
  pipeline.py            #   orchestration entrypoints
dags/
  flu_pipeline_dag.py    # Airflow TaskFlow DAG (dag_id: flu_data_pipeline)
api/
  __init__.py            # create_app() factory
  routes.py              # blueprint: reports, CSV export, dashboard
  queries.py             # parameter-free analytical SQL
  dashboard.py           # single-file HTML dashboard
scripts/
  seed_database.py       # load committed sample CSVs into the DB
tests/                   # pytest suite (transforms, sources, API, contract)
docker/                  # postgres-init.sql · api.Dockerfile · airflow.Dockerfile
processed_files/         # committed sample data for the demo path
docker-compose.yml
pyproject.toml
Makefile
```

---

## Database Schema

Five normalized tables live in the `flu_schema` schema and are created in
foreign-key dependency order:

| Table | Description |
| --- | --- |
| `county_region` | County names, ACH region, 2020 population density |
| `temporal` | Week-ending dates, epiweek ids, flu seasons |
| `illness` | County-level respiratory illness metrics per week |
| `healthcare` | Hospitalization and ER-visit rates per region/week |
| `historics` | Historical CDC FluView season summaries |

Loading uses Postgres `COPY` into a temporary staging table followed by
`INSERT … ON CONFLICT DO NOTHING`, making every load idempotent and safe to
re-run.

---

## API Endpoints

| Endpoint | Description |
| --- | --- |
| `GET /` | API metadata |
| `GET /health` | Database connectivity check |
| `GET /viewer` | Interactive HTML dashboard |
| `GET /api/reports/weekly-trends` | Weekly positivity by illness type (JSON) |
| `GET /api/reports/healthcare-impact` | Hospitalization / ER metrics by ACH region (JSON) |
| `GET /api/reports/historical-summary` | Peak vs. average ILI by season (JSON) |
| `GET /api/export/csv?table=<name>` | Stream any table as CSV |

```bash
curl "http://localhost:5001/api/export/csv?table=illness" -o illness.csv
```

---

## Configuration

All settings are read from environment variables (see `.env.example`); nothing
is hardcoded. Copy the example file and edit as needed:

```bash
cp .env.example .env
```

| Variable | Default | Purpose |
| --- | --- | --- |
| `APP_DB_USER` / `APP_DB_PASSWORD` | `fluuser` / `flupass` | App DB credentials |
| `APP_DB_HOST` / `APP_DB_PORT` | `postgres` / `5432` | DB location |
| `APP_DB_NAME` | `flu_database` | Database name |
| `API_PORT` | `5001` | Host port for the dashboard |
| `AIRFLOW_ADMIN_USER` / `_PASSWORD` | `admin` / `admin` | Airflow login |
| `AIRFLOW_UID` | `50000` | Set to `$(id -u)` on Linux to avoid file-permission issues |

---

## Make Targets

```
make help       Show all targets
make install    Create a venv and install with dev/api extras
make test       Run the unit test suite
make up         Build and start the full Docker stack
make seed       Load the committed sample CSVs into the database
make logs       Tail logs from all services
make down       Stop the stack (keeps data volumes)
make clean      Stop the stack and remove all data volumes
```

---

## Data Sources

- **WA DOH RHINO** — Washington respiratory illness surveillance
  ([dashboard](https://doh.wa.gov/data-statistical-reports/diseases-and-chronic-conditions/communicable-disease-surveillance-data/respiratory-illness-data-dashboard))
- **WA Census** — county population density 2000–2020
  ([data.wa.gov](https://data.wa.gov/Demographics/Population-Density-By-County-2000-2020/e6ip-wkqq))
- **CDC FluView** — national flu surveillance via the Delphi Epidata API
  ([api.delphi.cmu.edu](https://api.delphi.cmu.edu/epidata/fluview/))

---

## Troubleshooting

**Dashboard shows "no data".** Load data first — either trigger the
`flu_data_pipeline` DAG in Airflow, or run `make seed` for the sample dataset.

**Airflow UI not responding.** Allow 30–60s after `make up` for the scheduler
and webserver to initialize; check progress with `make logs`.

**Port already in use.** Change `API_PORT` in `.env` (host side) or remap the
Airflow/Postgres ports in `docker-compose.yml`.

**File-permission errors on Linux.** Set `AIRFLOW_UID` to your host user id:
`echo "AIRFLOW_UID=$(id -u)" >> .env`.

---

## System Requirements

- Docker 20.10+ and Docker Compose v2
- ~4 GB RAM (8 GB recommended when running Airflow)
- ~2 GB disk for images and data

## License

Released for educational and public-health surveillance purposes.
