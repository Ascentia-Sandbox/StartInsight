"""Quality alerting service.

This module monitors quality metrics and triggers alerts when
thresholds are breached.

Alert channels:
- Logger (always)
- Sentry (if configured)
- Slack (CRITICAL alerts only, if webhook configured)
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any

import httpx

from app.core.config import settings
from app.services.quality_metrics import QualityMetrics

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Alert:
    """Quality alert data structure."""

    id: str
    severity: AlertSeverity
    title: str
    message: str
    metric_name: str
    threshold: float
    actual_value: float
    timestamp: datetime

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "severity": self.severity.value,
            "title": self.title,
            "message": self.message,
            "metric_name": self.metric_name,
            "threshold": self.threshold,
            "actual_value": self.actual_value,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class AlertThreshold:
    """Configuration for an alert threshold."""

    metric_name: str
    operator: str  # "lt" (less than) or "gt" (greater than)
    threshold: float
    severity: AlertSeverity
    title: str
    message_template: str


class QualityAlertService:
    """
    Monitor quality metrics and trigger alerts.

    Configurable thresholds for each metric type.
    Supports multiple alert channels.
    """

    # Default thresholds
    DEFAULT_THRESHOLDS: list[AlertThreshold] = [
        # Validation pass rate
        AlertThreshold(
            metric_name="validation_pass_rate",
            operator="lt",
            threshold=0.80,
            severity=AlertSeverity.WARNING,
            title="Low Validation Pass Rate",
            message_template=(
                "Validation pass rate is {actual:.1%}, "
                "below threshold of {threshold:.1%}. "
                "Check LLM output quality and prompt effectiveness."
            ),
        ),
        AlertThreshold(
            metric_name="validation_pass_rate",
            operator="lt",
            threshold=0.60,
            severity=AlertSeverity.CRITICAL,
            title="Critical Validation Pass Rate",
            message_template=(
                "CRITICAL: Validation pass rate dropped to {actual:.1%}. "
                "Immediate investigation required."
            ),
        ),
        # Duplicate rate
        AlertThreshold(
            metric_name="duplicate_rate",
            operator="gt",
            threshold=0.20,
            severity=AlertSeverity.WARNING,
            title="High Duplicate Rate",
            message_template=(
                "Duplicate rate is {actual:.1%}, "
                "above threshold of {threshold:.1%}. "
                "Check scraper deduplication logic."
            ),
        ),
        AlertThreshold(
            metric_name="duplicate_rate",
            operator="gt",
            threshold=0.40,
            severity=AlertSeverity.ERROR,
            title="Excessive Duplicate Rate",
            message_template=(
                "Duplicate rate reached {actual:.1%}. "
                "Significant data quality issue."
            ),
        ),
        # LLM error rate
        AlertThreshold(
            metric_name="llm_error_rate",
            operator="gt",
            threshold=0.10,
            severity=AlertSeverity.WARNING,
            title="High LLM Error Rate",
            message_template=(
                "LLM error rate is {actual:.1%}, "
                "above threshold of {threshold:.1%}. "
                "Check API status and rate limits."
            ),
        ),
        AlertThreshold(
            metric_name="llm_error_rate",
            operator="gt",
            threshold=0.25,
            severity=AlertSeverity.CRITICAL,
            title="Critical LLM Error Rate",
            message_template=(
                "CRITICAL: LLM error rate at {actual:.1%}. "
                "Analysis pipeline may be degraded."
            ),
        ),
        # Average relevance score
        AlertThreshold(
            metric_name="avg_relevance_score",
            operator="lt",
            threshold=0.50,
            severity=AlertSeverity.WARNING,
            title="Low Average Relevance",
            message_template=(
                "Average relevance score is {actual:.2f}, "
                "below threshold of {threshold:.2f}. "
                "Signal quality may be degraded."
            ),
        ),
        # Processing backlog
        AlertThreshold(
            metric_name="processing_backlog",
            operator="gt",
            threshold=100,
            severity=AlertSeverity.WARNING,
            title="High Processing Backlog",
            message_template=(
                "Processing backlog is {actual:.0f} signals, "
                "above threshold of {threshold:.0f}. "
                "Consider scaling worker capacity."
            ),
        ),
        AlertThreshold(
            metric_name="processing_backlog",
            operator="gt",
            threshold=500,
            severity=AlertSeverity.ERROR,
            title="Critical Processing Backlog",
            message_template=(
                "Processing backlog reached {actual:.0f} signals. "
                "Worker scaling required."
            ),
        ),
    ]

    def __init__(
        self,
        custom_thresholds: list[AlertThreshold] | None = None,
        alert_handlers: list[Callable[[Alert], None]] | None = None,
    ):
        """
        Initialize alert service.

        Args:
            custom_thresholds: Optional custom thresholds
            alert_handlers: Optional custom alert handlers
        """
        self._thresholds = list(self.DEFAULT_THRESHOLDS)
        if custom_thresholds:
            self._thresholds.extend(custom_thresholds)

        self._handlers: list[Callable[[Alert], None]] = [
            self._log_alert,  # Always log
        ]
        if alert_handlers:
            self._handlers.extend(alert_handlers)

        # Alert history (for deduplication and tracking)
        self._recent_alerts: list[Alert] = []

        logger.info(
            f"Quality alert service initialized with "
            f"{len(self._thresholds)} thresholds"
        )

    def add_threshold(self, threshold: AlertThreshold) -> None:
        """Add a custom threshold."""
        self._thresholds.append(threshold)

    def add_handler(self, handler: Callable[[Alert], None]) -> None:
        """Add a custom alert handler."""
        self._handlers.append(handler)

    def check_and_alert(self, metrics: QualityMetrics) -> list[Alert]:
        """
        Check metrics against thresholds and trigger alerts.

        Args:
            metrics: QualityMetrics to check

        Returns:
            List of triggered alerts
        """
        triggered_alerts: list[Alert] = []

        for threshold in self._thresholds:
            # Get the metric value
            value = self._get_metric_value(metrics, threshold.metric_name)
            if value is None:
                continue

            # Check threshold
            is_breached = (
                (threshold.operator == "lt" and value < threshold.threshold) or
                (threshold.operator == "gt" and value > threshold.threshold)
            )

            if is_breached:
                alert = self._create_alert(threshold, value)

                # Check for duplicate alert (same type within last hour)
                if not self._is_duplicate_alert(alert):
                    triggered_alerts.append(alert)
                    self._recent_alerts.append(alert)
                    self._dispatch_alert(alert)

        # Cleanup old alerts
        self._cleanup_old_alerts()

        return triggered_alerts

    def _get_metric_value(
        self,
        metrics: QualityMetrics,
        metric_name: str,
    ) -> float | None:
        """Get metric value by name."""
        mapping = {
            "validation_pass_rate": metrics.validation_pass_rate,
            "duplicate_rate": metrics.duplicate_rate,
            "llm_error_rate": metrics.llm_error_rate,
            "avg_relevance_score": metrics.average_relevance_score,
            "processing_backlog": float(metrics.processing_backlog),
            "signals_pending": float(metrics.signals_pending),
            "total_signals": float(metrics.total_signals_collected),
            "total_insights": float(metrics.total_insights_generated),
        }
        return mapping.get(metric_name)

    def _create_alert(
        self,
        threshold: AlertThreshold,
        actual_value: float,
    ) -> Alert:
        """Create an alert from a threshold breach."""
        message = threshold.message_template.format(
            actual=actual_value,
            threshold=threshold.threshold,
        )

        return Alert(
            id=f"{threshold.metric_name}_{datetime.now(UTC).timestamp():.0f}",
            severity=threshold.severity,
            title=threshold.title,
            message=message,
            metric_name=threshold.metric_name,
            threshold=threshold.threshold,
            actual_value=actual_value,
            timestamp=datetime.now(UTC),
        )

    def _is_duplicate_alert(self, alert: Alert) -> bool:
        """Check if alert is a duplicate of a recent alert."""
        one_hour_ago = datetime.now(UTC).replace(microsecond=0)
        one_hour_ago = one_hour_ago.replace(
            hour=one_hour_ago.hour - 1 if one_hour_ago.hour > 0 else 23
        )

        for recent in self._recent_alerts:
            if (
                recent.metric_name == alert.metric_name and
                recent.severity == alert.severity and
                recent.timestamp >= one_hour_ago
            ):
                return True
        return False

    def _dispatch_alert(self, alert: Alert) -> None:
        """Dispatch alert to all handlers."""
        for handler in self._handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Alert handler failed: {e}")

    def _log_alert(self, alert: Alert) -> None:
        """Log alert at appropriate level."""
        log_method = {
            AlertSeverity.INFO: logger.info,
            AlertSeverity.WARNING: logger.warning,
            AlertSeverity.ERROR: logger.error,
            AlertSeverity.CRITICAL: logger.critical,
        }.get(alert.severity, logger.warning)

        log_method(
            f"QUALITY ALERT [{alert.severity.value.upper()}]: {alert.title}\n"
            f"  {alert.message}\n"
            f"  Metric: {alert.metric_name} = {alert.actual_value:.4f} "
            f"(threshold: {alert.threshold:.4f})"
        )

    def _cleanup_old_alerts(self) -> None:
        """Remove alerts older than 24 hours."""
        cutoff = datetime.now(UTC).replace(microsecond=0)
        cutoff = cutoff.replace(day=cutoff.day - 1 if cutoff.day > 1 else 1)

        self._recent_alerts = [
            a for a in self._recent_alerts
            if a.timestamp >= cutoff
        ]

    def get_recent_alerts(
        self,
        severity: AlertSeverity | None = None,
        limit: int = 100,
    ) -> list[Alert]:
        """
        Get recent alerts, optionally filtered by severity.

        Args:
            severity: Optional severity filter
            limit: Maximum alerts to return

        Returns:
            List of recent alerts
        """
        alerts = self._recent_alerts
        if severity:
            alerts = [a for a in alerts if a.severity == severity]

        return sorted(
            alerts,
            key=lambda a: a.timestamp,
            reverse=True,
        )[:limit]


def create_sentry_handler() -> Callable[[Alert], None] | None:
    """
    Create Sentry alert handler if Sentry is configured.

    Returns:
        Handler function or None if Sentry not configured
    """
    try:
        import sentry_sdk

        def sentry_handler(alert: Alert) -> None:
            level_map = {
                AlertSeverity.INFO: "info",
                AlertSeverity.WARNING: "warning",
                AlertSeverity.ERROR: "error",
                AlertSeverity.CRITICAL: "fatal",
            }
            level = level_map.get(alert.severity, "warning")

            sentry_sdk.capture_message(
                f"[{alert.severity.value.upper()}] {alert.title}: {alert.message}",
                level=level,
                extras={
                    "metric_name": alert.metric_name,
                    "threshold": alert.threshold,
                    "actual_value": alert.actual_value,
                },
            )

        return sentry_handler

    except ImportError:
        logger.debug("Sentry not installed, skipping Sentry alert handler")
        return None


def create_slack_handler() -> Callable[[Alert], None] | None:
    """
    Create Slack webhook handler if webhook URL is configured.

    Only sends CRITICAL and ERROR alerts to avoid noise.

    Returns:
        Handler function or None if webhook not configured
    """
    if not settings.slack_webhook_url:
        logger.debug("Slack webhook not configured, skipping Slack alert handler")
        return None

    async def send_slack_notification(alert: Alert) -> None:
        """Send alert to Slack via webhook (async)."""
        # Only send ERROR and CRITICAL alerts to Slack
        if alert.severity not in (AlertSeverity.ERROR, AlertSeverity.CRITICAL):
            return

        # Emoji mapping for severity
        emoji_map = {
            AlertSeverity.ERROR: "⚠️",
            AlertSeverity.CRITICAL: "🚨",
        }
        emoji = emoji_map.get(alert.severity, "⚠️")

        # Color coding
        color_map = {
            AlertSeverity.ERROR: "#ff9800",  # Orange
            AlertSeverity.CRITICAL: "#f44336",  # Red
        }
        color = color_map.get(alert.severity, "#ff9800")

        # Build Slack message
        payload = {
            "text": f"{emoji} *StartInsight Alert*: {alert.title}",
            "attachments": [
                {
                    "color": color,
                    "fields": [
                        {
                            "title": "Severity",
                            "value": alert.severity.value.upper(),
                            "short": True,
                        },
                        {
                            "title": "Metric",
                            "value": alert.metric_name,
                            "short": True,
                        },
                        {
                            "title": "Threshold",
                            "value": f"{alert.threshold:.4f}",
                            "short": True,
                        },
                        {
                            "title": "Actual Value",
                            "value": f"{alert.actual_value:.4f}",
                            "short": True,
                        },
                        {
                            "title": "Message",
                            "value": alert.message,
                            "short": False,
                        },
                        {
                            "title": "Time",
                            "value": alert.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC"),
                            "short": False,
                        },
                    ],
                }
            ],
        }

        # Send to Slack
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(settings.slack_webhook_url, json=payload)
                response.raise_for_status()
                logger.info(f"Sent {alert.severity.value} alert to Slack: {alert.title}")
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")

    def slack_handler(alert: Alert) -> None:
        """Synchronous wrapper for async Slack notification."""
        import asyncio

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if loop.is_running():
            # If loop is already running, create task
            asyncio.create_task(send_slack_notification(alert))
        else:
            # If loop is not running, run it
            loop.run_until_complete(send_slack_notification(alert))

    return slack_handler


# Global alert service instance
_alert_service: QualityAlertService | None = None


def get_alert_service() -> QualityAlertService:
    """
    Get or create global alert service instance.

    Returns:
        QualityAlertService: Singleton service instance
    """
    global _alert_service
    if _alert_service is None:
        handlers = []

        # Add Sentry handler if configured
        sentry_handler = create_sentry_handler()
        if sentry_handler:
            handlers.append(sentry_handler)

        # Add Slack handler if configured
        slack_handler = create_slack_handler()
        if slack_handler:
            handlers.append(slack_handler)

        _alert_service = QualityAlertService(alert_handlers=handlers)
        logger.info(f"Alert service initialized with {len(handlers)} handlers")

    return _alert_service
