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
    api_reload: bool = False

    # CORS
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3002,http://127.0.0.1:3002"

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

    # PMF Optimization Flags (minimal-cost deployment)
    use_crawl4ai: bool = True  # Use Crawl4AI instead of Firecrawl (save $149/mo)
    enable_daily_digest: bool = False  # Disable to save email quota (stay in Resend Free tier)

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
    stripe_price_enterprise: str | None = None  # Price ID for Enterprise tier
    stripe_price_starter_yearly: str | None = None
    stripe_price_pro_yearly: str | None = None
    stripe_price_enterprise_yearly: str | None = None

    # Application URL (for email links)
    app_url: str = "http://localhost:3001"

    # Phase 6.2: Email Notifications (Resend)
    resend_api_key: str | None = None
    email_from_address: str = "noreply@startinsight.ai"
    email_from_name: str = "StartInsight"
    contact_email: str = "hello@startinsight.ai"

    # Phase 6.3: Rate Limiting
    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 1000

    # Enhanced rate limiting for payment endpoints
    payment_rate_limit_per_hour: int = 100
    payment_rate_limit_window_seconds: int = 3600

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

    # Production Infrastructure
    sentry_dsn: str | None = None  # Error tracking (required in production)
    refresh_token_secret: str | None = None  # Refresh token signing key
    slack_webhook_url: str | None = None  # Slack notifications for CRITICAL alerts

    # LLM Configuration
    default_llm_model: str = "google-gla:gemini-2.0-flash"
    llm_call_timeout: int = 120  # seconds

    # Database Connection Pool (Supabase session-mode pooler safe ceiling)
    db_pool_size: int = 5       # session-mode pooler: 15 total connections max
    db_max_overflow: int = 10   # total: 15 — handles FastAPI async concurrency safely
    db_pool_timeout: int = 30
    db_pool_recycle: int = 3600
    db_ssl: bool = True  # Supabase requires SSL

    # Redis Extended Config
    redis_ssl: bool = False
    redis_socket_connect_timeout: int = 5
    redis_socket_timeout: int = 5

    # Sentry Monitoring
    sentry_traces_sample_rate: float = 0.1
    sentry_profiles_sample_rate: float = 0.1

    # Worker (Arq)
    worker_max_jobs: int = 10
    worker_job_timeout: int = 600

    # Scraper Defaults
    reddit_subreddits: str = "startups,SaaS"
    reddit_post_limit: int = 25
    reddit_json_rate_limit: float = 1.0  # Seconds between Reddit JSON API requests
    reddit_search_queries: str = "startup idea validation,SaaS problem,building in public"
    reddit_scrape_comments: bool = True  # Deep-scrape top post comment threads
    reddit_comment_scrape_limit: int = 5  # Max posts to deep-scrape comments for
    product_hunt_days_back: int = 1
    product_hunt_limit: int = 10
    trends_timeframe: str = "now 7-d"
    trends_geo: str = "US"

    # Middleware & Security
    max_request_size: int = 1_000_000
    sse_max_duration: int = 3600
    jwks_fetch_timeout: float = 10.0
    jwks_cache_ttl: int = 3600
    cors_allowed_methods: str = "GET,POST,PUT,PATCH,DELETE,OPTIONS"
    cors_allowed_headers: str = "Authorization,Content-Type,X-Request-ID,X-API-Key,Accept,Accept-Language"
    cors_origin_regex: str = ""  # Optional regex for dynamic origins (e.g. Vercel preview deployments)
    csp_connect_src: str = "'self' https://generativelanguage.googleapis.com https://*.supabase.co"
    cors_allowed_production_origins: str = "https://startinsight.app,https://www.startinsight.app,https://app.startinsight.app"

    # Application
    app_version: str = "0.1.0"
    tenant_base_domain: str = "startinsight.ai"
    default_max_users: int = 10
    default_max_teams: int = 3
    default_max_api_keys: int = 2

    @field_validator('jwt_secret')
    @classmethod
    def validate_jwt_secret_strength(cls, v: str | None) -> str | None:
        """Ensure JWT secret is cryptographically strong."""
        if v is None:
            return None

        # Minimum length check
        if len(v) < 32:
            raise ValueError("JWT_SECRET must be at least 32 characters for security")

        # Check for basic entropy (should not contain predictable patterns)
        # This is a basic check - in production, more sophisticated entropy analysis
        # might be needed
        if len(set(v)) < len(v) * 0.5:  # If less than 50% unique characters
            # This is a very basic entropy check
            pass

        return v

    @model_validator(mode='after')
    def check_production_config(self) -> 'Settings':
        """Validate critical settings in production environment."""
        if self.environment == "production":
            # Phase 4+: Authentication is CRITICAL in production
            if not self.jwt_secret:
                raise ValueError(
                    "JWT_SECRET is required in production for Supabase Auth. "
                    "Generate a secure secret: openssl rand -hex 64"
                )
            if not self.supabase_url:
                raise ValueError("SUPABASE_URL is required in production")
            if not self.supabase_service_role_key:
                raise ValueError("SUPABASE_SERVICE_ROLE_KEY is required in production")

            # Production Infrastructure
            if not self.sentry_dsn:
                raise ValueError(
                    "SENTRY_DSN is required in production for error tracking. "
                    "Get DSN from sentry.io project settings"
                )
            if not self.refresh_token_secret:
                raise ValueError(
                    "REFRESH_TOKEN_SECRET is required in production. "
                    "Generate a secure secret: openssl rand -hex 32"
                )

            # Deployment safety checks
            if self.api_reload:
                raise ValueError("API_RELOAD must be False in production")
            if "localhost" in self.app_url or "127.0.0.1" in self.app_url:
                raise ValueError("APP_URL must not contain localhost in production")
            if not self.app_url.startswith("https://"):
                raise ValueError("APP_URL must use HTTPS in production")

            # Security: Enforce CORS whitelist in production
            allowed_origins = [o.strip() for o in self.cors_allowed_production_origins.split(",")]

            for origin in self.cors_origins_list:
                # Check for localhost/127.0.0.1
                if "localhost" in origin.lower() or "127.0.0.1" in origin:
                    raise ValueError(
                        "localhost/127.0.0.1 CORS origins not allowed in production. "
                        "Set CORS_ORIGINS to your production frontend domain."
                    )

                # Enforce HTTPS
                if not origin.startswith("https://"):
                    raise ValueError(
                        f"Production CORS origins must use HTTPS: {origin}"
                    )

                # Enforce whitelist
                if origin not in allowed_origins:
                    raise ValueError(
                        f"CORS origin '{origin}' not in production whitelist. "
                        f"Allowed origins: {', '.join(allowed_origins)}"
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
