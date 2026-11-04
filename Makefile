.PHONY: model build up down logs test smoke
# The one-shot model-setup is also automatically run as a dependency of API.
model:
	docker compose run --build --rm model-setup
build:
	docker compose build
up:
	docker compose up --build -d
down:
	docker compose down
logs:
	docker compose logs -f --tail=150 api ui model-setup
test:
	PYTHONPATH=backend pytest -q backend/tests
smoke:
	python backend/scripts/smoke_test.py
