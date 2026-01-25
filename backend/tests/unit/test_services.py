"""Unit tests for Phase 5.2-5.4 services.

Tests for build tools, export services, and real-time feed.
These tests don't require database access.
"""

import asyncio
import json
from datetime import datetime
from uuid import uuid4

import pytest

from app.services.brand_generator import (
    BrandPackage,
    ColorPalette,
    FontStack,
    LogoConcept,
    BrandVoice,
    get_default_brand_package,
)
from app.services.landing_page import (
    LandingPageTemplate,
    HeroSection,
    FeatureItem,
    get_default_landing_page,
)
from app.services.export_service import (
    ExportFormat,
    export_insight_csv,
    export_insight_pdf,
    export_analysis_csv,
    export_analysis_json,
    export_analysis_pdf,
    generate_pdf_content,
)
from app.services.realtime_feed import (
    InsightFeedMessage,
    EventStore,
    get_event_store,
    get_feed_stats,
    get_recent_insights,
    publish_new_insight,
)


# ============================================
# Brand Generator Tests (Phase 5.2)
# ============================================


class TestBrandGenerator:
    """Tests for brand package generation."""

    def test_get_default_brand_package(self):
        """Test default brand package generation."""
        brand = get_default_brand_package("TestCo")

        assert brand.company_name == "TestCo"
        assert brand.color_palette is not None
        assert brand.color_palette.primary.startswith("#")
        assert brand.fonts is not None
        assert brand.fonts.heading == "Inter"
        assert brand.logo_concept is not None
        assert brand.brand_voice is not None
        assert brand.css_variables is not None
        assert "--color-primary" in brand.css_variables

    def test_brand_color_palette_structure(self):
        """Test color palette has all required colors."""
        brand = get_default_brand_package("TestCo")
        palette = brand.color_palette

        assert palette.primary is not None
        assert palette.secondary is not None
        assert palette.accent is not None
        assert palette.background is not None
        assert palette.text is not None
        assert palette.text_muted is not None

    def test_brand_font_stack_structure(self):
        """Test font stack has all required fonts."""
        brand = get_default_brand_package("TestCo")
        fonts = brand.fonts

        assert fonts.heading is not None
        assert fonts.body is not None
        assert fonts.mono is not None
        assert fonts.google_fonts_url is not None
        assert "fonts.googleapis.com" in fonts.google_fonts_url

    def test_brand_voice_guidelines(self):
        """Test brand voice has guidelines."""
        brand = get_default_brand_package("TestCo")
        voice = brand.brand_voice

        assert voice.tone is not None
        assert len(voice.personality_traits) >= 3
        assert len(voice.key_messages) >= 3
        assert len(voice.words_to_use) >= 5
        assert len(voice.words_to_avoid) >= 3


# ============================================
# Landing Page Generator Tests (Phase 5.2)
# ============================================


class TestLandingPageGenerator:
    """Tests for landing page template generation."""

    def test_get_default_landing_page(self):
        """Test default landing page generation."""
        landing = get_default_landing_page("TestCo")

        assert landing.hero is not None
        assert landing.hero.headline is not None
        assert landing.hero.cta_primary is not None
        assert len(landing.features) >= 3
        assert len(landing.social_proof) >= 2
        assert len(landing.faq) >= 3
        assert landing.seo is not None

    def test_landing_hero_section(self):
        """Test hero section structure."""
        landing = get_default_landing_page("TestCo")
        hero = landing.hero

        assert len(hero.headline) <= 100
        assert len(hero.subheadline) <= 200
        assert len(hero.cta_primary) <= 30
        assert hero.hero_image_suggestion is not None

    def test_landing_features_structure(self):
        """Test features section structure."""
        landing = get_default_landing_page("TestCo")

        for feature in landing.features:
            assert len(feature.title) <= 50
            assert len(feature.description) <= 150
            assert feature.icon_suggestion is not None

    def test_landing_pricing_tiers(self):
        """Test pricing tiers structure."""
        landing = get_default_landing_page("TestCo")

        assert landing.pricing is not None
        assert len(landing.pricing) >= 2

        for tier in landing.pricing:
            assert tier.name is not None
            assert tier.price is not None
            assert len(tier.features) >= 3
            assert tier.cta is not None

    def test_landing_seo_metadata(self):
        """Test SEO metadata structure."""
        landing = get_default_landing_page("TestCo")
        seo = landing.seo

        assert len(seo.title) <= 60
        assert len(seo.description) <= 160
        assert len(seo.keywords) >= 5
        assert seo.og_title is not None
        assert seo.og_description is not None


# ============================================
# Export Service Tests (Phase 5.3)
# ============================================


class TestExportService:
    """Tests for export service functionality."""

    def test_export_format_enum(self):
        """Test export format enum values."""
        assert ExportFormat.PDF == "pdf"
        assert ExportFormat.CSV == "csv"
        assert ExportFormat.JSON == "json"

    def test_generate_pdf_content(self):
        """Test PDF HTML generation."""
        sections = [
            {"heading": "Section 1", "content": "Test content"},
            {"heading": "Section 2", "content": ["Item 1", "Item 2"]},
            {"heading": "Section 3", "content": {"Key": "Value"}},
        ]

        html = generate_pdf_content("Test Report", sections)

        assert "<!DOCTYPE html>" in html
        assert "Test Report" in html
        assert "Section 1" in html
        assert "Test content" in html
        assert "Item 1" in html
        assert "Key" in html

    def test_export_insight_csv(self):
        """Test insight CSV export."""
        insights = [
            {
                "id": str(uuid4()),
                "problem_statement": "Test problem",
                "proposed_solution": "Test solution",
                "market_size_estimate": "Large",
                "relevance_score": 0.85,
                "opportunity_score": 8,
                "created_at": datetime.now().isoformat(),
            },
            {
                "id": str(uuid4()),
                "problem_statement": "Another problem",
                "proposed_solution": "Another solution",
                "market_size_estimate": "Medium",
                "relevance_score": 0.72,
                "opportunity_score": 6,
                "created_at": datetime.now().isoformat(),
            },
        ]

        csv_content = export_insight_csv(insights)

        assert "id,problem_statement" in csv_content
        assert "Test problem" in csv_content
        assert "Another problem" in csv_content
        # CSV should have header + 2 data rows
        lines = csv_content.strip().split("\n")
        assert len(lines) == 3

    def test_export_insight_pdf(self):
        """Test insight PDF HTML export."""
        insight = {
            "id": str(uuid4()),
            "problem_statement": "Test problem statement",
            "proposed_solution": "Test solution",
            "market_size_estimate": "Large",
            "relevance_score": 0.85,
            "opportunity_score": 8,
            "problem_score": 7,
            "feasibility_score": 6,
            "competitors": [
                {"name": "Competitor A", "weakness": "Slow"}
            ],
        }

        html = export_insight_pdf(insight)

        assert "<!DOCTYPE html>" in html
        assert "Test problem statement" in html
        assert "Test solution" in html
        assert "8-Dimension Scoring" in html

    def test_export_analysis_csv(self):
        """Test analysis CSV export."""
        analyses = [
            {
                "id": str(uuid4()),
                "idea_description": "Test idea",
                "target_market": "Startups",
                "budget_range": "10k-50k",
                "status": "completed",
                "opportunity_score": 0.82,
                "market_fit_score": 0.75,
                "execution_readiness": 0.68,
                "market_analysis": {"tam": "$50B"},
                "risk_assessment": {"overall_risk": 0.45},
                "created_at": datetime.now().isoformat(),
            },
        ]

        csv_content = export_analysis_csv(analyses)

        assert "id,idea_description" in csv_content
        assert "Test idea" in csv_content
        assert "Startups" in csv_content

    def test_export_analysis_json(self):
        """Test analysis JSON export."""
        analysis = {
            "id": str(uuid4()),
            "idea_description": "Test idea",
            "target_market": "Startups",
            "status": "completed",
            "opportunity_score": 0.82,
        }

        json_str = export_analysis_json(analysis)
        data = json.loads(json_str)

        assert "meta" in data
        assert "analysis" in data
        assert data["meta"]["source"] == "StartInsight Research Agent"
        assert data["analysis"]["idea_description"] == "Test idea"

    def test_export_analysis_pdf(self):
        """Test analysis PDF HTML export."""
        analysis = {
            "id": str(uuid4()),
            "idea_description": "Test startup idea",
            "target_market": "B2B SaaS",
            "budget_range": "50k-200k",
            "status": "completed",
            "opportunity_score": 0.82,
            "market_fit_score": 0.75,
            "execution_readiness": 0.68,
            "market_analysis": {
                "tam": "$50B",
                "sam": "$5B",
                "som": "$50M",
                "growth_rate": 0.15,
                "market_maturity": "growing",
                "key_trends": ["AI adoption", "Automation"],
            },
            "value_equation": {
                "dream_outcome_score": 9,
                "perceived_likelihood_score": 7,
                "time_delay_score": 4,
                "effort_sacrifice_score": 3,
                "value_score": 5.25,
                "analysis": "Strong value proposition",
            },
            "competitor_landscape": [
                {"name": "Competitor A", "unique_value_prop": "Best analytics", "threat_level": "medium"},
            ],
            "execution_roadmap": [
                {"phase_number": 1, "name": "MVP", "duration": "4-6 weeks"},
            ],
            "risk_assessment": {
                "technical_risk": 4,
                "market_risk": 6,
                "team_risk": 3,
                "financial_risk": 5,
                "overall_risk": 0.45,
            },
        }

        html = export_analysis_pdf(analysis)

        assert "<!DOCTYPE html>" in html
        assert "Test startup idea" in html
        assert "Market Analysis" in html
        assert "Value Equation" in html
        assert "Competitor Landscape" in html
        assert "Risk Assessment" in html


# ============================================
# Real-time Feed Tests (Phase 5.4)
# ============================================


class TestRealtimeFeed:
    """Tests for real-time feed functionality."""

    def test_insight_feed_message_creation(self):
        """Test InsightFeedMessage model."""
        msg = InsightFeedMessage(
            event_type="new_insight",
            insight_id=str(uuid4()),
            timestamp=datetime.now().isoformat(),
            data={"problem_statement": "Test"},
        )

        assert msg.event_type == "new_insight"
        assert msg.insight_id is not None
        assert msg.timestamp is not None
        assert "problem_statement" in msg.data

    def test_event_store_creation(self):
        """Test EventStore initialization."""
        store = EventStore(max_events=100)

        assert store._max_events == 100
        assert len(store._events) == 0
        assert len(store._subscribers) == 0

    @pytest.mark.asyncio
    async def test_event_store_add_event(self):
        """Test adding events to store."""
        store = EventStore(max_events=10)

        event = InsightFeedMessage(
            event_type="new_insight",
            insight_id=str(uuid4()),
            timestamp=datetime.now().isoformat(),
            data={"test": True},
        )

        await store.add_event(event)

        recent = store.get_recent_events(count=10)
        assert len(recent) == 1
        assert recent[0].event_type == "new_insight"

    @pytest.mark.asyncio
    async def test_event_store_max_events(self):
        """Test event store respects max_events limit."""
        store = EventStore(max_events=5)

        # Add 10 events
        for i in range(10):
            event = InsightFeedMessage(
                event_type="new_insight",
                insight_id=str(uuid4()),
                timestamp=datetime.now().isoformat(),
                data={"index": i},
            )
            await store.add_event(event)

        recent = store.get_recent_events(count=100)
        assert len(recent) == 5  # Only last 5 kept
        # Should have events 5-9 (latest)
        assert recent[0].data["index"] == 5
        assert recent[-1].data["index"] == 9

    @pytest.mark.asyncio
    async def test_event_store_subscribe(self):
        """Test subscriber registration."""
        store = EventStore()

        queue = await store.subscribe("test-subscriber")

        assert "test-subscriber" in store._subscribers
        assert queue is not None

        await store.unsubscribe("test-subscriber")
        assert "test-subscriber" not in store._subscribers

    @pytest.mark.asyncio
    async def test_publish_new_insight(self):
        """Test publishing new insight event."""
        # Reset global event store
        import app.services.realtime_feed as feed_module
        feed_module._event_store = None

        insight_id = str(uuid4())
        insight_data = {
            "problem_statement": "Test problem",
            "relevance_score": 0.85,
        }

        await publish_new_insight(insight_id, insight_data)

        events = get_recent_insights(limit=10)
        assert len(events) >= 1
        assert events[-1].insight_id == insight_id

    def test_get_feed_stats(self):
        """Test feed statistics."""
        # Reset global event store
        import app.services.realtime_feed as feed_module
        feed_module._event_store = None

        stats = get_feed_stats()

        assert "status" in stats
        assert "subscriber_count" in stats
        assert "recent_event_count" in stats
        assert stats["status"] == "healthy"


# ============================================
# Service Import Tests
# ============================================


class TestServiceImports:
    """Test that all Phase 5.2-5.4 services can be imported."""

    def test_import_brand_generator(self):
        """Test brand generator imports."""
        from app.services.brand_generator import (
            BrandPackage,
            generate_brand_package,
            get_default_brand_package,
        )

        assert BrandPackage is not None
        assert generate_brand_package is not None
        assert get_default_brand_package is not None

    def test_import_landing_page(self):
        """Test landing page imports."""
        from app.services.landing_page import (
            LandingPageTemplate,
            generate_landing_page,
            get_default_landing_page,
        )

        assert LandingPageTemplate is not None
        assert generate_landing_page is not None
        assert get_default_landing_page is not None

    def test_import_export_service(self):
        """Test export service imports."""
        from app.services.export_service import (
            ExportFormat,
            export_insight_pdf,
            export_insight_csv,
            export_analysis_pdf,
            export_analysis_csv,
            export_analysis_json,
        )

        assert ExportFormat is not None
        assert export_insight_pdf is not None
        assert export_insight_csv is not None

    def test_import_realtime_feed(self):
        """Test realtime feed imports."""
        from app.services.realtime_feed import (
            InsightFeedMessage,
            subscribe_to_insights,
            unsubscribe_from_insights,
            publish_new_insight,
        )

        assert InsightFeedMessage is not None
        assert subscribe_to_insights is not None
        assert unsubscribe_from_insights is not None
