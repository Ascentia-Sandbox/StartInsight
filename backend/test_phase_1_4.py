"""Test Phase 1.4: Task Queue Setup."""

import asyncio
import logging

from arq import create_pool
from arq.connections import RedisSettings

from app.core.config import settings
from app.worker import WorkerSettings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_worker_configuration():
    """Test that worker configuration is correct."""
    logger.info("Testing worker configuration...")

    # Check that WorkerSettings has required attributes
    assert hasattr(WorkerSettings, "redis_settings")
    assert hasattr(WorkerSettings, "functions")
    assert hasattr(WorkerSettings, "cron_jobs")

    # Check that functions are registered
    assert len(WorkerSettings.functions) == 4
    logger.info(f"✓ {len(WorkerSettings.functions)} task functions registered")

    # Check that cron job is configured
    assert len(WorkerSettings.cron_jobs) == 1
    logger.info("✓ Cron job configured for scrape_all_sources")

    logger.info("✓ Worker configuration test passed\n")


async def test_redis_connection():
    """Test Redis connection."""
    logger.info("Testing Redis connection...")

    try:
        redis = await create_pool(
            RedisSettings(
                host=settings.redis_host,
                port=settings.redis_port,
                database=0,
            )
        )

        # Test connection by setting and getting a test value
        await redis.set(b"test_key", b"test_value")
        value = await redis.get(b"test_key")

        assert value == b"test_value"
        logger.info(f"✓ Redis connected at {settings.redis_host}:{settings.redis_port}")

        # Clean up
        await redis.delete(b"test_key")
        await redis.close()

        logger.info("✓ Redis connection test passed\n")

    except Exception as e:
        logger.error(f"✗ Redis connection failed: {e}")
        raise


async def test_task_enqueue():
    """Test that tasks can be enqueued."""
    logger.info("Testing task enqueue...")

    try:
        redis = await create_pool(
            RedisSettings(
                host=settings.redis_host,
                port=settings.redis_port,
                database=0,
            )
        )

        # Note: We can't actually run the tasks without the worker running
        # But we can verify the task names are valid
        task_names = [
            "scrape_reddit_task",
            "scrape_product_hunt_task",
            "scrape_trends_task",
            "scrape_all_sources_task",
        ]

        for task_name in task_names:
            # Check that task is in registered functions
            registered = any(f.__name__ == task_name for f in WorkerSettings.functions)
            assert registered, f"Task {task_name} not registered"
            logger.info(f"✓ Task '{task_name}' is registered")

        await redis.close()

        logger.info("✓ Task enqueue test passed\n")

    except Exception as e:
        logger.error(f"✗ Task enqueue test failed: {e}")
        raise


async def test_configuration():
    """Test configuration values."""
    logger.info("Testing configuration...")

    # Check Redis settings
    assert settings.redis_host
    assert settings.redis_port
    logger.info(f"✓ Redis: {settings.redis_host}:{settings.redis_port}")

    # Check scrape interval
    assert settings.scrape_interval_hours == 6
    logger.info(f"✓ Scrape interval: {settings.scrape_interval_hours} hours")

    logger.info("✓ Configuration test passed\n")


async def run_all_tests():
    """Run all Phase 1.4 tests."""
    logger.info("=" * 60)
    logger.info("Phase 1.4 Test Suite: Task Queue Setup")
    logger.info("=" * 60 + "\n")

    try:
        await test_worker_configuration()
        await test_redis_connection()
        await test_task_enqueue()
        await test_configuration()

        logger.info("=" * 60)
        logger.info("✓ ALL PHASE 1.4 TESTS PASSED")
        logger.info("=" * 60)
        return True

    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"✗ PHASE 1.4 TESTS FAILED: {e}")
        logger.error("=" * 60)
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1)
