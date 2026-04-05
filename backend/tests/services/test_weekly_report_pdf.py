"""Unit tests for weekly_report_pdf service."""

from datetime import date

from app.services.weekly_report_pdf import build_weekly_report_html

SAMPLE_INSIGHTS = [
    {
        "title": f"Insight {i}",
        "problem_statement": f"Problem statement for insight {i} with enough text.",
        "relevance_score": f"{70 + i}%",
        "market_size": f"${i * 10}M",
        "revenue_potential": f"${i * 5}M",
        "opportunity_score": 70 + i,
        "proposed_solution": f"Solution for insight {i}.",
        "insight_url": f"https://startinsight.co/insights/id-{i}",
    }
    for i in range(1, 11)
]


class TestBuildWeeklyReportHtml:
    """Tests for build_weekly_report_html."""

    def test_returns_string(self):
        html = build_weekly_report_html(SAMPLE_INSIGHTS, week_number=13)
        assert isinstance(html, str)
        assert len(html) > 500

    def test_contains_doctype(self):
        html = build_weekly_report_html(SAMPLE_INSIGHTS, week_number=13)
        assert "<!DOCTYPE html>" in html

    def test_contains_week_number(self):
        html = build_weekly_report_html(SAMPLE_INSIGHTS, week_number=13)
        assert "013" in html  # zero-padded issue number

    def test_free_version_contains_cta(self):
        html = build_weekly_report_html(SAMPLE_INSIGHTS, week_number=13, is_pro=False)
        assert "startinsight.co/pricing" in html
        assert "Unlock the full analysis" in html

    def test_pro_version_has_no_cta(self):
        html = build_weekly_report_html(SAMPLE_INSIGHTS, week_number=13, is_pro=True)
        assert "startinsight.co/pricing" not in html

    def test_free_version_no_market_size(self):
        html = build_weekly_report_html(SAMPLE_INSIGHTS, week_number=13, is_pro=False)
        # Free cards don't show market size or proposed solution columns
        assert "Market Size" not in html

    def test_pro_version_shows_market_size(self):
        html = build_weekly_report_html(SAMPLE_INSIGHTS, week_number=13, is_pro=True)
        assert "Market Size" in html

    def test_all_10_insight_titles_present(self):
        html = build_weekly_report_html(SAMPLE_INSIGHTS, week_number=13)
        for i in range(1, 11):
            assert f"Insight {i}" in html

    def test_insight_urls_in_pro_version(self):
        html = build_weekly_report_html(SAMPLE_INSIGHTS, week_number=13, is_pro=True)
        assert "https://startinsight.co/insights/id-1" in html

    def test_brand_color_present(self):
        html = build_weekly_report_html(SAMPLE_INSIGHTS, week_number=13)
        assert "#0D7377" in html  # teal brand token

    def test_empty_insights_list(self):
        html = build_weekly_report_html([], week_number=1)
        assert "<!DOCTYPE html>" in html  # still renders without crashing

    def test_truncates_long_problem_statement_free(self):
        long_insight = [{**SAMPLE_INSIGHTS[0], "problem_statement": "x" * 300}]
        html = build_weekly_report_html(long_insight, week_number=1, is_pro=False)
        assert "…" in html  # truncated with ellipsis

    def test_cover_shows_free_badge(self):
        html = build_weekly_report_html(SAMPLE_INSIGHTS, week_number=5, is_pro=False)
        assert "FREE PREVIEW" in html

    def test_cover_shows_pro_badge(self):
        html = build_weekly_report_html(SAMPLE_INSIGHTS, week_number=5, is_pro=True)
        assert ">PRO<" in html

    def test_current_year_in_cover(self):
        html = build_weekly_report_html(SAMPLE_INSIGHTS, week_number=1)
        assert str(date.today().year) in html
