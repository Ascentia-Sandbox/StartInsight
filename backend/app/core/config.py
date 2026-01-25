"""Application configuration using Pydantic Settings."""

from pydantic import PostgresDsn, field_validator, model_validator
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
    google_api_key: str | None = None  # Primary: Gemini API
    anthropic_api_key: str | None = None  # Fallback: Claude API
    openai_api_key: str | None = None  # Fallback: GPT-4o

    # Web Scraping APIs
    firecrawl_api_key: str | None = None
    reddit_client_id: str | None = None
    reddit_client_secret: str | None = None
    reddit_user_agent: str = "StartInsight Bot v1.0"
    reddit_username: str | None = None

    # Task Scheduling
    scrape_interval_hours: int = 6
    analysis_batch_size: int = 10

    # Supabase (Phase 4+ - Asia Pacific)
    supabase_url: str | None = None
    supabase_anon_key: str | None = None
    supabase_service_role_key: str | None = None

    # JWT Configuration (for Supabase Auth verification)
    jwt_secret: str | None = None
    jwt_algorithm: str = "HS256"

    # Phase 6.1: Stripe Payment Integration
    stripe_secret_key: str | None = None
    stripe_publishable_key: str | None = None
    stripe_webhook_secret: str | None = None
    stripe_price_starter: str | None = None  # Price ID for Starter tier
    stripe_price_pro: str | None = None  # Price ID for Pro tier

    # Phase 6.2: Email Notifications (Resend)
    resend_api_key: str | None = None
    email_from_address: str = "noreply@startinsight.ai"
    email_from_name: str = "StartInsight"

    # Phase 6.3: Rate Limiting
    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 1000

    # Phase 7.1: Twitter/X Integration
    twitter_api_key: str | None = None
    twitter_api_secret: str | None = None
    twitter_access_token: str | None = None
    twitter_access_secret: str | None = None
    twitter_bearer_token: str | None = None

    # Phase 7.2: Public API
    public_api_rate_limit: int = 100  # Requests per hour per API key

    # Phase 7.3: Multi-tenancy
    default_tenant_id: str = "default"
    enable_multi_tenancy: bool = False

    @field_validator('jwt_secret')
    @classmethod
    def validate_jwt_secret_length(cls, v: str | None) -> str | None:
        """Ensure JWT secret is strong (min 32 characters)."""
        if v and len(v) < 32:
            raise ValueError("JWT_SECRET must be at least 32 characters for security")
        return v

    @model_validator(mode='after')
    def check_production_config(self) -> 'Settings':
        """Validate critical settings in production environment."""
        if self.environment == "production":
            # Phase 4+: Authentication is CRITICAL in production
            if not self.jwt_secret:
                raise ValueError(
                    "JWT_SECRET is required in production for Supabase Auth. "
                    "Generate a secure secret: openssl rand -hex 32"
                )
            if not self.supabase_url:
                raise ValueError("SUPABASE_URL is required in production")
            if not self.supabase_service_role_key:
                raise ValueError("SUPABASE_SERVICE_ROLE_KEY is required in production")

            # Security: Prevent localhost CORS in production
            if "localhost" in self.cors_origins.lower() or "127.0.0.1" in self.cors_origins:
                raise ValueError(
                    "localhost/127.0.0.1 CORS origins not allowed in production. "
                    "Set CORS_ORIGINS to your production frontend domain."
                )

        return self

    @property
    def cors_origins_list(self) -> list[str]:
        """Get CORS origins as a list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def async_database_url(self) -> str:
        """Get the async database URL string."""
        return str(self.database_url)

    @property
    def redis_host(self) -> str:
        """Extract Redis host from redis_url."""
        # Parse redis://host:port format
        if "://" in self.redis_url:
            url_parts = self.redis_url.split("://")[1]
            host_port = url_parts.split("/")[0]
            if ":" in host_port:
                return host_port.split(":")[0]
            return host_port
        return "localhost"

    @property
    def redis_port(self) -> int:
        """Extract Redis port from redis_url."""
        # Parse redis://host:port format
        if "://" in self.redis_url:
            url_parts = self.redis_url.split("://")[1]
            host_port = url_parts.split("/")[0]
            if ":" in host_port:
                return int(host_port.split(":")[1])
        return 6379


# Global settings instance
settings = Settings()
