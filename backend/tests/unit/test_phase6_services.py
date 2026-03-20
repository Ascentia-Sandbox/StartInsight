"""Unit tests for Phase 6 services: correlation, anomaly detection, spike detection.

All pure-function tests — no DB or mocking required.
"""

import uuid

from app.services.anomaly_detection import WelfordBaseline
from app.services.signal_correlation import (
    _compute_tfidf,
    _cosine_similarity,
    _tokenize,
)


class TestUnionFindTransitiveClosure:
    """Test that the union-find grouping merges transitive pairs correctly."""

    def test_transitive_closure(self):
        """A~B and B~C should all end up in the same group."""
        # Simulate the union-find logic from correlate_recent_insights
        parent: dict[int, int] = {}
        rank: dict[int, int] = {}

        def find(x: int) -> int:
            if x not in parent:
                parent[x] = x
                rank[x] = 0
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(a: int, b: int) -> None:
            ra, rb = find(a), find(b)
            if ra == rb:
                return
            if rank[ra] < rank[rb]:
                ra, rb = rb, ra
            parent[rb] = ra
            if rank[ra] == rank[rb]:
                rank[ra] += 1

        # A(0)~B(1), B(1)~C(2) — transitive: all should merge
        pairs = [(0, 1, 0.8), (1, 2, 0.5)]
        for i, j, _ in pairs:
            union(i, j)

        group_map: dict[int, uuid.UUID] = {}
        grouped: dict[int, uuid.UUID] = {}
        for idx in parent:
            root = find(idx)
            if root not in group_map:
                group_map[root] = uuid.uuid4()
            grouped[idx] = group_map[root]

        # All three should share the same group
        assert grouped[0] == grouped[1] == grouped[2]

    def test_disjoint_groups_remain_separate(self):
        """A~B and C~D with no link should stay in separate groups."""
        parent: dict[int, int] = {}
        rank: dict[int, int] = {}

        def find(x: int) -> int:
            if x not in parent:
                parent[x] = x
                rank[x] = 0
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(a: int, b: int) -> None:
            ra, rb = find(a), find(b)
            if ra == rb:
                return
            if rank[ra] < rank[rb]:
                ra, rb = rb, ra
            parent[rb] = ra
            if rank[ra] == rank[rb]:
                rank[ra] += 1

        pairs = [(0, 1, 0.8), (2, 3, 0.7)]
        for i, j, _ in pairs:
            union(i, j)

        group_map: dict[int, uuid.UUID] = {}
        grouped: dict[int, uuid.UUID] = {}
        for idx in parent:
            root = find(idx)
            if root not in group_map:
                group_map[root] = uuid.uuid4()
            grouped[idx] = group_map[root]

        assert grouped[0] == grouped[1]
        assert grouped[2] == grouped[3]
        assert grouped[0] != grouped[2]


class TestCosineSimilarity:
    def test_identical_vectors(self):
        vec = {"ai": 0.5, "startup": 0.3, "funding": 0.2}
        assert abs(_cosine_similarity(vec, vec) - 1.0) < 1e-9

    def test_orthogonal_vectors(self):
        vec_a = {"ai": 1.0, "startup": 1.0}
        vec_b = {"cooking": 1.0, "recipe": 1.0}
        assert _cosine_similarity(vec_a, vec_b) == 0.0

    def test_empty_vectors(self):
        assert _cosine_similarity({}, {"a": 1.0}) == 0.0
        assert _cosine_similarity({}, {}) == 0.0


class TestTokenize:
    def test_removes_stopwords(self):
        tokens = _tokenize("the quick brown fox is a very fast animal")
        assert "the" not in tokens
        assert "very" not in tokens
        assert "quick" in tokens
        assert "brown" in tokens
        assert "fast" in tokens
        assert "animal" in tokens

    def test_removes_short_tokens(self):
        tokens = _tokenize("AI is an ML tool")
        # "AI", "is", "an", "ML" are all < 3 chars
        assert "tool" in tokens
        assert len([t for t in tokens if len(t) < 3]) == 0

    def test_lowercases(self):
        tokens = _tokenize("StartUp Funding Round")
        assert "startup" in tokens
        assert "funding" in tokens


class TestTfIdf:
    def test_single_document(self):
        docs = [["startup", "funding", "startup"]]
        vectors = _compute_tfidf(docs)
        assert len(vectors) == 1
        assert "startup" in vectors[0]
        assert "funding" in vectors[0]

    def test_empty_corpus(self):
        assert _compute_tfidf([]) == []


class TestWelfordBaseline:
    def test_roundtrip(self):
        """Init from (count, mean, variance), update, verify consistency."""
        # Build a baseline from scratch
        b1 = WelfordBaseline()
        for v in [10, 20, 30, 40, 50]:
            b1.update(v)

        # Reconstruct from stored values
        b2 = WelfordBaseline(count=b1.count, mean=b1.mean, variance=b1.variance)

        assert b2.count == b1.count
        assert abs(b2.mean - b1.mean) < 1e-9
        assert abs(b2.variance - b1.variance) < 1e-9

        # Both should produce the same result after another update
        b1.update(60)
        b2.update(60)
        assert abs(b1.mean - b2.mean) < 1e-9
        assert abs(b1.variance - b2.variance) < 1e-9

    def test_z_score_insufficient_data(self):
        """Returns 0.0 for count < 5."""
        b = WelfordBaseline()
        for v in [10, 20, 30]:
            b.update(v)
        assert b.z_score(100) == 0.0

    def test_z_score_with_data(self):
        b = WelfordBaseline()
        for v in [10, 10, 10, 10, 10]:
            b.update(v)
        # Mean = 10, variance = 0, stddev = 0 → should return 0.0
        assert b.z_score(100) == 0.0

        # Now add some variance
        b2 = WelfordBaseline()
        for v in [10, 20, 10, 20, 10]:
            b2.update(v)
        z = b2.z_score(30)
        assert z > 0  # 30 is above mean of 14

    def test_detect_anomaly_spike(self):
        b = WelfordBaseline()
        for v in [10, 12, 11, 10, 13, 11, 10, 12]:
            b.update(v)
        anomaly = b.detect_anomaly(50)  # Way above mean ~11
        assert anomaly == "spike"

    def test_detect_anomaly_drought(self):
        b = WelfordBaseline()
        for v in [100, 110, 105, 100, 108, 102, 100, 107]:
            b.update(v)
        anomaly = b.detect_anomaly(0)  # Way below mean ~104
        assert anomaly == "drought"

    def test_detect_anomaly_normal(self):
        b = WelfordBaseline()
        for v in [10, 12, 11, 10, 13, 11, 10, 12]:
            b.update(v)
        anomaly = b.detect_anomaly(11)  # Near mean
        assert anomaly is None
