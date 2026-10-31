# Relay

A server-side event collector and delivery gateway.

## Current scope

- FastAPI application with a health endpoint.
- Automated code, formatting, type, and API checks.

## Requirements

- Python 3.14
- Poetry 2.4

## Setup

Create the project environment with `poetry env use python3.14`.

Install dependencies with `poetry install`.

## Run

Start the development server with:

`poetry run uvicorn app.main:app --reload`

`GET http://127.0.0.1:8000/health` returns HTTP 200 and `{"status": "ok"}`.

## Checks

Run `./check.sh` from the project directory.

This runs Poetry validation, Ruff linting and formatting checks,
Pyright strict type checking, and pytest.

## Local database

On first setup, copy `.env.example` to `.env`.

Start PostgreSQL with:

`docker compose -p relay -f compose.yaml --env-file .env up -d --wait --wait-timeout 120 postgres`

Check its status with:

`docker compose -p relay -f compose.yaml --env-file .env ps`

The local database is available at `127.0.0.1:55432`.
Its data is stored in the `relay_postgres_data` Docker volume.
