-- Initializes the PostgreSQL instance on first start.
-- The application database (flu_database) is created by the postgres image from
-- POSTGRES_DB. Here we add a separate database for Airflow metadata so pipeline
-- data and orchestration state never share a schema.

SELECT 'CREATE DATABASE airflow'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'airflow')\gexec

GRANT ALL PRIVILEGES ON DATABASE airflow TO CURRENT_USER;
