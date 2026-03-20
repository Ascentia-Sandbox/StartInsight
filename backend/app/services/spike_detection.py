"""Phase 6.4C: Keyword spike detection.

Detects spikes when keyword trend value exceeds 3× its 7-day rolling baseline.
Uses realtime trend data stored in raw_signals.extra_metadata.trend_data_realtime.
"""

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.core.constants import MIN_SPIKE_BASELINE_POINTS as MIN_BASELINE_POINTS
from app.core.constants import SPIKE_MULTIPLIER
from app.db.session import AsyncSessionLocal
from app.models.raw_signal import RawSignal

logger = logging.getLogger(__name__)


async def detect_keyword_spikes() -> list[dict]:
    """Scan recent Google Trends signals for keyword spikes.

    For each keyword with realtime trend data:
    1. Calculate 7-day rolling average
    2. Compare latest value against average × SPIKE_MULTIPLIER
    3. Flag as spike if exceeded

    Returns:
        List of spike dicts: {keyword, current_value, baseline, multiplier, source}
    """
    spikes = []
    seven_days_ago = datetime.now(UTC) - timedelta(days=7)

    try:
        async with AsyncSessionLocal() as session:
            # Find Google Trends signals with realtime data
            result = await session.execute(
                select(RawSignal)
                .where(RawSignal.source.like("google_trends%"))
                .where(RawSignal.extra_metadata.isnot(None))
                .order_by(RawSignal.created_at.desc())
                .limit(200)
            )
            signals = result.scalars().all()

            seen_keywords: set[str] = set()

            for signal in signals:
                meta = signal.extra_metadata or {}
                keyword = meta.get("keyword")
                if not keyword or keyword in seen_keywords:
                    continue
                seen_keywords.add(keyword)

                trend_data = meta.get("trend_data_realtime", {})
                timestamps = trend_data.get("timestamps", [])
                values = trend_data.get("values", [])

                if len(values) < MIN_BASELINE_POINTS:
                    continue

                # Filter to last 7 days
                recent_values = []
                for ts, val in zip(timestamps, values):
                    try:
                        dt = datetime.fromisoformat(ts)
                        if dt >= seven_days_ago:
                            recent_values.append(val)
                    except (ValueError, TypeError):
                        continue

                if len(recent_values) < MIN_BASELINE_POINTS:
                    continue

                # Calculate baseline (average of all except latest)
                baseline = sum(recent_values[:-1]) / len(recent_values[:-1])
                latest = recent_values[-1]

                if baseline > 0 and latest >= baseline * SPIKE_MULTIPLIER:
                    spikes.append(
                        {
                            "keyword": keyword,
                            "current_value": latest,
                            "baseline": round(baseline, 2),
                            "multiplier": round(latest / baseline, 2),
                            "source": signal.source,
                            "detected_at": datetime.now(UTC).isoformat(),
                        }
                    )
                    logger.info(
                        f"Keyword spike detected: '{keyword}' at {latest} "
                        f"(baseline {baseline:.1f}, {latest / baseline:.1f}×)"
                    )

    except Exception as e:
        logger.error(f"Keyword spike detection failed: {e}")

    return spikes
