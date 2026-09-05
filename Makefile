.PHONY: dev migrate seed bench test

dev:
	docker compose -f infra/docker-compose.yml up --build

migrate:
	alembic upgrade head

seed:
	python data/seed/seed.py

bench:
	python -m packages.engine.bench

test:
	pytest
