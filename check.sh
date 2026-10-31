#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

poetry check
poetry run ruff check .
poetry run ruff format --check .
poetry run pyright
poetry run python -m pytest
