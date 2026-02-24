from newsletter_api.config import Settings


def test_settings_loads_required_env(monkeypatch):
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/newsletter")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setenv("RESEND_API_KEY", "re_test")
    settings = Settings()
    assert settings.app_env == "test"
