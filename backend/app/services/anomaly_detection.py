"""Phase 6.4A: Temporal baselines using Welford's online algorithm.

Tracks per-source signal volume baselines with O(1) memory.
Detects anomalies when yield deviates >2σ from baseline.

Thresholds:
- z > 2.0: "spike" — potential trend surge
- z < -2.0: "drought" — scraper may be broken or source down
"""

import logging
import math

logger = logging.getLogger(__name__)


class WelfordBaseline:
    """Welford's online algorithm for computing running mean and variance.

    O(1) memory — only stores count, mean, M2 (sum of squared differences).
    Thread-safe via atomic Redis updates in update_source_baseline().
    """

    def __init__(self, count: int = 0, mean: float = 0.0, variance: float = 0.0):
        """Initialize from stored baseline values.

        Args:
            count: Number of observations seen so far.
            mean: Running mean of observations.
            variance: Population variance (M2 / count). Used to reconstruct
                M2 = variance * count for continued online updates.
        """
        self.count = count
        self.mean = mean
        # Store M2 (sum of squared differences) internally
        self._m2 = variance * count if count > 0 else 0.0

    def update(self, value: float) -> None:
        """Add a new observation using Welford's algorithm."""
        self.count += 1
        delta = value - self.mean
        self.mean += delta / self.count
        delta2 = value - self.mean
        self._m2 += delta * delta2

    @property
    def variance(self) -> float:
        """Population variance."""
        if self.count < 2:
            return 0.0
        return self._m2 / self.count

    @property
    def stddev(self) -> float:
        """Population standard deviation."""
        return math.sqrt(self.variance)

    def z_score(self, value: float) -> float:
        """Calculate z-score for a given value against the baseline.

        Returns 0.0 if insufficient data (< 5 observations).
        """
        if self.count < 5 or self.stddev == 0:
            return 0.0
        return (value - self.mean) / self.stddev

    def detect_anomaly(self, value: float) -> str | None:
        """Detect anomaly type based on z-score thresholds.

        Returns:
            "spike" if z > 2.0 (unusually high signal volume)
            "drought" if z < -2.0 (unusually low signal volume)
            None if within normal range
        """
        z = self.z_score(value)
        if z > 2.0:
            return "spike"
        if z < -2.0:
            return "drought"
        return None


async def update_source_baseline(source_name: str, signals_count: int) -> str | None:
    """Update Welford baseline for a source and check for anomalies.

    Reads current baseline from source_health table, updates with new observation,
    writes back, and returns anomaly type if detected.

    Args:
        source_name: Scraper source identifier
        signals_count: Number of signals from latest run

    Returns:
        "spike", "drought", or None
    """
    from sqlalchemy import text

    from app.db.session import AsyncSessionLocal

    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text(
                    "SELECT baseline_mean, baseline_variance, baseline_count "
                    "FROM source_health WHERE source_name = :name "
                    "FOR UPDATE"
                ),
                {"name": source_name},
            )
            row = result.mappings().first()
            if not row:
                return None

            # Reconstruct baseline
            baseline = WelfordBaseline(
                count=row["baseline_count"],
                mean=row["baseline_mean"],
                variance=row["baseline_variance"],
            )

            # Check for anomaly BEFORE updating (compare against existing baseline)
            anomaly = baseline.detect_anomaly(float(signals_count))

            # Update baseline with new observation
            baseline.update(float(signals_count))

            # Write back
            await session.execute(
                text(
                    "UPDATE source_health SET "
                    "baseline_mean = :mean, "
                    "baseline_variance = :variance, "
                    "baseline_count = :count "
                    "WHERE source_name = :name"
                ),
                {
                    "mean": baseline.mean,
                    "variance": baseline.variance,
                    "count": baseline.count,
                    "name": source_name,
                },
            )
            await session.commit()

            if anomaly:
                logger.warning(
                    f"Anomaly detected for {source_name}: {anomaly} "
                    f"(signals={signals_count}, mean={baseline.mean:.1f}, "
                    f"z={baseline.z_score(float(signals_count)):.2f})"
                )

            return anomaly

    except Exception as e:
        logger.debug(f"Could not update baseline for {source_name}: {e}")
        return None
