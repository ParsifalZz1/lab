from app.config import Settings


def test_settings_read_environment_values(monkeypatch) -> None:
    monkeypatch.setenv("EXECUTOR_MAX_CONCURRENCY", "12")

    settings = Settings(_env_file=None)

    assert settings.executor_max_concurrency == 12
