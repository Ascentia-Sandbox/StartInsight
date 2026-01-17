"""Application configuration using Pydantic Settings."""

from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Environment
    environment: str = "development"
    log_level: str = "info"

    # Database
    database_url: PostgresDsn

    # Redis
    redis_url: str = "redis://localhost:6379"

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True

    # CORS
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    # AI & LLM APIs
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None

    # Web Scraping APIs
    firecrawl_api_key: str | None = None
    reddit_client_id: str | None = None
    reddit_client_secret: str | None = None
    reddit_user_agent: str = "StartInsight Bot v1.0"

    # Task Scheduling
    scrape_interval_hours: int = 6
    analysis_batch_size: int = 10

    @property
    def cors_origins_list(self) -> list[str]:
        """Get CORS origins as a list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def async_database_url(self) -> str:
        """Get the async database URL string."""
        return str(self.database_url)


# Global settings instance
settings = Settings()
