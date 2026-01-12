.PHONY: help install format lint typecheck test test-unit test-integration precommit dev dev-host clean-db smoke

help:
	@echo "Targets:"
	@echo "  install           Install dependencies"
	@echo "  dev               Run FastAPI locally (reload) reading .env"
	@echo "  dev-host          Run FastAPI on 0.0.0.0:8000 (reload) reading .env"
	@echo "  test              Run all tests"
	@echo "  test-unit         Run unit tests"
	@echo "  test-integration  Run integration tests"
	@echo "  precommit         Run pre-commit for all files"
	@echo "  format            Format code (black)"
	@echo "  lint              Lint (flake8)"
	@echo "  typecheck         Type check (mypy)"
	@echo "  smoke             Run SQLite smoke script"
	@echo "  clean-db          Remove local SQLite database files"

install:
	poetry install

dev:
	poetry run uvicorn zkybank.infrastructure.main:app --reload --env-file .env

dev-host:
	poetry run uvicorn zkybank.infrastructure.main:app --reload --env-file .env --host 0.0.0.0 --port 8000

test:
	poetry run pytest -v

test-unit:
	poetry run pytest -v tests/unit

test-integration:
	poetry run pytest -v tests/integration

precommit:
	poetry run pre-commit run --all-files

format:
	poetry run black .

lint:
	poetry run flake8 .

typecheck:
	poetry run mypy .

smoke:
	poetry run python -m zkybank.scripts.smoke_sqlite

clean-db:
	rm -f data/zkybank.db data/zkybank.db-journal data/zkybank.db-wal data/zkybank.db-shm

concurrency:
	poetry run python -m zkybank.scripts.concurrency
