.PHONY: backend-format backend-lint backend-test frontend-lint frontend-test

backend-format:
	uv --directory backend run ruff format .

backend-lint:
	uv --directory backend run ruff check .

backend-test:
	uv --directory backend run pytest

frontend-lint:
	npm --prefix frontend run lint

frontend-test:
	npm --prefix frontend run test
