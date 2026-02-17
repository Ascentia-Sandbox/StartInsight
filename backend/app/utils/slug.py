"""Shared slug generation utility."""

import re


def generate_slug(title: str, max_length: int = 80) -> str:
    """Generate URL-friendly slug from title.

    Args:
        title: The text to slugify.
        max_length: Maximum slug length (default 80).

    Returns:
        URL-friendly slug string.
    """
    slug = title.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug[:max_length]
