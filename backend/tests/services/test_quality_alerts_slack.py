"""Tests for Slack alerting integration in quality alerts."""

from datetime import UTC, datetime
from unittest.mock import patch

from app.services.quality_alerts import (
    Alert,
    AlertSeverity,
    AlertThreshold,
    QualityAlertService,
    create_slack_handler,
)


class TestSlackHandler:
    """Test Slack webhook handler creation and filtering."""

    def test_no_handler_without_webhook_url(self):
        """Should return None when SLACK_WEBHOOK_URL is not set."""
        with patch("app.services.quality_alerts.settings") as mock_settings:
            mock_settings.slack_webhook_url = None
            handler = create_slack_handler()
            assert handler is None

    def test_handler_created_with_webhook_url(self):
        """Should return a handler function when webhook URL is set."""
        with patch("app.services.quality_alerts.settings") as mock_settings:
            mock_settings.slack_webhook_url = "https://hooks.slack.com/services/test"
            handler = create_slack_handler()
            assert handler is not None
            assert callable(handler)


class TestAlertServiceWithSlack:
    """Test QualityAlertService with Slack integration."""

    def test_alert_service_creates_with_handlers(self):
        """Alert service should initialize with configured handlers."""
        service = QualityAlertService()
        # Should have at least the log handler
        assert len(service._handlers) >= 1

    def test_alert_dispatch_calls_handlers(self):
        """Dispatch should call all registered handlers."""
        handler_called = False

        def test_handler(alert):
            nonlocal handler_called
            handler_called = True

        service = QualityAlertService(alert_handlers=[test_handler])

        alert = Alert(
            id="test_123",
            severity=AlertSeverity.CRITICAL,
            title="Test Alert",
            message="Test message",
            metric_name="test_metric",
            threshold=0.8,
            actual_value=0.4,
            timestamp=datetime.now(UTC),
        )

        service._dispatch_alert(alert)
        assert handler_called

    def test_alert_handler_error_does_not_crash(self):
        """A failing handler should not crash the service."""
        def failing_handler(alert):
            raise ValueError("Handler failed!")

        service = QualityAlertService(alert_handlers=[failing_handler])

        alert = Alert(
            id="test_456",
            severity=AlertSeverity.ERROR,
            title="Test Alert",
            message="Test message",
            metric_name="test_metric",
            threshold=0.5,
            actual_value=0.8,
            timestamp=datetime.now(UTC),
        )

        # Should not raise
        service._dispatch_alert(alert)


class TestAlertCreation:
    """Test alert creation and deduplication."""

    def test_create_alert_from_threshold(self):
        """Should create alert with correct fields."""
        service = QualityAlertService()
        threshold = AlertThreshold(
            metric_name="test_metric",
            operator="lt",
            threshold=0.8,
            severity=AlertSeverity.CRITICAL,
            title="Test Title",
            message_template="Value is {actual:.1%}, below {threshold:.1%}",
        )

        alert = service._create_alert(threshold, 0.5)
        assert alert.severity == AlertSeverity.CRITICAL
        assert alert.title == "Test Title"
        assert "50.0%" in alert.message
        assert alert.metric_name == "test_metric"
        assert alert.actual_value == 0.5
        assert alert.threshold == 0.8

    def test_duplicate_alert_detected(self):
        """Same alert type/severity within 1 hour should be flagged as duplicate."""
        # Use a fixed time at noon to avoid midnight edge-case in hour subtraction
        fixed_now = datetime(2026, 2, 18, 12, 0, 0, tzinfo=UTC)
        service = QualityAlertService()

        alert1 = Alert(
            id="test_1",
            severity=AlertSeverity.CRITICAL,
            title="Test",
            message="Test",
            metric_name="test_metric",
            threshold=0.8,
            actual_value=0.4,
            timestamp=fixed_now,
        )

        service._recent_alerts.append(alert1)

        alert2 = Alert(
            id="test_2",
            severity=AlertSeverity.CRITICAL,
            title="Test",
            message="Test",
            metric_name="test_metric",
            threshold=0.8,
            actual_value=0.3,
            timestamp=fixed_now,
        )

        with patch("app.services.quality_alerts.datetime") as mock_dt:
            mock_dt.now.return_value = fixed_now
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            assert service._is_duplicate_alert(alert2) is True

    def test_different_metric_not_duplicate(self):
        """Alert for different metric should not be flagged as duplicate."""
        service = QualityAlertService()

        alert1 = Alert(
            id="test_1",
            severity=AlertSeverity.CRITICAL,
            title="Test",
            message="Test",
            metric_name="metric_a",
            threshold=0.8,
            actual_value=0.4,
            timestamp=datetime.now(UTC),
        )

        service._recent_alerts.append(alert1)

        alert2 = Alert(
            id="test_2",
            severity=AlertSeverity.CRITICAL,
            title="Test",
            message="Test",
            metric_name="metric_b",
            threshold=0.8,
            actual_value=0.3,
            timestamp=datetime.now(UTC),
        )

        assert service._is_duplicate_alert(alert2) is False

    def test_alert_to_dict(self):
        """Alert.to_dict should serialize all fields."""
        alert = Alert(
            id="test_1",
            severity=AlertSeverity.CRITICAL,
            title="Test",
            message="Test msg",
            metric_name="test_metric",
            threshold=0.8,
            actual_value=0.4,
            timestamp=datetime(2026, 2, 7, 12, 0, 0),
        )

        d = alert.to_dict()
        assert d["id"] == "test_1"
        assert d["severity"] == "critical"
        assert d["title"] == "Test"
        assert d["message"] == "Test msg"
        assert d["metric_name"] == "test_metric"
        assert d["threshold"] == 0.8
        assert d["actual_value"] == 0.4
        assert "2026-02-07" in d["timestamp"]
