"""Data retention and audit logging services for compliance."""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.config import settings
from app.models.webhook_event import WebhookEvent
from app.models.subscription import PaymentHistory

logger = logging.getLogger(__name__)

class DataRetentionService:
    """Service for managing data retention policies."""

    @staticmethod
    async def cleanup_old_webhook_events(db: AsyncSession, days_to_keep: int = 30):
        """
        Cleanup webhook events older than specified days.

        Args:
            db: Database session
            days_to_keep: Number of days to retain webhook events
        """
        try:
            # Calculate cutoff date
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

            # Delete old webhook events
            result = await db.execute(
                text("DELETE FROM webhook_events WHERE created_at < :cutoff_date"),
                {"cutoff_date": cutoff_date}
            )

            deleted_count = result.rowcount
            logger.info(f"Deleted {deleted_count} old webhook events (older than {days_to_keep} days)")

            await db.commit()
            return deleted_count

        except Exception as e:
            logger.error(f"Error cleaning up old webhook events: {e}")
            await db.rollback()
            raise

    @staticmethod
    async def cleanup_old_payment_history(db: AsyncSession, days_to_keep: int = 365):
        """
        Cleanup payment history older than specified days.

        Args:
            db: Database session
            days_to_keep: Number of days to retain payment history
        """
        try:
            # Calculate cutoff date
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

            # Delete old payment history
            result = await db.execute(
                text("DELETE FROM payment_history WHERE created_at < :cutoff_date"),
                {"cutoff_date": cutoff_date}
            )

            deleted_count = result.rowcount
            logger.info(f"Deleted {deleted_count} old payment history records (older than {days_to_keep} days)")

            await db.commit()
            return deleted_count

        except Exception as e:
            logger.error(f"Error cleaning up old payment history: {e}")
            await db.rollback()
            raise

    @staticmethod
    async def cleanup_old_user_data(db: AsyncSession, days_to_keep: int = 365):
        """
        Cleanup old user data that may be subject to GDPR deletion requests.

        Args:
            db: Database session
            days_to_keep: Number of days to retain user data before soft-deletion
        """
        try:
            # Calculate cutoff date
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

            # Soft-delete old inactive users (mark as deleted but keep data for compliance)
            # This is a simplified example - in practice, you'd need more sophisticated logic
            result = await db.execute(
                text("""
                    UPDATE users
                    SET deleted_at = NOW(),
                        deletion_reason = 'Data retention policy: Automatic cleanup'
                    WHERE deleted_at IS NULL
                    AND updated_at < :cutoff_date
                    AND subscription_tier = 'free'
                """),
                {"cutoff_date": cutoff_date}
            )

            deleted_count = result.rowcount
            logger.info(f"Soft-deleted {deleted_count} old free users (older than {days_to_keep} days)")

            await db.commit()
            return deleted_count

        except Exception as e:
            logger.error(f"Error cleaning up old user data: {e}")
            await db.rollback()
            raise


class AuditLoggingService:
    """Service for audit logging of sensitive operations."""

    @staticmethod
    async def log_payment_operation(
        db: AsyncSession,
        user_id: str,
        operation: str,
        details: dict,
        success: bool = True,
        request_id: Optional[str] = None
    ):
        """
        Log a payment-related operation for audit purposes.

        Args:
            db: Database session
            user_id: User performing the operation
            operation: Type of operation (e.g., 'create_checkout', 'handle_webhook')
            details: Additional details about the operation
            success: Whether the operation was successful
            request_id: Request ID for correlation
        """
        try:
            # In a real implementation, this would store audit logs in a dedicated table
            # For now, we'll just log to the standard logger
            logger.info(
                f"AUDIT: {operation} by user {user_id} - "
                f"Success: {success}, Details: {details}, RequestID: {request_id}"
            )

            # In a production system, you'd want to store these in a dedicated audit_log table
            # with proper indexing and retention policies

            # For enhanced security, you could also store this in a separate audit log table
            # with additional fields like timestamp, IP address, user agent, etc.

        except Exception as e:
            logger.error(f"Error logging audit operation: {e}")
            raise

    @staticmethod
    async def log_webhook_processing(
        db: AsyncSession,
        event_id: str,
        event_type: str,
        status: str,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None
    ):
        """
        Log webhook processing for audit purposes.

        Args:
            db: Database session
            event_id: Stripe event ID
            event_type: Type of webhook event
            status: Processing status
            user_id: User associated with the operation (if any)
            request_id: Request ID for correlation
        """
        try:
            # Log the webhook processing
            logger.info(
                f"AUDIT: Webhook {event_id} ({event_type}) processed - "
                f"Status: {status}, User: {user_id or 'unknown'}, RequestID: {request_id or 'unknown'}"
            )

            # In a production system, you'd want to store this in a dedicated audit log table
            # with proper indexing and retention policies

        except Exception as e:
            logger.error(f"Error logging webhook audit: {e}")
            raise

    @staticmethod
    async def log_security_event(
        db: AsyncSession,
        event_type: str,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        severity: str = "INFO"
    ):
        """
        Log security-related events for audit and monitoring.

        Args:
            db: Database session
            event_type: Type of security event
            user_id: User associated with the event (if any)
            details: Additional details about the event
            severity: Severity level (INFO, WARNING, ERROR, CRITICAL)
        """
        try:
            logger.info(
                f"SECURITY: {severity} - {event_type} - User: {user_id or 'unknown'}, Details: {details or {}}"
            )

            # In a production system, you'd want to store these in a dedicated security log table

        except Exception as e:
            logger.error(f"Error logging security event: {e}")
            raise