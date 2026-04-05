"""SEO category definitions for programmatic landing pages.

Each category maps to a URL slug and a set of keywords used to match insights.
The frontend fetches insights by topic slug via GET /api/insights/by-topic/{slug}.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class SEOCategory:
    slug: str
    title: str
    description: str
    keywords: list[str]
    meta_description: str


SEO_CATEGORIES: dict[str, SEOCategory] = {
    cat.slug: cat
    for cat in [
        SEOCategory(
            slug="ai-saas-ideas",
            title="AI SaaS Startup Ideas",
            keywords=["AI", "SaaS", "machine learning", "artificial intelligence", "GPT", "LLM"],
            description="AI-powered SaaS opportunities discovered from real market signals.",
            meta_description="Discover AI SaaS startup ideas backed by data from Reddit, HN, and Google Trends. 8-dimension scoring.",
        ),
        SEOCategory(
            slug="fintech-startup-ideas",
            title="Fintech Startup Ideas",
            keywords=[
                "fintech",
                "payment",
                "banking",
                "finance",
                "neobank",
                "lending",
                "insurtech",
            ],
            description="Fintech market gaps and opportunities in payments, lending, and digital banking.",
            meta_description="Data-driven fintech startup ideas. Market gaps in payments, banking, and lending discovered by AI.",
        ),
        SEOCategory(
            slug="devtools-opportunities",
            title="Developer Tools Opportunities",
            keywords=["developer", "API", "tools", "SDK", "devops", "infrastructure", "CLI"],
            description="Developer tool opportunities: APIs, SDKs, and infrastructure gaps.",
            meta_description="Developer tools startup ideas. API, SDK, and infrastructure opportunities backed by real signals.",
        ),
        SEOCategory(
            slug="health-tech-ideas",
            title="Health Tech Startup Ideas",
            keywords=[
                "health",
                "medical",
                "wellness",
                "healthcare",
                "mental health",
                "fitness",
                "telehealth",
            ],
            description="Health tech opportunities in telemedicine, wellness, and digital health.",
            meta_description="Health tech startup ideas backed by data. Wellness, telehealth, and digital health market gaps.",
        ),
        SEOCategory(
            slug="ecommerce-gaps",
            title="E-Commerce Market Gaps",
            keywords=["ecommerce", "retail", "marketplace", "shopify", "D2C", "dropshipping"],
            description="E-commerce and marketplace opportunities from consumer demand signals.",
            meta_description="E-commerce startup ideas from real consumer signals. Marketplace and D2C opportunities.",
        ),
        SEOCategory(
            slug="edtech-opportunities",
            title="EdTech Startup Ideas",
            keywords=[
                "education",
                "learning",
                "course",
                "edtech",
                "tutoring",
                "skills",
                "training",
            ],
            description="Education technology gaps in online learning, upskilling, and training.",
            meta_description="EdTech startup ideas backed by data. Online learning and training market opportunities.",
        ),
        SEOCategory(
            slug="remote-work-tools",
            title="Remote Work Tool Ideas",
            keywords=["remote", "collaboration", "productivity", "async", "workspace", "team"],
            description="Remote work and collaboration tool opportunities.",
            meta_description="Remote work startup ideas. Collaboration and productivity tool gaps from real market signals.",
        ),
        SEOCategory(
            slug="sustainability-startups",
            title="Sustainability Startup Ideas",
            keywords=[
                "green",
                "sustainability",
                "climate",
                "carbon",
                "renewable",
                "ESG",
                "cleantech",
            ],
            description="Green tech and sustainability opportunities in climate, energy, and ESG.",
            meta_description="Sustainability startup ideas. Climate tech and green business opportunities backed by data.",
        ),
        SEOCategory(
            slug="malaysia-startup-ideas",
            title="Malaysia Startup Ideas",
            keywords=["Malaysia", "KL", "Kuala Lumpur", "MY", "Malaysian", "ASEAN"],
            description="Startup opportunities specific to the Malaysian market.",
            meta_description="Malaysia startup ideas. Market gaps and opportunities for Malaysian founders, backed by data.",
        ),
        SEOCategory(
            slug="singapore-startup-ideas",
            title="Singapore Startup Ideas",
            keywords=["Singapore", "SG", "Singaporean", "SEA", "ASEAN"],
            description="Startup opportunities specific to the Singapore market.",
            meta_description="Singapore startup ideas. Market gaps and opportunities for SG founders, backed by data.",
        ),
        SEOCategory(
            slug="no-code-automation",
            title="No-Code & Automation Ideas",
            keywords=["no-code", "low-code", "automation", "workflow", "zapier", "make", "n8n"],
            description="No-code and automation tool opportunities.",
            meta_description="No-code startup ideas. Automation and workflow tool opportunities from real market signals.",
        ),
        SEOCategory(
            slug="b2b-saas-ideas",
            title="B2B SaaS Startup Ideas",
            keywords=["B2B", "enterprise", "CRM", "ERP", "sales", "marketing automation"],
            description="B2B SaaS opportunities in sales, marketing, and enterprise software.",
            meta_description="B2B SaaS startup ideas. Enterprise software and sales tool market gaps backed by data.",
        ),
    ]
}


def get_all_categories() -> list[SEOCategory]:
    """Return all SEO categories for sitemap generation."""
    return list(SEO_CATEGORIES.values())


def get_category(slug: str) -> SEOCategory | None:
    """Look up a category by slug."""
    return SEO_CATEGORIES.get(slug)
