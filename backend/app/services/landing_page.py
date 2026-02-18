"""Landing Page Generator - Phase 5.2.

Generates AI-powered landing page templates including:
- Hero section copy
- Features section
- Social proof suggestions
- CTA optimization
- SEO metadata
"""

import logging

from pydantic import BaseModel, Field
from pydantic_ai import Agent

from app.core.config import settings
from app.services.brand_generator import BrandPackage

logger = logging.getLogger(__name__)


# ============================================================
# Landing Page Schema
# ============================================================


class HeroSection(BaseModel):
    """Hero section content."""

    headline: str = Field(max_length=100, description="Main headline (max 100 chars)")
    subheadline: str = Field(max_length=200, description="Supporting subheadline")
    cta_primary: str = Field(max_length=30, description="Primary CTA button text")
    cta_secondary: str = Field(max_length=30, description="Secondary CTA text")
    hero_image_suggestion: str = Field(
        description="Description of ideal hero image/illustration"
    )


class FeatureItem(BaseModel):
    """Individual feature item."""

    title: str = Field(max_length=50, description="Feature title")
    description: str = Field(max_length=150, description="Feature description")
    icon_suggestion: str = Field(description="Suggested icon name (Lucide/Heroicons)")


class SocialProofItem(BaseModel):
    """Social proof element."""

    type: str = Field(description="Type: testimonial, stat, logo, case_study")
    content: str = Field(description="Content or placeholder text")
    attribution: str | None = Field(
        default=None, description="Attribution (name, company)"
    )


class PricingTier(BaseModel):
    """Pricing tier definition."""

    name: str = Field(description="Tier name (Free, Starter, Pro)")
    price: str = Field(description="Price string ($0, $19/mo)")
    features: list[str] = Field(
        min_length=3, max_length=7, description="3-7 features"
    )
    cta: str = Field(description="CTA button text")
    highlighted: bool = Field(default=False, description="Is this the recommended tier?")


class SEOMetadata(BaseModel):
    """SEO optimization metadata."""

    title: str = Field(max_length=60, description="Page title (max 60 chars)")
    description: str = Field(max_length=160, description="Meta description (max 160)")
    keywords: list[str] = Field(
        min_length=5, max_length=10, description="Target keywords"
    )
    og_title: str = Field(description="Open Graph title")
    og_description: str = Field(description="Open Graph description")


class LandingPageTemplate(BaseModel):
    """Complete landing page template."""

    hero: HeroSection
    features: list[FeatureItem] = Field(
        min_length=3, max_length=6, description="3-6 features"
    )
    social_proof: list[SocialProofItem] = Field(
        min_length=2, max_length=5, description="2-5 social proof items"
    )
    pricing: list[PricingTier] | None = Field(
        default=None, description="Optional pricing tiers"
    )
    faq: list[dict[str, str]] = Field(
        min_length=3, max_length=8, description="3-8 FAQ items"
    )
    seo: SEOMetadata
    html_structure: str = Field(
        description="HTML structure suggestion with Tailwind classes"
    )


# ============================================================
# Landing Page System Prompt
# ============================================================

LANDING_PAGE_SYSTEM_PROMPT = """You are an expert landing page copywriter and conversion optimizer.
Create high-converting landing page content that's specific, compelling, and actionable.

## Guidelines

### Hero Section
- Headline: Clear value proposition in <10 words
- Subheadline: Expand on the benefit, address pain point
- CTA: Action-oriented, specific (not "Learn More")
- Suggest an appropriate hero visual

### Features Section
- Focus on benefits, not features
- Use the "So you can..." framework
- Suggest appropriate icons (Lucide/Heroicons names)

### Social Proof
- Include mix of testimonials, stats, and logos
- Make testimonials specific and believable
- Stats should be concrete (numbers, percentages)

### FAQ Section
- Address common objections
- Cover pricing, security, onboarding
- Keep answers concise

### SEO
- Include target keywords naturally
- Write for humans first, search engines second
- Optimize meta title and description

### HTML Structure
Provide a suggested HTML structure using:
- Semantic HTML5 elements
- Tailwind CSS classes
- Responsive design considerations

Be specific to the product. Avoid generic startup cliches."""


# ============================================================
# PydanticAI Agent Configuration
# ============================================================


def get_landing_page_agent() -> Agent:
    """Get PydanticAI agent for landing page generation (API key from GOOGLE_API_KEY env)."""
    return Agent(
        model=settings.default_llm_model,
        system_prompt=LANDING_PAGE_SYSTEM_PROMPT,
        output_type=LandingPageTemplate,
    )


# ============================================================
# Landing Page Generation Function
# ============================================================


async def generate_landing_page(
    company_name: str,
    idea_description: str,
    target_market: str,
    value_proposition: str,
    brand_package: BrandPackage | None = None,
    include_pricing: bool = True,
) -> LandingPageTemplate:
    """
    Generate a landing page template for a startup idea.

    Args:
        company_name: Name of the company/product
        idea_description: Description of the startup idea
        target_market: Target audience description
        value_proposition: Core value proposition
        brand_package: Optional brand package for consistency
        include_pricing: Whether to include pricing section

    Returns:
        LandingPageTemplate: Complete landing page content template
    """
    brand_context = ""
    if brand_package:
        brand_context = f"""
## Brand Guidelines
- Tone: {brand_package.brand_voice.tone}
- Key Messages: {', '.join(brand_package.brand_voice.key_messages)}
- Colors: Primary {brand_package.color_palette.primary}
"""

    pricing_instruction = (
        "Include 3 pricing tiers (Free, Starter $19/mo, Pro $49/mo)"
        if include_pricing
        else "Do NOT include pricing section"
    )

    prompt = f"""Create landing page content for this startup:

## Company Name
{company_name}

## Product Description
{idea_description}

## Target Market
{target_market}

## Value Proposition
{value_proposition}
{brand_context}
## Instructions
{pricing_instruction}

Generate complete landing page content including:
1. Hero section (headline, subheadline, CTAs)
2. 3-6 feature cards with benefits and icon suggestions
3. 2-5 social proof elements (testimonials, stats)
4. 3-8 FAQ items addressing objections
5. SEO metadata (title, description, keywords)
6. HTML structure with Tailwind CSS"""

    try:
        agent = get_landing_page_agent()
        result = await agent.run(prompt)
        landing_page = result.output

        logger.info(f"Landing page generated for '{company_name}'")
        return landing_page

    except Exception as e:
        logger.error(f"Landing page generation failed: {e}")
        raise


# ============================================================
# Default/Fallback Landing Page
# ============================================================


def get_default_landing_page(company_name: str) -> LandingPageTemplate:
    """Get a default landing page template for testing."""
    return LandingPageTemplate(
        hero=HeroSection(
            headline=f"Welcome to {company_name}",
            subheadline="The modern solution for your business needs",
            cta_primary="Get Started Free",
            cta_secondary="See Demo",
            hero_image_suggestion="Abstract illustration showing growth and connectivity",
        ),
        features=[
            FeatureItem(
                title="Easy to Use",
                description="Get started in minutes with our intuitive interface",
                icon_suggestion="Zap",
            ),
            FeatureItem(
                title="Powerful Analytics",
                description="Make data-driven decisions with real-time insights",
                icon_suggestion="BarChart3",
            ),
            FeatureItem(
                title="Secure & Reliable",
                description="Enterprise-grade security with 99.9% uptime",
                icon_suggestion="Shield",
            ),
        ],
        social_proof=[
            SocialProofItem(
                type="stat",
                content="10,000+ users trust us",
                attribution=None,
            ),
            SocialProofItem(
                type="testimonial",
                content="This product transformed how we work.",
                attribution="Jane Doe, CEO at TechCorp",
            ),
        ],
        pricing=[
            PricingTier(
                name="Free",
                price="$0",
                features=["5 projects", "Basic analytics", "Community support"],
                cta="Start Free",
                highlighted=False,
            ),
            PricingTier(
                name="Pro",
                price="$19/mo",
                features=[
                    "Unlimited projects",
                    "Advanced analytics",
                    "Priority support",
                    "Team collaboration",
                ],
                cta="Start Pro Trial",
                highlighted=True,
            ),
            PricingTier(
                name="Enterprise",
                price="Custom",
                features=[
                    "Everything in Pro",
                    "Custom integrations",
                    "Dedicated support",
                    "SLA guarantee",
                ],
                cta="Contact Sales",
                highlighted=False,
            ),
        ],
        faq=[
            {"question": "How do I get started?", "answer": "Sign up for free and follow our quick setup guide."},
            {"question": "Can I cancel anytime?", "answer": "Yes, cancel your subscription at any time with no fees."},
            {"question": "Is my data secure?", "answer": "We use enterprise-grade encryption and are SOC 2 compliant."},
        ],
        seo=SEOMetadata(
            title=f"{company_name} - Modern Solution for Your Needs",
            description=f"{company_name} helps you achieve more with less effort. Start free today.",
            keywords=["product", "solution", "business", "automation", "productivity"],
            og_title=f"{company_name} - Get Started Free",
            og_description=f"Join thousands using {company_name} to transform their workflow.",
        ),
        html_structure="""<main class="min-h-screen">
  <!-- Hero -->
  <section class="py-20 px-4 text-center bg-gradient-to-b from-primary/10">
    <h1 class="text-5xl font-bold mb-4">{headline}</h1>
    <p class="text-xl text-muted-foreground mb-8">{subheadline}</p>
    <div class="flex gap-4 justify-center">
      <Button size="lg">{cta_primary}</Button>
      <Button variant="outline" size="lg">{cta_secondary}</Button>
    </div>
  </section>

  <!-- Features -->
  <section class="py-16 px-4">
    <div class="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
      {features.map(feature => <FeatureCard {...feature} />)}
    </div>
  </section>

  <!-- Social Proof -->
  <section class="py-16 px-4 bg-muted/50">
    {social_proof}
  </section>

  <!-- Pricing -->
  <section class="py-16 px-4">
    <PricingTable tiers={pricing} />
  </section>

  <!-- FAQ -->
  <section class="py-16 px-4">
    <Accordion items={faq} />
  </section>
</main>""",
    )
