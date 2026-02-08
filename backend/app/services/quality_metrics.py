"""Quality metrics collection and tracking service.

This module provides metrics collection for monitoring data quality
across the scraping and analysis pipeline.

Tracks:
- Signal collection metrics by source
- Duplicate and truncation rates
- Analysis success rates
- Validation pass rates
- Dimension score distributions
- Error rates by component
"""

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.insight import Insight
from app.models.raw_signal import RawSignal

logger = logging.getLogger(__name__)


@dataclass
class QualityMetrics:
    """Aggregated quality metrics for a time period."""

    # Time period
    period_start: datetime
    period_end: datetime

    # Collection metrics
    total_signals_collected: int = 0
    signals_by_source: dict[str, int] = field(default_factory=dict)
    duplicate_count: int = 0
    duplicate_rate: float = 0.0
    truncation_count: int = 0
    truncation_rate: float = 0.0

    # Analysis metrics
    total_insights_generated: int = 0
    validation_pass_count: int = 0
    validation_fail_count: int = 0
    validation_pass_rate: float = 0.0
    average_problem_statement_length: int = 0

    # Score metrics
    average_relevance_score: float = 0.0
    dimension_averages: dict[str, float] = field(default_factory=dict)
    score_distribution: dict[str, dict[str, int]] = field(default_factory=dict)

    # Error metrics
    scraper_error_counts: dict[str, int] = field(default_factory=dict)
    scraper_error_rates: dict[str, float] = field(default_factory=dict)
    llm_error_count: int = 0
    llm_error_rate: float = 0.0

    # Processing metrics
    average_processing_time_ms: float = 0.0
    signals_pending: int = 0
    processing_backlog: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert metrics to dictionary for JSON serialization."""
        return {
            "period": {
                "start": self.period_start.isoformat(),
                "end": self.period_end.isoformat(),
            },
            "collection": {
                "total_signals": self.total_signals_collected,
                "by_source": self.signals_by_source,
                "duplicate_count": self.duplicate_count,
                "duplicate_rate": round(self.duplicate_rate, 4),
                "truncation_count": self.truncation_count,
                "truncation_rate": round(self.truncation_rate, 4),
            },
            "analysis": {
                "total_insights": self.total_insights_generated,
                "validation_pass_count": self.validation_pass_count,
                "validation_fail_count": self.validation_fail_count,
                "validation_pass_rate": round(self.validation_pass_rate, 4),
                "avg_problem_statement_length": self.average_problem_statement_length,
            },
            "scores": {
                "average_relevance": round(self.average_relevance_score, 4),
                "dimension_averages": {
                    k: round(v, 2) for k, v in self.dimension_averages.items()
                },
                "distribution": self.score_distribution,
            },
            "errors": {
                "scraper_counts": self.scraper_error_counts,
                "scraper_rates": {
                    k: round(v, 4) for k, v in self.scraper_error_rates.items()
                },
                "llm_error_count": self.llm_error_count,
                "llm_error_rate": round(self.llm_error_rate, 4),
            },
            "processing": {
                "avg_processing_time_ms": round(self.average_processing_time_ms, 2),
                "signals_pending": self.signals_pending,
                "backlog": self.processing_backlog,
            },
        }


class QualityMetricsCollector:
    """
    Collect and aggregate quality metrics from database.

    Provides methods to calculate metrics for various time periods
    and track quality trends over time.
    """

    def __init__(self):
        """Initialize metrics collector."""
        self._validation_results: list[dict] = []
        self._error_counts: dict[str, int] = {}

    def record_validation_result(
        self,
        signal_id: str,
        passed: bool,
        errors: list[str] | None = None,
        warnings: list[str] | None = None,
        quality_score: float = 0.0,
    ) -> None:
        """
        Record a validation result for tracking.

        Args:
            signal_id: Signal identifier
            passed: Whether validation passed
            errors: List of validation errors
            warnings: List of validation warnings
            quality_score: Quality score (0-100)
        """
        self._validation_results.append({
            "signal_id": signal_id,
            "passed": passed,
            "errors": errors or [],
            "warnings": warnings or [],
            "quality_score": quality_score,
            "timestamp": datetime.now(UTC),
        })

        # Keep only recent results (last 1000)
        if len(self._validation_results) > 1000:
            self._validation_results = self._validation_results[-1000:]

    def record_error(self, component: str, error_type: str) -> None:
        """
        Record an error for tracking.

        Args:
            component: Component name (e.g., "reddit_scraper", "llm")
            error_type: Type of error
        """
        key = f"{component}:{error_type}"
        self._error_counts[key] = self._error_counts.get(key, 0) + 1

    async def collect_metrics(
        self,
        session: AsyncSession,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> QualityMetrics:
        """
        Collect quality metrics for a time period.

        Args:
            session: Database session
            start: Period start (default: 24 hours ago)
            end: Period end (default: now)

        Returns:
            QualityMetrics with aggregated data
        """
        end = end or datetime.now(UTC)
        start = start or (end - timedelta(hours=24))

        metrics = QualityMetrics(period_start=start, period_end=end)

        # Collect signal metrics
        await self._collect_signal_metrics(session, start, end, metrics)

        # Collect insight metrics
        await self._collect_insight_metrics(session, start, end, metrics)

        # Collect score metrics
        await self._collect_score_metrics(session, start, end, metrics)

        # Collect validation metrics from local tracking
        self._collect_validation_metrics(start, end, metrics)

        # Calculate error rates
        self._calculate_error_rates(metrics)

        return metrics

    async def _collect_signal_metrics(
        self,
        session: AsyncSession,
        start: datetime,
        end: datetime,
        metrics: QualityMetrics,
    ) -> None:
        """Collect signal collection metrics."""
        # Total signals by source
        source_query = (
            select(RawSignal.source, func.count(RawSignal.id))
            .where(RawSignal.created_at >= start)
            .where(RawSignal.created_at < end)
            .group_by(RawSignal.source)
        )
        result = await session.execute(source_query)
        metrics.signals_by_source = dict(result.all())
        metrics.total_signals_collected = sum(metrics.signals_by_source.values())

        # Pending signals (unprocessed)
        pending_query = (
            select(func.count(RawSignal.id))
            .where(RawSignal.processed == False)  # noqa: E712
        )
        result = await session.execute(pending_query)
        metrics.signals_pending = result.scalar() or 0

        # Processing backlog (unprocessed older than 1 hour)
        backlog_time = datetime.now(UTC) - timedelta(hours=1)
        backlog_query = (
            select(func.count(RawSignal.id))
            .where(RawSignal.processed == False)  # noqa: E712
            .where(RawSignal.created_at < backlog_time)
        )
        result = await session.execute(backlog_query)
        metrics.processing_backlog = result.scalar() or 0

    async def _collect_insight_metrics(
        self,
        session: AsyncSession,
        start: datetime,
        end: datetime,
        metrics: QualityMetrics,
    ) -> None:
        """Collect insight analysis metrics."""
        # Total insights
        insight_query = (
            select(func.count(Insight.id))
            .where(Insight.created_at >= start)
            .where(Insight.created_at < end)
        )
        result = await session.execute(insight_query)
        metrics.total_insights_generated = result.scalar() or 0

        # Average problem statement length
        length_query = (
            select(func.avg(func.length(Insight.problem_statement)))
            .where(Insight.created_at >= start)
            .where(Insight.created_at < end)
        )
        result = await session.execute(length_query)
        avg_length = result.scalar()
        metrics.average_problem_statement_length = int(avg_length or 0)

    async def _collect_score_metrics(
        self,
        session: AsyncSession,
        start: datetime,
        end: datetime,
        metrics: QualityMetrics,
    ) -> None:
        """Collect score-related metrics."""
        # Average relevance score
        relevance_query = (
            select(func.avg(Insight.relevance_score))
            .where(Insight.created_at >= start)
            .where(Insight.created_at < end)
        )
        result = await session.execute(relevance_query)
        metrics.average_relevance_score = float(result.scalar() or 0)

        # Dimension averages
        dimension_fields = [
            ("opportunity", Insight.opportunity_score),
            ("problem", Insight.problem_score),
            ("feasibility", Insight.feasibility_score),
            ("why_now", Insight.why_now_score),
            ("go_to_market", Insight.go_to_market_score),
            ("founder_fit", Insight.founder_fit_score),
            ("execution_difficulty", Insight.execution_difficulty),
        ]

        for name, field in dimension_fields:
            avg_query = (
                select(func.avg(field))
                .where(Insight.created_at >= start)
                .where(Insight.created_at < end)
                .where(field.isnot(None))
            )
            result = await session.execute(avg_query)
            avg_value = result.scalar()
            if avg_value is not None:
                metrics.dimension_averages[name] = float(avg_value)

        # Score distribution (count per score bucket)
        for name, field in dimension_fields[:4]:  # Just main dimensions
            distribution = {}
            for score in range(1, 11):
                count_query = (
                    select(func.count(Insight.id))
                    .where(Insight.created_at >= start)
                    .where(Insight.created_at < end)
                    .where(field == score)
                )
                result = await session.execute(count_query)
                count = result.scalar() or 0
                distribution[str(score)] = count

            metrics.score_distribution[name] = distribution

    def _collect_validation_metrics(
        self,
        start: datetime,
        end: datetime,
        metrics: QualityMetrics,
    ) -> None:
        """Collect validation metrics from local tracking."""
        recent_results = [
            r for r in self._validation_results
            if start <= r["timestamp"] < end
        ]

        if not recent_results:
            return

        metrics.validation_pass_count = sum(1 for r in recent_results if r["passed"])
        metrics.validation_fail_count = sum(1 for r in recent_results if not r["passed"])

        total = len(recent_results)
        if total > 0:
            metrics.validation_pass_rate = metrics.validation_pass_count / total

    def _calculate_error_rates(self, metrics: QualityMetrics) -> None:
        """Calculate error rates from error counts."""
        total_signals = metrics.total_signals_collected

        # Calculate scraper error rates
        for key, count in self._error_counts.items():
            if "scraper" in key.lower():
                component = key.split(":")[0]
                metrics.scraper_error_counts[component] = count
                source_signals = metrics.signals_by_source.get(
                    component.replace("_scraper", ""), 0
                )
                if source_signals > 0:
                    metrics.scraper_error_rates[component] = count / source_signals

        # Calculate LLM error rate
        llm_errors = sum(
            v for k, v in self._error_counts.items()
            if "llm" in k.lower() or "analysis" in k.lower()
        )
        metrics.llm_error_count = llm_errors
        if metrics.total_insights_generated > 0:
            metrics.llm_error_rate = llm_errors / (
                metrics.total_insights_generated + llm_errors
            )

    async def collect_daily_metrics(
        self,
        session: AsyncSession,
        date: datetime | None = None,
    ) -> QualityMetrics:
        """
        Collect metrics for a specific day.

        Args:
            session: Database session
            date: Date to collect metrics for (default: today)

        Returns:
            QualityMetrics for the day
        """
        date = date or datetime.now(UTC)
        start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)

        return await self.collect_metrics(session, start, end)

    def get_quality_score(self, metrics: QualityMetrics) -> float:
        """
        Calculate overall quality score (0-100).

        Weighting:
        - Validation pass rate: 30%
        - Low duplicate rate: 20%
        - High average relevance: 20%
        - Low error rate: 20%
        - Processing throughput: 10%

        Args:
            metrics: QualityMetrics to score

        Returns:
            Overall quality score (0-100)
        """
        score = 0.0

        # Validation pass rate (30 points)
        score += metrics.validation_pass_rate * 30

        # Low duplicate rate (20 points) - lower is better
        duplicate_score = max(0, 1 - metrics.duplicate_rate) * 20
        score += duplicate_score

        # High average relevance (20 points)
        score += metrics.average_relevance_score * 20

        # Low error rate (20 points)
        error_rate = metrics.llm_error_rate + sum(
            metrics.scraper_error_rates.values()
        ) / max(len(metrics.scraper_error_rates), 1)
        error_score = max(0, 1 - error_rate) * 20
        score += error_score

        # Processing throughput (10 points) - low backlog is good
        if metrics.total_signals_collected > 0:
            backlog_ratio = metrics.processing_backlog / metrics.total_signals_collected
            throughput_score = max(0, 1 - backlog_ratio) * 10
        else:
            throughput_score = 10
        score += throughput_score

        return min(100.0, score)


# Global collector instance
_metrics_collector: QualityMetricsCollector | None = None


def get_metrics_collector() -> QualityMetricsCollector:
    """
    Get or create global metrics collector instance.

    Returns:
        QualityMetricsCollector: Singleton collector instance
    """
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = QualityMetricsCollector()
    return _metrics_collector
