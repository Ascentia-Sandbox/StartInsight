"""Phase 6.4B: Cross-source signal correlation engine.

Detects when multiple sources discuss the same topic within 24h
using lightweight TF-IDF keyword overlap + cosine similarity.

No external dependencies (pure Python) — avoids 50MB scikit-learn.
"""

import logging
import math
import re
import uuid
from collections import Counter
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update

from app.core.constants import (
    CORRELATION_WINDOW_HOURS,
    MAX_INSIGHTS_TO_SCAN,
    SIMILARITY_THRESHOLD,
)
from app.db.session import AsyncSessionLocal
from app.models.insight import Insight

logger = logging.getLogger(__name__)

# Common English stop words (kept minimal for startup context)
_STOP_WORDS = frozenset({
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "can", "shall", "must", "need", "to", "of",
    "in", "for", "on", "with", "at", "by", "from", "as", "into", "through",
    "during", "before", "after", "above", "below", "between", "out", "off",
    "over", "under", "again", "further", "then", "once", "here", "there",
    "when", "where", "why", "how", "all", "each", "every", "both", "few",
    "more", "most", "other", "some", "such", "no", "nor", "not", "only",
    "own", "same", "so", "than", "too", "very", "just", "because", "but",
    "and", "or", "if", "while", "about", "up", "it", "its", "this", "that",
    "these", "those", "i", "me", "my", "we", "our", "you", "your", "he",
    "him", "his", "she", "her", "they", "them", "their", "what", "which",
    "who", "whom",
})


def _tokenize(text: str) -> list[str]:
    """Tokenize text into lowercase words, removing stop words and short tokens."""
    words = re.findall(r"[a-zA-Z]{3,}", text.lower())
    return [w for w in words if w not in _STOP_WORDS]


def _compute_tfidf(documents: list[list[str]]) -> list[dict[str, float]]:
    """Compute TF-IDF vectors for a list of tokenized documents.

    Returns list of {term: tfidf_weight} dicts, one per document.
    """
    n_docs = len(documents)
    if n_docs == 0:
        return []

    # Document frequency (how many docs contain each term)
    df: Counter = Counter()
    for doc in documents:
        unique_terms = set(doc)
        for term in unique_terms:
            df[term] += 1

    # Compute TF-IDF for each document
    tfidf_vectors = []
    for doc in documents:
        tf = Counter(doc)
        doc_len = len(doc) or 1
        vector = {}
        for term, count in tf.items():
            tf_val = count / doc_len
            idf_val = math.log((n_docs + 1) / (df[term] + 1)) + 1  # Smoothed IDF
            vector[term] = tf_val * idf_val
        tfidf_vectors.append(vector)

    return tfidf_vectors


def _cosine_similarity(vec_a: dict[str, float], vec_b: dict[str, float]) -> float:
    """Compute cosine similarity between two sparse TF-IDF vectors."""
    # Dot product (only over shared terms)
    shared_terms = set(vec_a.keys()) & set(vec_b.keys())
    if not shared_terms:
        return 0.0

    dot = sum(vec_a[t] * vec_b[t] for t in shared_terms)

    # Magnitudes
    mag_a = math.sqrt(sum(v * v for v in vec_a.values()))
    mag_b = math.sqrt(sum(v * v for v in vec_b.values()))

    if mag_a == 0 or mag_b == 0:
        return 0.0

    return dot / (mag_a * mag_b)


async def correlate_recent_insights() -> list[dict]:
    """Find cross-source correlations among insights created in the last 24 hours.

    Algorithm:
    1. Fetch recent insights (last 24h) across all sources
    2. Build TF-IDF vectors from problem_statement + title
    3. Compare every pair from DIFFERENT sources
    4. Group highly similar pairs (similarity > threshold)
    5. Assign correlation_group_id to grouped insights

    Returns:
        List of correlation groups found.
    """
    cutoff = datetime.now(UTC) - timedelta(hours=CORRELATION_WINDOW_HOURS)
    groups_found = []

    try:
        async with AsyncSessionLocal() as session:
            # Fetch recent insights with their source info
            result = await session.execute(
                select(Insight)
                .where(Insight.created_at >= cutoff)
                .where(Insight.admin_status == "approved")
                .order_by(Insight.created_at.desc())
                .limit(MAX_INSIGHTS_TO_SCAN)
            )
            insights = result.scalars().all()

            if len(insights) < 2:
                return []

            # Load source info via raw_signal relationship
            # Build text corpus
            texts = []
            insight_sources = []
            for ins in insights:
                text = f"{ins.title or ''} {ins.problem_statement or ''}"
                texts.append(text)
                # Get source from raw_signal
                source = ins.raw_signal.source if ins.raw_signal else "unknown"
                insight_sources.append(source)

            # Tokenize and compute TF-IDF
            tokenized = [_tokenize(t) for t in texts]
            tfidf_vectors = _compute_tfidf(tokenized)

            # Find correlated pairs (different sources only)
            # Track which insights are already grouped
            grouped: dict[int, uuid.UUID] = {}  # index → group_id
            correlation_pairs = []

            for i in range(len(insights)):
                for j in range(i + 1, len(insights)):
                    # Skip same-source comparisons
                    if insight_sources[i] == insight_sources[j]:
                        continue

                    sim = _cosine_similarity(tfidf_vectors[i], tfidf_vectors[j])
                    if sim >= SIMILARITY_THRESHOLD:
                        correlation_pairs.append((i, j, sim))

            # Build groups from pairs using union-find with path compression
            uf_parent: dict[int, int] = {}
            uf_rank: dict[int, int] = {}

            def _find(x: int) -> int:
                if x not in uf_parent:
                    uf_parent[x] = x
                    uf_rank[x] = 0
                while uf_parent[x] != x:
                    uf_parent[x] = uf_parent[uf_parent[x]]  # path compression
                    x = uf_parent[x]
                return x

            def _union(a: int, b: int) -> None:
                ra, rb = _find(a), _find(b)
                if ra == rb:
                    return
                if uf_rank[ra] < uf_rank[rb]:
                    ra, rb = rb, ra
                uf_parent[rb] = ra
                if uf_rank[ra] == uf_rank[rb]:
                    uf_rank[ra] += 1

            for i, j, sim in correlation_pairs:
                _union(i, j)

            group_map: dict[int, uuid.UUID] = {}
            grouped: dict[int, uuid.UUID] = {}
            for idx in uf_parent:
                root = _find(idx)
                if root not in group_map:
                    group_map[root] = uuid.uuid4()
                grouped[idx] = group_map[root]

            # Aggregate groups
            group_members: dict[uuid.UUID, list[int]] = {}
            for idx, gid in grouped.items():
                group_members.setdefault(gid, []).append(idx)

            # Update insights in DB
            for group_id, member_indices in group_members.items():
                if len(member_indices) < 2:
                    continue

                sources_in_group = set(insight_sources[idx] for idx in member_indices)
                source_count = len(sources_in_group)

                for idx in member_indices:
                    ins = insights[idx]
                    # Find best similarity for this insight within the group
                    best_sim = 0.0
                    for i, j, sim in correlation_pairs:
                        if i == idx or j == idx:
                            best_sim = max(best_sim, sim)

                    await session.execute(
                        update(Insight)
                        .where(Insight.id == ins.id)
                        .values(
                            correlation_group_id=group_id,
                            correlation_score=round(best_sim, 4),
                            source_count=source_count,
                        )
                    )

                groups_found.append({
                    "group_id": str(group_id),
                    "insights": [str(insights[idx].id) for idx in member_indices],
                    "sources": list(sources_in_group),
                    "source_count": source_count,
                    "max_similarity": round(max(
                        sim for i, j, sim in correlation_pairs
                        if i in member_indices or j in member_indices
                    ), 4) if correlation_pairs else 0,
                })

            await session.commit()

        if groups_found:
            logger.info(
                f"Signal correlation: found {len(groups_found)} groups "
                f"across {len(insights)} recent insights"
            )

    except Exception as e:
        logger.error(f"Signal correlation failed: {e}")

    return groups_found
