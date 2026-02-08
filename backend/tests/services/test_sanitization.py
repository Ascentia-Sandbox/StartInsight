"""Tests for input sanitization service."""


from app.services.sanitization import sanitize_html, sanitize_insight


class TestSanitizeHtml:
    """Test HTML sanitization function."""

    def test_strips_script_tags(self):
        """Script tags should be stripped (content may remain as harmless text)."""
        result = sanitize_html("<script>alert('XSS')</script>Safe text")
        assert "<script>" not in result
        assert "</script>" not in result
        assert "Safe text" in result

    def test_allows_safe_tags(self):
        """Allowed HTML tags should be preserved."""
        html = "<p>Hello <strong>world</strong></p>"
        result = sanitize_html(html)
        assert "<p>" in result
        assert "<strong>" in result

    def test_allows_links(self):
        """Anchor tags with href should be preserved."""
        html = '<a href="https://example.com" title="Example">Link</a>'
        result = sanitize_html(html)
        assert "<a" in result
        assert "href" in result

    def test_strips_onclick(self):
        """Event handlers like onclick should be stripped."""
        html = '<a href="#" onclick="alert(1)">Click</a>'
        result = sanitize_html(html)
        assert "onclick" not in result

    def test_strips_img_tag(self):
        """IMG tags should be stripped (not in allowed list)."""
        html = '<img src="x" onerror="alert(1)">'
        result = sanitize_html(html)
        assert "<img" not in result

    def test_strips_iframe(self):
        """Iframe tags should be stripped."""
        html = '<iframe src="https://evil.com"></iframe>'
        result = sanitize_html(html)
        assert "<iframe" not in result

    def test_none_input(self):
        """None input should return None."""
        assert sanitize_html(None) is None

    def test_empty_string(self):
        """Empty string should return empty string."""
        assert sanitize_html("") == ""

    def test_plain_text(self):
        """Plain text without HTML should pass through."""
        text = "This is plain text without any HTML"
        assert sanitize_html(text) == text

    def test_allows_list_elements(self):
        """UL, OL, LI tags should be allowed."""
        html = "<ul><li>Item 1</li><li>Item 2</li></ul>"
        result = sanitize_html(html)
        assert "<ul>" in result
        assert "<li>" in result

    def test_strips_style_tag(self):
        """Style tags should be stripped."""
        html = '<style>body{display:none}</style><p>Text</p>'
        result = sanitize_html(html)
        assert "<style>" not in result
        assert "<p>Text</p>" in result

    def test_strips_form_tags(self):
        """Form-related tags should be stripped."""
        html = '<form action="https://evil.com"><input type="text"><button>Submit</button></form>'
        result = sanitize_html(html)
        assert "<form" not in result
        assert "<input" not in result


class TestSanitizeInsight:
    """Test insight data sanitization."""

    def test_sanitizes_text_fields(self):
        """All text fields should be sanitized."""
        data = {
            "problem_statement": "<script>alert(1)</script>Real problem",
            "proposed_solution": "<p>Good solution</p>",
            "market_gap_analysis": "Plain text analysis",
        }
        result = sanitize_insight(data)
        assert "script" not in result["problem_statement"].lower()
        assert "Real problem" in result["problem_statement"]
        assert "<p>Good solution</p>" == result["proposed_solution"]
        assert result["market_gap_analysis"] == "Plain text analysis"

    def test_preserves_non_text_fields(self):
        """Non-text fields should be untouched."""
        data = {
            "problem_statement": "test",
            "relevance_score": 0.85,
            "market_size_estimate": "Large",
        }
        result = sanitize_insight(data)
        assert result["relevance_score"] == 0.85
        assert result["market_size_estimate"] == "Large"

    def test_handles_missing_fields(self):
        """Should not error on missing fields."""
        data = {"problem_statement": "test"}
        result = sanitize_insight(data)
        assert result["problem_statement"] == "test"

    def test_handles_none_fields(self):
        """None values in text fields should be preserved."""
        data = {"problem_statement": None}
        result = sanitize_insight(data)
        assert result["problem_statement"] is None

    def test_empty_dict(self):
        """Empty dict should return empty dict."""
        result = sanitize_insight({})
        assert result == {}
