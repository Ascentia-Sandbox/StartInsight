"""Metrics tracking and monitoring for StartInsight."""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


# ============================================================
# LLM Cost Tracking
# ============================================================

# Claude 3.5 Sonnet pricing (as of Jan 2024)
CLAUDE_SONNET_PRICING = {
    "input_tokens": 0.003 / 1000,  # $0.003 per 1K input tokens
    "output_tokens": 0.015 / 1000,  # $0.015 per 1K output tokens
}

# GPT-4o pricing (as of Jan 2024)
GPT4O_PRICING = {
    "input_tokens": 0.005 / 1000,  # $0.005 per 1K input tokens
    "output_tokens": 0.015 / 1000,  # $0.015 per 1K output tokens
}


@dataclass
class LLMCallMetrics:
    """Metrics for a single LLM API call."""

    timestamp: datetime
    model: str  # "claude-3-5-sonnet", "gpt-4o"
    prompt_length: int  # Characters in prompt
    response_length: int  # Characters in response
    input_tokens: int  # Actual tokens used (from API response)
    output_tokens: int  # Actual tokens generated (from API response)
    latency_ms: float  # API call latency in milliseconds
    success: bool  # Whether call succeeded
    error: str | None = None  # Error message if failed
    cost_usd: float = 0.0  # Estimated cost in USD

    def __post_init__(self):
        """Calculate cost after initialization."""
        if self.success and self.input_tokens > 0:
            if "claude" in self.model.lower():
                pricing = CLAUDE_SONNET_PRICING
            elif "gpt" in self.model.lower():
                pricing = GPT4O_PRICING
            else:
                pricing = CLAUDE_SONNET_PRICING  # Default

            self.cost_usd = (
                self.input_tokens * pricing["input_tokens"]
                + self.output_tokens * pricing["output_tokens"]
            )


@dataclass
class InsightMetrics:
    """Aggregated metrics for insights generation."""

    total_insights_generated: int = 0
    total_insights_failed: int = 0
    relevance_scores: list[float] = field(default_factory=list)
    llm_calls: list[LLMCallMetrics] = field(default_factory=list)
    errors_by_type: dict[str, int] = field(default_factory=lambda: defaultdict(int))

    @property
    def average_relevance_score(self) -> float:
        """Calculate average relevance score."""
        if not self.relevance_scores:
            return 0.0
        return sum(self.relevance_scores) / len(self.relevance_scores)

    @property
    def total_cost_usd(self) -> float:
        """Calculate total LLM API costs."""
        return sum(call.cost_usd for call in self.llm_calls)

    @property
    def average_latency_ms(self) -> float:
        """Calculate average LLM API latency."""
        successful_calls = [call for call in self.llm_calls if call.success]
        if not successful_calls:
            return 0.0
        return sum(call.latency_ms for call in successful_calls) / len(
            successful_calls
        )

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        total = self.total_insights_generated + self.total_insights_failed
        if total == 0:
            return 0.0
        return (self.total_insights_generated / total) * 100


class MetricsTracker:
    """
    Singleton metrics tracker for monitoring LLM performance.

    Tracks:
    - Total insights generated
    - Average relevance scores
    - LLM API costs and latency
    - Error rates by type
    """

    _instance = None

    def __new__(cls):
        """Ensure singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize metrics tracker."""
        if self._initialized:
            return

        self.metrics = InsightMetrics()
        self._initialized = True
        logger.info("MetricsTracker initialized")

    def track_llm_call(
        self,
        model: str,
        prompt: str,
        response: str | None,
        input_tokens: int,
        output_tokens: int,
        latency_ms: float,
        success: bool,
        error: str | None = None,
    ) -> None:
        """
        Track a single LLM API call.

        Args:
            model: Model name (e.g., "claude-3-5-sonnet-20241022")
            prompt: Input prompt text
            response: LLM response text (None if failed)
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            latency_ms: API call latency in milliseconds
            success: Whether the call succeeded
            error: Error message if failed
        """
        call_metrics = LLMCallMetrics(
            timestamp=datetime.utcnow(),
            model=model,
            prompt_length=len(prompt),
            response_length=len(response) if response else 0,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            success=success,
            error=error,
        )

        self.metrics.llm_calls.append(call_metrics)

        # Log structured data
        logger.info(
            f"LLM Call: model={model}, tokens={input_tokens}/{output_tokens}, "
            f"latency={latency_ms:.0f}ms, cost=${call_metrics.cost_usd:.4f}, "
            f"success={success}"
        )

        if not success and error:
            error_type = type(error).__name__ if isinstance(error, Exception) else "Unknown"
            self.metrics.errors_by_type[error_type] += 1
            logger.warning(f"LLM Error: {error_type} - {error}")

    def track_insight_generated(self, relevance_score: float) -> None:
        """
        Track a successfully generated insight.

        Args:
            relevance_score: Relevance score (0.0 - 1.0)
        """
        self.metrics.total_insights_generated += 1
        self.metrics.relevance_scores.append(relevance_score)

        logger.info(
            f"Insight generated: score={relevance_score:.2f}, "
            f"total={self.metrics.total_insights_generated}, "
            f"avg_score={self.metrics.average_relevance_score:.2f}"
        )

    def track_insight_failed(self, error: Exception) -> None:
        """
        Track a failed insight generation.

        Args:
            error: Exception that caused the failure
        """
        self.metrics.total_insights_failed += 1
        error_type = type(error).__name__
        self.metrics.errors_by_type[error_type] += 1

        logger.error(
            f"Insight generation failed: {error_type} - {error}, "
            f"total_failed={self.metrics.total_insights_failed}"
        )

    def get_summary(self) -> dict[str, Any]:
        """
        Get metrics summary.

        Returns:
            Dictionary with aggregated metrics
        """
        return {
            "insights": {
                "total_generated": self.metrics.total_insights_generated,
                "total_failed": self.metrics.total_insights_failed,
                "success_rate": f"{self.metrics.success_rate:.1f}%",
                "average_relevance_score": f"{self.metrics.average_relevance_score:.2f}",
            },
            "llm": {
                "total_calls": len(self.metrics.llm_calls),
                "total_cost_usd": f"${self.metrics.total_cost_usd:.4f}",
                "average_latency_ms": f"{self.metrics.average_latency_ms:.0f}",
            },
            "errors": dict(self.metrics.errors_by_type),
        }

    def log_summary(self) -> None:
        """Log metrics summary."""
        summary = self.get_summary()
        logger.info("=" * 60)
        logger.info("Metrics Summary:")
        logger.info(f"  Insights: {summary['insights']}")
        logger.info(f"  LLM: {summary['llm']}")
        logger.info(f"  Errors: {summary['errors']}")
        logger.info("=" * 60)

    def reset(self) -> None:
        """Reset all metrics (for testing)."""
        self.metrics = InsightMetrics()
        logger.info("Metrics reset")


# Global instance
_tracker = None


def get_metrics_tracker() -> MetricsTracker:
    """Get singleton metrics tracker instance."""
    global _tracker
    if _tracker is None:
        _tracker = MetricsTracker()
    return _tracker
