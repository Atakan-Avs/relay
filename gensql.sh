#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

DATABASE_URL=$(poetry run python - <<'PY'
from app.config import Settings

url = Settings.model_validate({}).database_url.set(drivername="postgresql")
print(url.render_as_string(hide_password=False))
PY
)
export DATABASE_URL

poetry run sql-infer generate sql-infer.toml
poetry run ruff check --fix --config 'lint.extend-safe-fixes = ["F841"]' app/async_queries.py
poetry run ruff format app/async_queries.py
