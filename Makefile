.PHONY: backend-format backend-lint backend-test db-upgrade frontend-lint frontend-test

backend-format:
	uv --directory backend run ruff format .

backend-lint:
	uv --directory backend run ruff check .

backend-test:
	uv --directory backend run pytest

db-upgrade:
	uv --directory backend run alembic upgrade head

frontend-lint:
	npm --prefix frontend run lint

frontend-test:
	npm --prefix frontend run test
