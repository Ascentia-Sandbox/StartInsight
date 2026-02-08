"""Input sanitization service for XSS prevention."""


import bleach

# Allowed HTML tags (safe subset for formatted text)
ALLOWED_TAGS = ['p', 'b', 'i', 'u', 'em', 'strong', 'a', 'ul', 'ol', 'li', 'br']

# Allowed attributes (only href and title for links)
ALLOWED_ATTRIBUTES = {'a': ['href', 'title']}


def sanitize_html(text: str | None) -> str | None:
    """
    Remove dangerous HTML/JS from user input.

    Args:
        text: Raw user input (may contain HTML/JS)

    Returns:
        Sanitized text with dangerous content stripped

    Example:
        >>> sanitize_html("<script>alert('XSS')</script><p>Safe text</p>")
        "&lt;script&gt;alert('XSS')&lt;/script&gt;<p>Safe text</p>"
    """
    if not text:
        return text

    return bleach.clean(
        text,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True,  # Strip disallowed tags instead of escaping
    )


def sanitize_insight(insight_data: dict) -> dict:
    """
    Sanitize all text fields in insight data.

    Args:
        insight_data: Dictionary containing insight fields

    Returns:
        Sanitized insight data

    Note:
        Modifies the dictionary in-place AND returns it
    """
    text_fields = [
        'problem_statement',
        'proposed_solution',
        'market_gap_analysis',
        'target_customer_segments',
        'competitive_landscape',
        'revenue_model_suggestions',
        'implementation_roadmap',
        'key_risks_and_challenges',
    ]

    for field in text_fields:
        if field in insight_data and insight_data[field]:
            insight_data[field] = sanitize_html(insight_data[field])

    return insight_data
