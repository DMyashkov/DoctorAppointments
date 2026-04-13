from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    jwt_secret: str = "dev-secret-change-me"
    jwt_expire_minutes: int = 120
    pbkdf2_iterations: int = 210_000
    app_env: str = "dev"
    database_url: str | None = None


def get_settings() -> Settings:
    return Settings()
