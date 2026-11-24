from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    GITHUB_TOKEN: str | None = None
    GITHUB_REPOSITORY: str = "asamuratatsuya/DevOpsHub"
    PROMETHEUS_URL: str = "http://prometheus-server.monitoring.svc.cluster.local"

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
