"""Test Phase 1.6: Environment & Configuration."""

import logging
import os
from pathlib import Path

from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_env_example_exists():
    """Test that .env.example file exists."""
    logger.info("Testing .env.example file existence...")

    env_example_path = Path(".env.example")
    assert env_example_path.exists(), ".env.example file not found"

    logger.info("✓ .env.example file exists")


def test_env_example_content():
    """Test that .env.example contains all required variables."""
    logger.info("Testing .env.example content...")

    required_vars = [
        "ENVIRONMENT",
        "LOG_LEVEL",
        "DATABASE_URL",
        "REDIS_URL",
        "API_HOST",
        "API_PORT",
        "CORS_ORIGINS",
        "ANTHROPIC_API_KEY",
        "FIRECRAWL_API_KEY",
        "REDDIT_CLIENT_ID",
        "REDDIT_CLIENT_SECRET",
        "REDDIT_USER_AGENT",
        "REDDIT_USERNAME",
        "SCRAPE_INTERVAL_HOURS",
        "ANALYSIS_BATCH_SIZE",
    ]

    with open(".env.example", "r") as f:
        content = f.read()

    missing_vars = []
    for var in required_vars:
        if var not in content:
            missing_vars.append(var)

    assert not missing_vars, f"Missing variables in .env.example: {missing_vars}"

    logger.info(f"✓ All {len(required_vars)} required variables present")


def test_configuration_loading():
    """Test that configuration loads correctly from environment."""
    logger.info("Testing configuration loading...")

    # Test that settings object exists
    assert settings is not None
    logger.info("✓ Settings object loaded")

    # Test environment
    assert settings.environment in ["development", "production", "staging"]
    logger.info(f"✓ Environment: {settings.environment}")

    # Test database URL
    assert settings.database_url
    assert "postgresql" in str(settings.database_url)
    logger.info(f"✓ Database URL configured: {str(settings.database_url)[:50]}...")

    # Test Redis URL
    assert settings.redis_url
    assert "redis://" in settings.redis_url
    logger.info(f"✓ Redis URL configured: {settings.redis_url}")

    # Test Redis properties
    assert settings.redis_host
    assert settings.redis_port
    logger.info(f"✓ Redis connection: {settings.redis_host}:{settings.redis_port}")

    # Test API configuration
    assert settings.api_host
    assert settings.api_port
    logger.info(f"✓ API configuration: {settings.api_host}:{settings.api_port}")

    # Test CORS origins
    assert settings.cors_origins
    assert isinstance(settings.cors_origins_list, list)
    logger.info(f"✓ CORS origins: {len(settings.cors_origins_list)} configured")

    # Test task scheduling
    assert settings.scrape_interval_hours > 0
    assert settings.analysis_batch_size > 0
    logger.info(
        f"✓ Task scheduling: scrape_interval={settings.scrape_interval_hours}h, "
        f"batch_size={settings.analysis_batch_size}"
    )


def test_database_url_format():
    """Test that database URL is in correct async format."""
    logger.info("Testing database URL format...")

    db_url = str(settings.database_url)

    # Should use asyncpg driver
    assert "asyncpg" in db_url, "Database URL should use asyncpg driver for async support"

    # Should be postgresql
    assert db_url.startswith("postgresql"), "Database URL should be PostgreSQL"

    # Should have correct port (5432 for Supabase)
    assert ":5432/" in db_url, "Database URL should include port 5432"

    logger.info("✓ Database URL format is correct for async usage")


def test_async_database_url_property():
    """Test async_database_url property."""
    logger.info("Testing async_database_url property...")

    async_url = settings.async_database_url
    assert async_url
    assert isinstance(async_url, str)
    assert "postgresql" in async_url

    logger.info("✓ async_database_url property works")


def test_optional_api_keys():
    """Test optional API keys (may not be set in dev environment)."""
    logger.info("Testing optional API keys...")

    # These may be None in development
    api_keys = {
        "Anthropic": settings.anthropic_api_key,
        "Firecrawl": settings.firecrawl_api_key,
        "Reddit Client ID": settings.reddit_client_id,
        "Reddit Client Secret": settings.reddit_client_secret,
    }

    for key_name, key_value in api_keys.items():
        if key_value:
            logger.info(f"✓ {key_name} is set")
        else:
            logger.warning(f"⚠ {key_name} is not set (optional in dev)")


def run_all_tests():
    """Run all Phase 1.6 tests."""
    logger.info("=" * 60)
    logger.info("Phase 1.6 Test Suite: Environment & Configuration")
    logger.info("=" * 60 + "\n")

    try:
        test_env_example_exists()
        test_env_example_content()
        test_configuration_loading()
        test_database_url_format()
        test_async_database_url_property()
        test_optional_api_keys()

        logger.info("=" * 60)
        logger.info("✓ ALL PHASE 1.6 TESTS PASSED")
        logger.info("=" * 60)
        return True

    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"✗ PHASE 1.6 TESTS FAILED: {e}")
        logger.error("=" * 60)
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
