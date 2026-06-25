.PHONY: help install test lint up down logs seed clean

help:                ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS = ":.*?## "}; {printf "  %-12s %s\n", $$1, $$2}'

install:             ## Create a venv and install the package with dev/api extras
	python3 -m venv .venv
	.venv/bin/pip install -e ".[api,dev]"

test:                ## Run the unit test suite
	.venv/bin/pytest -q

up:                  ## Build and start the full Docker stack
	docker compose up -d --build

down:                ## Stop the stack (keeps data volumes)
	docker compose down

clean:               ## Stop the stack and remove all data volumes
	docker compose down -v

logs:                ## Tail logs from all services
	docker compose logs -f

seed:                ## Load the committed sample CSVs into the database
	docker compose exec api python scripts/seed_database.py
