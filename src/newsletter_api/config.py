from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "dev"
    database_url: str = "postgresql://postgres:postgres@localhost:5432/newsletter"
    redis_url: str = "redis://localhost:6379/0"
    resend_api_key: str = "re_test"
    resend_from_email: str = "newsletter@newsletter.local"
