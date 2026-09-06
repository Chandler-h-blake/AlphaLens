from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_DIR = BACKEND_DIR.parent
WORKSPACE_DIR = PROJECT_DIR.parent


def normalize_database_url(value: str | None) -> str | None:
    """Select the installed psycopg driver when a platform supplies a standard URL."""
    if value is None:
        return None
    if value.startswith("postgresql://"):
        return f"postgresql+psycopg://{value.removeprefix('postgresql://')}"
    if value.startswith("postgres://"):
        return f"postgresql+psycopg://{value.removeprefix('postgres://')}"
    return value


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables or the project-root .env."""

    model_config = SettingsConfigDict(
        env_file=PROJECT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "AlphaLens AI Research Platform API"
    app_env: str = "development"
    api_prefix: str = "/api"
    allowed_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    seed_factor_dir: str = "../data/seed/factors"
    seed_research_dir: str = "../data/seed/research/reports"
    seed_industry_rotation_file: str = "../data/seed/industry/industry_rotation.csv"
    seed_industry_mapping_file: str = "../data/seed/research/industry_mapping.csv"
    data_backend: Literal["csv", "database"] = "csv"
    database_url: str | None = None
    llm_provider: Literal["disabled", "openai_compatible"] = "disabled"
    llm_api_key: str | None = None
    llm_api_key_env: str = "OPENAI_API_KEY"
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4.1-mini"
    market_data_provider: Literal["disabled", "eastmoney_public"] = "eastmoney_public"
    market_data_timeout_seconds: float = 12.0
    market_announcement_limit: int = 8
    task_recovery_enabled: bool = True
    public_site_url: str | None = None
    frontend_dist_dir: str = "../frontend-dist"
    public_write_rate_limit_enabled: bool = True
    market_refresh_limit_per_minute: int = 12
    report_generation_limit_per_hour: int = 3
    factor_refresh_limit_per_hour: int = 2

    @field_validator("database_url")
    @classmethod
    def normalize_database_url(cls, value: str | None) -> str | None:
        return normalize_database_url(value)

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    @property
    def seed_factor_path(self) -> Path:
        return self.resolve_backend_path(self.seed_factor_dir)

    @property
    def seed_research_path(self) -> Path:
        return self.resolve_backend_path(self.seed_research_dir)

    @property
    def seed_industry_rotation_path(self) -> Path:
        return self.resolve_backend_path(self.seed_industry_rotation_file)

    @property
    def seed_industry_mapping_path(self) -> Path:
        return self.resolve_backend_path(self.seed_industry_mapping_file)

    @property
    def frontend_dist_path(self) -> Path:
        return self.resolve_backend_path(self.frontend_dist_dir)

    @staticmethod
    def resolve_backend_path(value: str) -> Path:
        configured_path = Path(value).expanduser()
        if configured_path.is_absolute():
            return configured_path
        return (BACKEND_DIR / configured_path).resolve()


@lru_cache
def get_settings() -> Settings:
    return Settings()
