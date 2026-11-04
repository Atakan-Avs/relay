from pathlib import Path

from pytest import MonkeyPatch
from sqlalchemy.engine import make_url

from app.config import Settings


def test_settings_load_relay_env_and_preserve_password(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    values = {
        "RELAY_DB_HOST": "127.0.0.1",
        "RELAY_DB_PORT": "55432",
        "RELAY_DB_NAME": "relay_test",
        "RELAY_DB_USER": "relay_test",
        "RELAY_DB_PASSWORD": "p@ss:/%word",
    }

    for name in values:
        monkeypatch.delenv(name, raising=False)

    monkeypatch.setenv("DB_HOST", "unrelated.invalid")
    monkeypatch.chdir(tmp_path)

    (tmp_path / ".env").write_text(
        "\n".join(f"{name}={value}" for name, value in values.items()) + "\n",
        encoding="utf-8",
    )

    settings = Settings.model_validate({})
    url = make_url(settings.database_url.render_as_string(hide_password=False))

    assert url.drivername == "postgresql+psycopg"
    assert url.host == "127.0.0.1"
    assert url.port == 55432
    assert url.database == "relay_test"
    assert url.username == "relay_test"
    assert url.password == "p@ss:/%word"
