.PHONY: install test lint format up down migrate ingest

install:
	pip install -e ".[dev]"

test:
	pytest tests/ -v

lint:
	ruff check src/ tests/
	mypy src/

format:
	ruff format src/ tests/

up:
	docker compose up -d

down:
	docker compose down

migrate:
	alembic upgrade head

ingest:
	python -m drug_discovery.ingestion.run

run:
	uvicorn drug_discovery.api.main:app --reload --port 8000
