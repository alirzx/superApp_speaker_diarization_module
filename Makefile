.PHONY: model build up down logs test smoke
model:
	docker compose --profile setup run --rm model-setup
build:
	docker compose build api ui
up:
	docker compose up -d api ui
down:
	docker compose down
logs:
	docker compose logs -f --tail=100 api ui
test:
	PYTHONPATH=backend pytest -q backend/tests
smoke:
	python backend/scripts/smoke_test.py
