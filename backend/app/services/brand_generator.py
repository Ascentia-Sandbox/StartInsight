"""Brand Package Generator - Phase 5.2.

Generates AI-powered brand packages including:
- Color palette (primary, secondary, accent)
- Font recommendations
- Logo concept suggestions
- Brand voice guidelines
"""

import logging
from typing import Any

from pydantic import BaseModel, Field
from pydantic_ai import Agent

from app.core.config import settings

logger = logging.getLogger(__name__)


# ============================================================
# Brand Package Schema
# ============================================================


class ColorPalette(BaseModel):
    """Brand color palette."""

    primary: str = Field(description="Primary brand color (hex, e.g., #3B82F6)")
    secondary: str = Field(description="Secondary color (hex)")
    accent: str = Field(description="Accent color for CTAs (hex)")
    background: str = Field(description="Background color (hex)")
    text: str = Field(description="Primary text color (hex)")
    text_muted: str = Field(description="Muted text color (hex)")


class FontStack(BaseModel):
    """Brand font recommendations."""

    heading: str = Field(description="Heading font (e.g., 'Inter', 'Poppins')")
    body: str = Field(description="Body text font")
    mono: str = Field(description="Monospace font for code")
    google_fonts_url: str = Field(description="Google Fonts import URL")


class LogoConcept(BaseModel):
    """Logo design concept."""

    style: str = Field(description="Logo style (wordmark, icon, combination, abstract)")
    concept: str = Field(description="Logo concept description")
    symbol_suggestion: str = Field(description="Suggested symbol or icon")
    tagline: str = Field(description="Brand tagline suggestion")


class BrandVoice(BaseModel):
    """Brand voice and messaging guidelines."""

    tone: str = Field(description="Brand tone (professional, friendly, playful, etc.)")
    personality_traits: list[str] = Field(
        min_length=3, max_length=5, description="3-5 brand personality traits"
    )
    key_messages: list[str] = Field(
        min_length=3, max_length=5, description="3-5 core messaging points"
    )
    words_to_use: list[str] = Field(
        min_length=5, max_length=10, description="Words that embody the brand"
    )
    words_to_avoid: list[str] = Field(
        min_length=3, max_length=5, description="Words to avoid"
    )


class BrandPackage(BaseModel):
    """Complete brand package output."""

    company_name: str
    industry: str
    target_audience: str
    color_palette: ColorPalette
    fonts: FontStack
    logo_concept: LogoConcept
    brand_voice: BrandVoice
    css_variables: str = Field(description="CSS custom properties for the brand")


# ============================================================
# Brand Generator System Prompt
# ============================================================

BRAND_SYSTEM_PROMPT = """You are an expert brand strategist and designer.
Given a startup idea and target market, create a cohesive brand package.

## Guidelines

### Color Palette
- Choose colors that evoke the right emotions for the industry
- Ensure sufficient contrast for accessibility (WCAG 2.1 AA)
- Consider color psychology and cultural associations
- Provide hex values (e.g., #3B82F6)

### Font Selection
- Choose readable, web-safe fonts available on Google Fonts
- Pair complementary heading and body fonts
- Consider the brand personality

### Logo Concept
- Describe a logo that's simple, memorable, and scalable
- Suggest an icon/symbol that represents the brand
- Provide a memorable tagline

### Brand Voice
- Define tone that resonates with target audience
- List personality traits that humanize the brand
- Provide actionable messaging guidelines

### CSS Variables
Generate CSS custom properties for easy integration:
```css
:root {
  --color-primary: #hexcode;
  --color-secondary: #hexcode;
  --font-heading: 'FontName', sans-serif;
  ...
}
```

Be specific, actionable, and creative. Avoid generic suggestions."""


# ============================================================
# PydanticAI Agent Configuration
# ============================================================


def get_brand_agent() -> Agent:
    """Get PydanticAI agent for brand generation (API key from GOOGLE_API_KEY env)."""
    return Agent(
        model="google-gla:gemini-2.0-flash",
        system_prompt=BRAND_SYSTEM_PROMPT,
        output_type=BrandPackage,
    )


# ============================================================
# Brand Generation Function
# ============================================================


async def generate_brand_package(
    company_name: str,
    idea_description: str,
    target_market: str,
    industry: str,
    brand_keywords: list[str] | None = None,
) -> BrandPackage:
    """
    Generate a brand package for a startup idea.

    Args:
        company_name: Name of the company/product
        idea_description: Description of the startup idea
        target_market: Target audience description
        industry: Industry/vertical (e.g., "SaaS", "FinTech")
        brand_keywords: Optional keywords to guide branding (e.g., ["innovative", "trustworthy"])

    Returns:
        BrandPackage: Complete brand package with colors, fonts, logo concept, voice
    """
    keywords_str = ", ".join(brand_keywords) if brand_keywords else "modern, innovative"

    prompt = f"""Create a brand package for this startup:

## Company Name
{company_name}

## Idea Description
{idea_description}

## Target Market
{target_market}

## Industry
{industry}

## Brand Keywords
{keywords_str}

Generate a complete, cohesive brand package including:
1. Color palette (primary, secondary, accent, background, text colors)
2. Font stack (heading, body, monospace fonts)
3. Logo concept (style, symbol, tagline)
4. Brand voice (tone, personality, messaging)
5. CSS variables for easy integration"""

    try:
        agent = get_brand_agent()
        result = await agent.run(prompt)
        brand_package = result.output

        logger.info(f"Brand package generated for '{company_name}'")
        return brand_package

    except Exception as e:
        logger.error(f"Brand generation failed: {e}")
        raise


# ============================================================
# Default/Fallback Brand Package
# ============================================================


def get_default_brand_package(company_name: str) -> BrandPackage:
    """Get a default brand package when generation fails or for testing."""
    return BrandPackage(
        company_name=company_name,
        industry="Technology",
        target_audience="General",
        color_palette=ColorPalette(
            primary="#3B82F6",  # Blue
            secondary="#10B981",  # Green
            accent="#F59E0B",  # Amber
            background="#FFFFFF",
            text="#1F2937",
            text_muted="#6B7280",
        ),
        fonts=FontStack(
            heading="Inter",
            body="Inter",
            mono="JetBrains Mono",
            google_fonts_url="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono&display=swap",
        ),
        logo_concept=LogoConcept(
            style="wordmark",
            concept="Clean, modern wordmark with subtle geometric accent",
            symbol_suggestion="Abstract geometric shape representing growth",
            tagline="Your tagline here",
        ),
        brand_voice=BrandVoice(
            tone="Professional yet approachable",
            personality_traits=["Innovative", "Trustworthy", "Friendly", "Expert"],
            key_messages=[
                "We solve real problems",
                "Built for modern teams",
                "Simple yet powerful",
            ],
            words_to_use=["empower", "transform", "streamline", "intelligent", "seamless"],
            words_to_avoid=["complicated", "basic", "cheap", "legacy"],
        ),
        css_variables=""":root {
  --color-primary: #3B82F6;
  --color-secondary: #10B981;
  --color-accent: #F59E0B;
  --color-background: #FFFFFF;
  --color-text: #1F2937;
  --color-text-muted: #6B7280;
  --font-heading: 'Inter', sans-serif;
  --font-body: 'Inter', sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
}""",
    )
