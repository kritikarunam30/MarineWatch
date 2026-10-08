PY ?= python
NPM ?= npm

.PHONY: install up down logs migrate seed replay check lint typecheck test frontend-check

install:
	$(PY) -m pip install -e ".[dev]"
	cd frontend && $(NPM) ci

up:
	docker compose up -d --build
	@echo "API http://localhost:8000/docs  ·  map http://localhost:5173"

down:
	docker compose down

logs:
	docker compose logs -f

migrate:
	$(PY) -m alembic upgrade head

seed:
	$(PY) -m scripts.seed

replay:
	$(PY) -m pipeline.jobs.replay

check: lint typecheck test frontend-check

lint:
	$(PY) -m ruff check .
	$(PY) -m ruff format --check .

typecheck:
	$(PY) -m mypy

test:
	$(PY) -m pytest

frontend-check:
	cd frontend && $(NPM) run lint && $(NPM) run typecheck && $(NPM) test
