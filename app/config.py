"""Application configuration using pydantic-settings."""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "Life Curriculum Assistant"
    debug: bool = False
    secret_key: str = "change-me-in-production"

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/lifecurriculum"
    database_pool_size: int = 10
    database_max_overflow: int = 20

    @property
    def async_database_url(self) -> str:
        """Convert database URL to async format for SQLAlchemy."""
        url = self.database_url
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://") and "+asyncpg" not in url:
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    # Google Gemini
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash-thinking-exp"

    # Anthropic Claude
    anthropic_api_key: str = ""
    claude_model: str = "claude-sonnet-4-20250514"

    # JWT
    jwt_secret_key: str = "change-me-jwt-secret"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # Rate Limiting
    free_daily_chat_limit: int = 20
    premium_daily_chat_limit: int = 200

    # Email
    smtp_host: str = "localhost"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_email: str = "noreply@lifecurriculum.app"
    smtp_from_name: str = "Life Curriculum Assistant"
    smtp_use_tls: bool = True

    # Frontend URL for email links
    frontend_url: str = "http://localhost:8000"

    # Token expiry
    email_verification_expire_hours: int = 24
    password_reset_expire_hours: int = 1


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
