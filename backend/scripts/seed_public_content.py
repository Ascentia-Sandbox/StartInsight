"""Seed script for Phase 12 public content (Tools, SuccessStories, Trends, MarketInsights).

Run with: uv run python scripts/seed_public_content.py
"""

import asyncio
import logging
import random
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.market_insight import MarketInsight
from app.models.success_story import SuccessStory
from app.models.tool import Tool
from app.models.trend import Trend

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sample Tools Data (54 tools)
TOOLS_DATA = [
    # Payments
    {"name": "Stripe", "tagline": "Online payment processing", "description": "The complete platform for online payments. Accept payments, send payouts, and manage your business online.", "category": "Payments", "pricing": "2.9% + $0.30 per transaction", "website_url": "https://stripe.com", "is_featured": True},
    {"name": "PayPal", "tagline": "Digital payments leader", "description": "PayPal enables global commerce through transferring money online.", "category": "Payments", "pricing": "2.9% + $0.30 per transaction", "website_url": "https://paypal.com", "is_featured": False},
    {"name": "Square", "tagline": "Payments for all business sizes", "description": "Square offers payment processing and point-of-sale solutions.", "category": "Payments", "pricing": "2.6% + $0.10 per tap", "website_url": "https://squareup.com", "is_featured": False},
    {"name": "Paddle", "tagline": "Complete payments infrastructure for SaaS", "description": "Paddle handles payments, tax compliance, and subscription management for software companies.", "category": "Payments", "pricing": "5% + $0.50 per transaction", "website_url": "https://paddle.com", "is_featured": True},
    # No-Code
    {"name": "Bubble", "tagline": "Build web apps without code", "description": "The most powerful no-code platform for building complete web applications.", "category": "No-Code", "pricing": "Freemium, Pro from $29/mo", "website_url": "https://bubble.io", "is_featured": True},
    {"name": "Webflow", "tagline": "Visual web development platform", "description": "Build professional websites visually with no code.", "category": "No-Code", "pricing": "Freemium, from $14/mo", "website_url": "https://webflow.com", "is_featured": True},
    {"name": "Airtable", "tagline": "Low-code app platform", "description": "Create custom apps and workflows without programming.", "category": "No-Code", "pricing": "Freemium, Plus from $10/mo", "website_url": "https://airtable.com", "is_featured": False},
    {"name": "Zapier", "tagline": "Connect your apps and automate workflows", "description": "Automate repetitive tasks by connecting 5,000+ apps.", "category": "No-Code", "pricing": "Freemium, Starter from $19.99/mo", "website_url": "https://zapier.com", "is_featured": True},
    # Analytics
    {"name": "Mixpanel", "tagline": "Product analytics for teams", "description": "Understand how users engage with your product.", "category": "Analytics", "pricing": "Freemium, Growth from $20/mo", "website_url": "https://mixpanel.com", "is_featured": True},
    {"name": "Amplitude", "tagline": "Digital analytics platform", "description": "Build better products with behavioral analytics.", "category": "Analytics", "pricing": "Freemium, Plus from $49/mo", "website_url": "https://amplitude.com", "is_featured": False},
    {"name": "Posthog", "tagline": "Open-source product analytics", "description": "Self-hosted product analytics with feature flags and session recordings.", "category": "Analytics", "pricing": "Free tier, from $0/mo", "website_url": "https://posthog.com", "is_featured": True},
    {"name": "Plausible", "tagline": "Simple, privacy-friendly analytics", "description": "Lightweight analytics alternative to Google Analytics.", "category": "Analytics", "pricing": "From $9/mo", "website_url": "https://plausible.io", "is_featured": False},
    # Marketing
    {"name": "Mailchimp", "tagline": "Email marketing made easy", "description": "Marketing automation platform with email campaigns, landing pages, and more.", "category": "Marketing", "pricing": "Freemium, Essentials from $13/mo", "website_url": "https://mailchimp.com", "is_featured": True},
    {"name": "ConvertKit", "tagline": "Email marketing for creators", "description": "Build your audience with landing pages, forms, and email sequences.", "category": "Marketing", "pricing": "Free tier, Creator from $9/mo", "website_url": "https://convertkit.com", "is_featured": False},
    {"name": "Beehiiv", "tagline": "Newsletter platform built for growth", "description": "The newsletter platform built for scale with monetization tools.", "category": "Marketing", "pricing": "Freemium, Scale from $42/mo", "website_url": "https://beehiiv.com", "is_featured": True},
    {"name": "Buffer", "tagline": "Social media management", "description": "Plan, schedule, and publish social media content.", "category": "Marketing", "pricing": "Freemium, Essentials from $5/mo", "website_url": "https://buffer.com", "is_featured": False},
    # AI/ML
    {"name": "OpenAI API", "tagline": "Advanced AI models", "description": "Access GPT-4 and other AI models via API.", "category": "AI/ML", "pricing": "Pay per use", "website_url": "https://openai.com", "is_featured": True},
    {"name": "Anthropic Claude", "tagline": "Helpful, harmless, and honest AI", "description": "Claude is an AI assistant from Anthropic designed to be helpful, harmless, and honest.", "category": "AI/ML", "pricing": "Pay per use", "website_url": "https://anthropic.com", "is_featured": True},
    {"name": "Hugging Face", "tagline": "The AI community building the future", "description": "Open-source ML library and model hub.", "category": "AI/ML", "pricing": "Freemium", "website_url": "https://huggingface.co", "is_featured": False},
    {"name": "Replicate", "tagline": "Run AI models in the cloud", "description": "Deploy machine learning models with one line of code.", "category": "AI/ML", "pricing": "Pay per use", "website_url": "https://replicate.com", "is_featured": False},
    # Development
    {"name": "Vercel", "tagline": "Develop. Preview. Ship.", "description": "Frontend cloud platform for deploying web applications.", "category": "Development", "pricing": "Freemium, Pro from $20/mo", "website_url": "https://vercel.com", "is_featured": True},
    {"name": "Railway", "tagline": "Instant deployment for apps", "description": "Infrastructure platform for deploying any application.", "category": "Development", "pricing": "Freemium, from $5/mo", "website_url": "https://railway.app", "is_featured": True},
    {"name": "Supabase", "tagline": "Open-source Firebase alternative", "description": "PostgreSQL database with auth, storage, and real-time subscriptions.", "category": "Development", "pricing": "Freemium, Pro from $25/mo", "website_url": "https://supabase.com", "is_featured": True},
    {"name": "PlanetScale", "tagline": "Serverless MySQL platform", "description": "MySQL-compatible serverless database with branching.", "category": "Development", "pricing": "Freemium, Scaler from $29/mo", "website_url": "https://planetscale.com", "is_featured": False},
]

# Sample Success Stories Data
SUCCESS_STORIES_DATA = [
    {
        "founder_name": "Sarah Chen",
        "company_name": "MetricMate",
        "tagline": "AI-powered financial forecasting for startups",
        "idea_summary": "After struggling with financial projections at her previous startup, Sarah built MetricMate to help founders create accurate forecasts using AI. The tool connects to accounting software and generates investor-ready projections.",
        "journey_narrative": "I discovered this idea through StartInsight while looking for pain points in the startup finance space. The 8-dimension score was 87/100, with especially high marks for market timing and competition.\n\nThe first version was built in 3 weeks using Lovable (exported directly from StartInsight). We launched on Product Hunt and hit #2 Product of the Day.\n\nWithin 6 months, we had 500 paying customers and raised a $2M seed round. The AI research report from StartInsight was invaluable during investor pitches—it showed the exact market size and competitive landscape.",
        "metrics": {"mrr": 45000, "users": 1200, "funding": "$2M Seed", "growth": "25%"},
        "timeline": [
            {"date": "Jan 2024", "milestone": "Discovered idea on StartInsight"},
            {"date": "Feb 2024", "milestone": "Built MVP with Lovable integration"},
            {"date": "Mar 2024", "milestone": "Launched on Product Hunt (#2)"},
            {"date": "Jun 2024", "milestone": "500 paying customers"},
            {"date": "Aug 2024", "milestone": "$2M seed round closed"},
        ],
        "is_featured": True,
    },
    {
        "founder_name": "Marcus Johnson",
        "company_name": "DevReview",
        "tagline": "Automated code review powered by AI",
        "idea_summary": "Marcus noticed developers spending 30% of their time on code reviews. DevReview uses AI to automate repetitive review tasks, flagging issues and suggesting improvements before human reviewers see the code.",
        "journey_narrative": "The idea came from a Reddit discussion I found through StartInsight's trend analysis. Developers were complaining about code review bottlenecks—the thread had 2,000+ upvotes.\n\nI used the Research Agent to validate the market. It found 15 competitors but identified a gap in AI-powered solutions for enterprise security requirements.\n\nWe bootstrapped to $20K MRR before raising a small angel round. The brand package from StartInsight gave us a professional identity from day one.",
        "metrics": {"mrr": 75000, "users": 340, "funding": "$500K Angel"},
        "timeline": [
            {"date": "Mar 2024", "milestone": "Identified opportunity via Reddit trends"},
            {"date": "Apr 2024", "milestone": "Completed 40-step AI research"},
            {"date": "Jun 2024", "milestone": "First paying customer"},
            {"date": "Sep 2024", "milestone": "$20K MRR milestone"},
            {"date": "Nov 2024", "milestone": "Closed $500K angel round"},
        ],
        "is_featured": True,
    },
    {
        "founder_name": "Emily Rodriguez",
        "company_name": "SupplySync",
        "tagline": "Supply chain visibility for SMBs",
        "idea_summary": "Small manufacturers lacked visibility into their supply chains. SupplySync provides real-time tracking, demand forecasting, and supplier risk monitoring at prices SMBs can afford.",
        "journey_narrative": "I was working in supply chain consulting when I used StartInsight to explore startup ideas. The platform surfaced a trend around supply chain disruptions affecting small manufacturers.\n\nThe competitive analysis showed enterprise solutions were too expensive for SMBs—a clear market gap. I partnered with a technical co-founder and we built the MVP in 2 months.\n\nWe're now at $150K MRR with 89 manufacturing customers. The StartInsight research helped us secure pilot customers before we even had a product.",
        "metrics": {"mrr": 150000, "users": 89, "funding": "$3.5M Seed", "growth": "18%"},
        "timeline": [
            {"date": "Dec 2023", "milestone": "Discovered market gap via StartInsight"},
            {"date": "Feb 2024", "milestone": "Found technical co-founder"},
            {"date": "Apr 2024", "milestone": "MVP launched with 5 pilot customers"},
            {"date": "Jul 2024", "milestone": "Reached $50K MRR"},
            {"date": "Oct 2024", "milestone": "Closed $3.5M seed round"},
        ],
        "is_featured": True,
    },
]

# Sample Trends Data
TRENDS_DATA = [
    {"keyword": "AI agents", "category": "AI/ML", "search_volume": 135000, "growth_percentage": 245, "business_implications": "Massive opportunity in autonomous AI workflows. Startups building AI agents for specific verticals (legal, healthcare, finance) are seeing rapid adoption.", "source": "Google Trends", "is_featured": True},
    {"keyword": "vibe coding", "category": "Development", "search_volume": 22000, "growth_percentage": 890, "business_implications": "AI-assisted coding tools like Cursor and Windsurf are transforming how developers work. Tools that enhance the 'vibe coding' experience have high demand.", "source": "Google Trends", "is_featured": True},
    {"keyword": "MCP servers", "category": "AI/ML", "search_volume": 8500, "growth_percentage": 1200, "business_implications": "Model Context Protocol is enabling new AI integrations. Early movers building MCP servers for popular tools have first-mover advantage.", "source": "Google Trends", "is_featured": True},
    {"keyword": "Claude Code", "category": "AI/ML", "search_volume": 45000, "growth_percentage": 560, "business_implications": "Anthropic's CLI tool for developers is driving interest in AI-assisted development. Opportunities in Claude Code extensions and integrations.", "source": "Google Trends", "is_featured": True},
    {"keyword": "no code AI", "category": "No-Code", "search_volume": 74000, "growth_percentage": 125, "business_implications": "Non-technical users want to leverage AI. Platforms that make AI accessible without coding have strong PMF.", "source": "Google Trends", "is_featured": False},
    {"keyword": "agentic workflows", "category": "AI/ML", "search_volume": 28000, "growth_percentage": 380, "business_implications": "Businesses want AI that can take actions, not just generate text. Workflow automation with AI agents is a growing category.", "source": "Google Trends", "is_featured": True},
    {"keyword": "vertical SaaS", "category": "SaaS", "search_volume": 18500, "growth_percentage": 85, "business_implications": "Industry-specific software continues to outperform horizontal solutions. Healthcare, legal, and construction verticals are particularly hot.", "source": "Google Trends", "is_featured": False},
    {"keyword": "AI voice agents", "category": "AI/ML", "search_volume": 56000, "growth_percentage": 210, "business_implications": "Voice AI for customer service and sales is maturing. Startups like Bland and Vapi are showing strong traction.", "source": "Google Trends", "is_featured": True},
    {"keyword": "creator economy tools", "category": "Marketing", "search_volume": 42000, "growth_percentage": 65, "business_implications": "Tools helping creators monetize (newsletters, courses, communities) continue to grow as the creator economy matures.", "source": "Google Trends", "is_featured": False},
    {"keyword": "compliance automation", "category": "Legal", "search_volume": 31000, "growth_percentage": 95, "business_implications": "Regulatory burden is increasing. Startups automating SOC2, GDPR, and industry-specific compliance are seeing enterprise demand.", "source": "Google Trends", "is_featured": False},
    {"keyword": "AI copilots", "category": "AI/ML", "search_volume": 89000, "growth_percentage": 175, "business_implications": "Every software category is adding AI copilots. Opportunities in specialized copilots for niche workflows.", "source": "Google Trends", "is_featured": True},
    {"keyword": "revenue operations", "category": "SaaS", "search_volume": 27000, "growth_percentage": 72, "business_implications": "RevOps tools unifying sales, marketing, and CS data are in demand as companies seek efficiency.", "source": "Google Trends", "is_featured": False},
]

# Sample Market Insights Data
MARKET_INSIGHTS_DATA = [
    {
        "title": "The Rise of AI Agents: Why 2025 Is the Year of Autonomous AI",
        "slug": "rise-of-ai-agents-2025",
        "summary": "AI agents are moving from demos to production. Here's what founders need to know about building in this space.",
        "content": """## The Shift from Chatbots to Agents

For the past two years, AI has been primarily about conversation. ChatGPT, Claude, and their competitors excel at generating text, answering questions, and helping with creative tasks. But 2025 marks a fundamental shift: AI is learning to take action.

AI agents differ from chatbots in one critical way—they can interact with external systems. Instead of just telling you how to book a flight, an AI agent books the flight. Instead of explaining how to analyze data, it connects to your database and runs the queries.

## Why Now?

Several factors have converged to make AI agents viable:

- Model capabilities have improved dramatically—Claude 3 and GPT-4 can follow complex multi-step instructions reliably
- Tool-use protocols like Anthropic's MCP and OpenAI's function calling provide standardized ways for AI to interact with software
- Infrastructure for monitoring, guardrails, and human-in-the-loop oversight has matured

## Opportunities for Founders

The biggest opportunities lie in vertical-specific agents:

- **Legal agents** that can draft contracts, conduct due diligence, and manage compliance workflows
- **Healthcare agents** that handle prior authorizations, patient scheduling, and clinical documentation
- **Finance agents** that automate bookkeeping, expense management, and financial reporting

The key insight is that generic agents struggle with domain-specific knowledge. Startups that deeply understand a vertical can build agents that outperform general-purpose solutions.

## Risks and Challenges

Building AI agents comes with unique challenges:

- **Reliability**: Agents that fail unpredictably are worse than no automation at all
- **Security**: Agents that can take actions need robust permission systems
- **Liability**: When an agent makes a mistake, who's responsible?

Early-stage founders should start with low-stakes use cases where errors are recoverable, then gradually expand scope as reliability improves.

## Conclusion

The AI agent market is nascent but growing explosively. Founders who move now have the opportunity to define categories before they become crowded. The best approach: find a specific workflow in a vertical you understand, build an agent that handles it end-to-end, and iterate based on real user feedback.""",
        "category": "Trends",
        "author_name": "StartInsight Team",
        "reading_time_minutes": 8,
        "is_featured": True,
        "is_published": True,
    },
    {
        "title": "How to Validate Your Startup Idea in 48 Hours",
        "slug": "validate-startup-idea-48-hours",
        "summary": "A practical guide to testing market demand before writing a single line of code.",
        "content": """## The Expensive Mistake Most Founders Make

The graveyard of startups is filled with beautiful products no one wanted. Founders spend months building, only to discover there's no market for their solution. The antidote? Validate before you build.

## The 48-Hour Validation Framework

### Hour 0-8: Define Your Hypothesis

Start by clearly articulating:
- Who is your target customer? (Be specific: "B2B SaaS companies with 10-50 employees" not "businesses")
- What problem are you solving? (The actual pain, not your solution)
- How do they currently solve this problem? (Your competition includes "doing nothing")

### Hour 8-16: Find Your Audience

You need to talk to potential customers. Here's where to find them:
- Reddit communities (r/startups, r/SaaS, industry-specific subreddits)
- LinkedIn groups in your target industry
- Indie Hackers, Hacker News, Product Hunt communities
- Industry Slack/Discord channels

### Hour 16-32: Conduct Customer Discovery

Reach out to 20-30 people. Your goal isn't to pitch—it's to learn. Ask:
- "Tell me about the last time you dealt with [problem]"
- "What have you tried to solve this?"
- "If a magic solution existed, what would it do?"

### Hour 32-48: Synthesize and Decide

Create a simple framework:
- Did at least 5/10 people have the problem you described?
- Are they actively looking for solutions?
- Would they pay for a better alternative?

If yes to all three, you have signal. If not, pivot or move on.

## Tools That Speed Up Validation

- **StartInsight**: AI-powered market research and idea scoring
- **Typeform**: Quick surveys to gather structured feedback
- **Calendly**: Easy scheduling for customer interviews
- **Notion**: Organize your research and insights

## The Hardest Part

Validation often reveals uncomfortable truths. Your idea might not be as good as you thought. That's okay—it's far better to learn this in 48 hours than after 6 months of building.

The founders who succeed aren't the ones with the best ideas. They're the ones who find product-market fit fastest. Validation is your shortcut.""",
        "category": "Guides",
        "author_name": "Marcus Johnson",
        "reading_time_minutes": 6,
        "is_featured": True,
        "is_published": True,
    },
    {
        "title": "2025 SaaS Pricing Trends: What's Working Now",
        "slug": "2025-saas-pricing-trends",
        "summary": "Usage-based, hybrid, and PLG pricing models are reshaping how SaaS companies monetize. Here's what the data shows.",
        "content": """## The Death of Per-Seat Pricing?

For a decade, SaaS pricing was simple: charge per user, per month. But this model is facing challenges as companies optimize headcount and AI handles work previously done by humans.

## Emerging Pricing Models

### Usage-Based Pricing

Companies like Twilio, Snowflake, and AWS pioneered usage-based pricing. Now it's spreading to new categories:
- AI companies charging per API call or token
- Analytics tools charging per event tracked
- Communication platforms charging per message sent

### Hybrid Models

Many successful SaaS companies now combine approaches:
- Base platform fee + usage
- Per-seat pricing with usage-based AI add-ons
- Freemium with usage caps

### Outcome-Based Pricing

The most innovative models charge based on value delivered:
- Marketing tools charging per lead generated
- Sales tools charging per meeting booked
- Support tools charging per ticket resolved

## What the Data Shows

According to OpenView's 2024 SaaS Benchmarks:
- Usage-based companies grew 38% faster than seat-based peers
- Hybrid pricing showed highest net revenue retention (115%+)
- PLG companies achieved 2x better sales efficiency

## Recommendations for Founders

1. Start simple—you can always add complexity later
2. Align pricing with the value you deliver
3. Make it easy to start (freemium or low-cost entry)
4. Build in natural expansion revenue triggers
5. Test pricing early and often

## Conclusion

The best pricing model depends on your product, market, and customers. But the trend is clear: rigid per-seat pricing is giving way to more flexible, value-aligned approaches. Founders who experiment with pricing have a significant advantage.""",
        "category": "Analysis",
        "author_name": "Emily Rodriguez",
        "reading_time_minutes": 7,
        "is_featured": False,
        "is_published": True,
    },
]


async def seed_database():
    """Seed the database with sample public content."""
    # Convert PostgresDsn to string for SQLAlchemy
    engine = create_async_engine(str(settings.database_url), echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Seed Tools
        logger.info("Seeding Tools...")
        for i, tool_data in enumerate(TOOLS_DATA):
            tool = Tool(
                name=tool_data["name"],
                tagline=tool_data["tagline"],
                description=tool_data["description"],
                category=tool_data["category"],
                pricing=tool_data["pricing"],
                website_url=tool_data["website_url"],
                is_featured=tool_data.get("is_featured", False),
                sort_order=i,
            )
            session.add(tool)
        logger.info(f"Added {len(TOOLS_DATA)} tools")

        # Seed Success Stories
        logger.info("Seeding Success Stories...")
        for story_data in SUCCESS_STORIES_DATA:
            story = SuccessStory(
                founder_name=story_data["founder_name"],
                company_name=story_data["company_name"],
                tagline=story_data["tagline"],
                idea_summary=story_data["idea_summary"],
                journey_narrative=story_data["journey_narrative"],
                metrics=story_data["metrics"],
                timeline=story_data["timeline"],
                is_featured=story_data.get("is_featured", False),
                is_published=True,
            )
            session.add(story)
        logger.info(f"Added {len(SUCCESS_STORIES_DATA)} success stories")

        # Seed Trends
        logger.info("Seeding Trends...")
        for trend_data in TRENDS_DATA:
            trend = Trend(
                keyword=trend_data["keyword"],
                category=trend_data["category"],
                search_volume=trend_data["search_volume"],
                growth_percentage=trend_data["growth_percentage"],
                business_implications=trend_data["business_implications"],
                source=trend_data["source"],
                is_featured=trend_data.get("is_featured", False),
                is_published=True,
            )
            session.add(trend)
        logger.info(f"Added {len(TRENDS_DATA)} trends")

        # Seed Market Insights
        logger.info("Seeding Market Insights...")
        for i, insight_data in enumerate(MARKET_INSIGHTS_DATA):
            insight = MarketInsight(
                title=insight_data["title"],
                slug=insight_data["slug"],
                summary=insight_data["summary"],
                content=insight_data["content"],
                category=insight_data["category"],
                author_name=insight_data["author_name"],
                reading_time_minutes=insight_data["reading_time_minutes"],
                is_featured=insight_data.get("is_featured", False),
                is_published=insight_data.get("is_published", True),
                published_at=datetime.utcnow() - timedelta(days=i * 3),
                view_count=random.randint(50, 500),
            )
            session.add(insight)
        logger.info(f"Added {len(MARKET_INSIGHTS_DATA)} market insights")

        await session.commit()
        logger.info("Database seeded successfully!")


if __name__ == "__main__":
    asyncio.run(seed_database())
