"""fix_insight_slugs

Revision ID: c007
Revises: c006
Create Date: 2026-02-16 14:00:00.000000

"""
import re
from collections.abc import Sequence

from sqlalchemy import text

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c007"
down_revision: str | None = "c006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _extract_title(proposed_solution: str, max_chars: int = 80) -> str:
    """Extract a short title from proposed_solution.

    Strategy: take the text before the first 'that' clause as a natural break.
    Cap at max_chars, breaking at last word boundary.
    """
    if not proposed_solution:
        return "Untitled Insight"

    text_val = proposed_solution.strip()

    # Try splitting at first " that " (case-insensitive)
    that_match = re.search(r"\s+that\s+", text_val, re.IGNORECASE)
    if that_match and that_match.start() > 10:
        text_val = text_val[: that_match.start()]

    # Also try splitting at " which " as a secondary break
    if len(text_val) > max_chars:
        which_match = re.search(r"\s+which\s+", text_val, re.IGNORECASE)
        if which_match and which_match.start() > 10:
            text_val = text_val[: which_match.start()]

    # Cap at max_chars, break at last word boundary
    if len(text_val) > max_chars:
        text_val = text_val[:max_chars]
        last_space = text_val.rfind(" ")
        if last_space > 20:
            text_val = text_val[:last_space]

    # Title case it for display
    text_val = text_val.strip().rstrip(".,;:-")
    # Capitalize first letter of each major word
    words = text_val.split()
    minor_words = {"a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
    result = []
    for i, word in enumerate(words):
        if i == 0 or word.lower() not in minor_words:
            result.append(word.capitalize())
        else:
            result.append(word.lower())

    return " ".join(result) if result else "Untitled Insight"


def _generate_slug(title: str, max_length: int = 80) -> str:
    """Generate URL-friendly slug from title."""
    slug = title.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug[:max_length]


def upgrade() -> None:
    conn = op.get_bind()

    # Fetch all insights that need fixing:
    # - title IS NULL (never populated)
    # - OR slug is too long (>80 chars, from old c006 migration)
    rows = conn.execute(
        text(
            "SELECT id, proposed_solution, slug, title FROM insights "
            "WHERE title IS NULL OR LENGTH(slug) > 80"
        )
    ).fetchall()

    if not rows:
        return

    # Collect all existing slugs to ensure uniqueness
    existing_slugs = set()
    all_slugs = conn.execute(text("SELECT slug FROM insights WHERE slug IS NOT NULL")).fetchall()
    for row in all_slugs:
        existing_slugs.add(row[0])

    for row in rows:
        insight_id = row[0]
        proposed_solution = row[1] or ""
        old_slug = row[2]
        existing_title = row[3]

        # Extract title only if not already set
        title = existing_title or _extract_title(proposed_solution)

        # Generate new short slug from title
        base_slug = _generate_slug(title)
        if not base_slug:
            base_slug = "insight"

        # Ensure uniqueness
        new_slug = base_slug
        counter = 1
        while new_slug in existing_slugs:
            suffix = f"-{counter}"
            new_slug = base_slug[: 80 - len(suffix)] + suffix
            counter += 1

        existing_slugs.add(new_slug)
        # Remove old slug from set if different
        if old_slug and old_slug != new_slug:
            existing_slugs.discard(old_slug)

        conn.execute(
            text("UPDATE insights SET title = :title, slug = :slug WHERE id = :id"),
            {"title": title, "slug": new_slug, "id": insight_id},
        )


def downgrade() -> None:
    # Set title back to NULL (slug restore is not implemented for simplicity)
    op.execute(text("UPDATE insights SET title = NULL"))
