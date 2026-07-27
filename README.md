# ModelFlow

ModelFlow is a dynamic hybrid DAG scheduler for a network of model workers.

## Prerequisites

- Python 3.12, managed with [uv](https://docs.astral.sh/uv/)
- Node.js 20 and npm 10

## Install

```bash
uv --directory backend sync --group dev
npm --prefix frontend install
```

## Run The API

```bash
make db-upgrade
uv --directory backend run uvicorn app.main:app --reload
```

## Checks

```bash
make backend-format
make backend-lint
make backend-test
make frontend-lint
make frontend-test
```
