"""Data retention cleanup worker for StartInsight."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

from app.core.config import settings
from app.db.session import async_engine
from app.services.compliance_service import DataRetentionService

logger = logging.getLogger(__name__)


class DataRetentionWorker:
    """Worker for managing data retention policies."""

    def __init__(self, db_url: Optional[str] = None):
        """
        Initialize the data retention worker.

        Args:
            db_url: Database URL (if different from settings)
        """
        self.db_url = db_url or settings.async_database_url

    async def run_cleanup(self, webhook_days: int = 30, payment_days: int = 365, user_days: int = 365):
        """
        Run data retention cleanup for webhook events, payment history, and user data.

        Args:
            webhook_days: Days to keep webhook events
            payment_days: Days to keep payment history
            user_days: Days to keep user data before soft-deletion
        """
        logger.info("Starting data retention cleanup...")

        try:
            # Create a new database session
            async with async_engine.begin() as conn:
                # Cleanup webhook events
                webhook_count = await DataRetentionService.cleanup_old_webhook_events(
                    conn, webhook_days
                )

                # Cleanup payment history
                payment_count = await DataRetentionService.cleanup_old_payment_history(
                    conn, payment_days
                )

                # Cleanup old user data
                user_count = await DataRetentionService.cleanup_old_user_data(
                    conn, user_days
                )

                logger.info(
                    f"Data retention cleanup completed: "
                    f"{webhook_count} webhook events deleted, "
                    f"{payment_count} payment history records deleted, "
                    f"{user_count} old user records soft-deleted"
                )

        except Exception as e:
            logger.error(f"Error during data retention cleanup: {e}")
            raise

    async def schedule_cleanup(self, interval_minutes: int = 1440):
        """
        Schedule periodic data retention cleanup (runs every 24 hours by default).

        Args:
            interval_minutes: Interval between cleanup runs in minutes
        """
        logger.info(f"Scheduling data retention cleanup every {interval_minutes} minutes")

        while True:
            try:
                await self.run_cleanup()
                logger.info(f"Next cleanup scheduled in {interval_minutes} minutes")
                await asyncio.sleep(interval_minutes * 60)
            except Exception as e:
                logger.error(f"Error in scheduled cleanup: {e}")
                # Wait a bit before retrying
                await asyncio.sleep(60)


# Example usage:
# worker = DataRetentionWorker()
# await worker.run_cleanup()