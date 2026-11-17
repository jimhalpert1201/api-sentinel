"""
Application configuration loaded from environment variables.

Uses pydantic-settings to provide type-safe, validated configuration
with automatic .env file loading.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""

    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ---- Application ----
    app_name: str = "API Sentinel"
    app_version: str = "0.1.0"
    debug: bool = False

    # ---- Database ----
    database_url: str = "postgresql://sentinel:sentinel@localhost:5432/api_sentinel"

    # ---- Redis ----
    redis_url: str = "redis://localhost:6379/0"

    # ---- JWT Authentication ----
    jwt_secret_key: str = "CHANGE_ME_TO_A_RANDOM_SECRET"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # ---- CORS ----
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        """Parse comma-separated CORS origins into a list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    # ---- Monitoring Defaults ----
    default_check_interval_seconds: int = 60
    default_check_timeout_seconds: int = 30
    incident_threshold_failures: int = 3
    incident_recovery_threshold: int = 3


# Singleton instance — import this throughout the application
settings = Settings()
