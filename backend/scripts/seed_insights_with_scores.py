"""Seed script for Insights with full 8-dimension scoring and trend keywords.

This script creates sample insights with all visualization data populated,
allowing frontend components (ScoreRadar, TrendKeywordCards, CommunitySignalsRadar)
to render properly.

Run with: uv run python scripts/seed_insights_with_scores.py
"""

import asyncio
import logging
from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.insight import Insight
from app.models.raw_signal import RawSignal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sample Insights with Full Scoring Data
INSIGHTS_DATA = [
    {
        "problem_statement": "DevOps teams waste 40% of their time on incident response due to fragmented monitoring tools",
        "proposed_solution": "Unified API monitoring platform with AI-powered root cause analysis that correlates logs, metrics, and traces automatically",
        "market_size_estimate": "Large",
        "relevance_score": 0.92,
        "title": "AI-Powered API Monitoring Platform",
        "opportunity_score": 9,
        "problem_score": 8,
        "feasibility_score": 7,
        "why_now_score": 9,
        "go_to_market_score": 7,
        "founder_fit_score": 6,
        "execution_difficulty": 6,
        "revenue_potential": "$$$",
        "value_ladder": {
            "lead_magnet": {"name": "Free API Health Check", "price": "$0", "value": "5-minute API audit"},
            "frontend": {"name": "Starter", "price": "$29/mo", "value": "10 endpoints, basic alerts"},
            "core": {"name": "Pro", "price": "$99/mo", "value": "100 endpoints, AI analysis"},
            "backend": {"name": "Enterprise", "price": "$499/mo", "value": "Unlimited, dedicated support"}
        },
        "market_gap_analysis": "Current monitoring tools like Datadog and New Relic are expensive and complex for SMBs. They require significant setup time and expertise. Our AI-first approach automates root cause analysis, reducing MTTR by 70%. The gap is in affordable, intelligent monitoring for growing SaaS companies.",
        "why_now_analysis": "The shift to microservices has exploded the number of APIs that need monitoring. AI capabilities have matured enough to automate root cause analysis. Remote work has made observability more critical than ever. Companies are looking for cost-effective alternatives to expensive enterprise tools.",
        "proof_signals": [
            {"type": "Reddit Traction", "evidence": "r/devops thread with 2,400 upvotes discussing monitoring fatigue"},
            {"type": "Google Trends", "evidence": "API monitoring searches up 145% YoY"},
            {"type": "Competitor Funding", "evidence": "Checkly raised $13M, indicating market validation"}
        ],
        "execution_plan": [
            {"step": 1, "action": "Build lightweight agent SDK for Node.js and Python"},
            {"step": 2, "action": "Integrate Claude API for root cause analysis"},
            {"step": 3, "action": "Launch on Product Hunt with free tier"},
            {"step": 4, "action": "Partner with DevOps influencers for distribution"},
            {"step": 5, "action": "Add Slack/PagerDuty integrations for alerts"}
        ],
        "community_signals_chart": [
            {"platform": "Reddit", "score": 8, "members": 2400000, "engagement_rate": 0.05, "top_url": "https://reddit.com/r/devops"},
            {"platform": "YouTube", "score": 7, "members": 150000, "engagement_rate": 0.03, "top_url": None},
            {"platform": "Facebook", "score": 5, "members": 45000, "engagement_rate": 0.02, "top_url": None}
        ],
        "trend_keywords": [
            {"keyword": "API monitoring", "volume": "27.1K", "growth": "+145%"},
            {"keyword": "observability platform", "volume": "18.5K", "growth": "+89%"},
            {"keyword": "incident response automation", "volume": "12.3K", "growth": "+210%"},
            {"keyword": "root cause analysis AI", "volume": "8.7K", "growth": "+340%"}
        ],
        "competitor_analysis": [
            {"name": "Datadog", "description": "Enterprise monitoring platform with comprehensive features but high cost", "url": "https://datadoghq.com", "market_position": "Leader"},
            {"name": "New Relic", "description": "Full-stack observability with usage-based pricing", "url": "https://newrelic.com", "market_position": "Leader"},
            {"name": "Checkly", "description": "API monitoring focused on synthetic checks and Playwright", "url": "https://checklyhq.com", "market_position": "Challenger"}
        ],
        "signal_source": "Reddit",
        "signal_url": "https://reddit.com/r/devops/comments/example1",
        "signal_content": "We're drowning in alerts from 15 different monitoring tools. Anyone found a solution that actually correlates issues automatically?"
    },
    {
        "problem_statement": "Content creators spend 6+ hours per week manually scheduling and optimizing posts across multiple platforms",
        "proposed_solution": "AI content scheduler that automatically optimizes posting times, generates variations, and cross-posts to all major platforms",
        "market_size_estimate": "Large",
        "relevance_score": 0.88,
        "title": "AI-Powered Content Scheduling Platform",
        "opportunity_score": 8,
        "problem_score": 7,
        "feasibility_score": 8,
        "why_now_score": 8,
        "go_to_market_score": 8,
        "founder_fit_score": 7,
        "execution_difficulty": 5,
        "revenue_potential": "$$",
        "value_ladder": {
            "lead_magnet": {"name": "Free Content Calendar", "price": "$0", "value": "7-day content plan template"},
            "frontend": {"name": "Creator", "price": "$15/mo", "value": "3 platforms, 30 posts/mo"},
            "core": {"name": "Pro Creator", "price": "$39/mo", "value": "Unlimited platforms, AI variations"},
            "backend": {"name": "Agency", "price": "$149/mo", "value": "10 brands, team features"}
        },
        "market_gap_analysis": "Buffer and Hootsuite are aging platforms without AI capabilities. Later is Instagram-focused. There's no modern tool that uses AI to optimize content across all platforms while generating variations automatically.",
        "why_now_analysis": "Creator economy has exploded to 50M+ creators. AI can now generate high-quality content variations. Platform APIs have matured for reliable scheduling. Creators are looking for tools that save time without sacrificing authenticity.",
        "proof_signals": [
            {"type": "Market Size", "evidence": "Creator economy tools market projected at $15B by 2028"},
            {"type": "User Pain", "evidence": "80% of creators cite content scheduling as top time sink"},
            {"type": "Platform Growth", "evidence": "TikTok and Threads added scheduling APIs in 2024"}
        ],
        "execution_plan": [
            {"step": 1, "action": "Build core scheduling engine for Instagram, TikTok, Twitter"},
            {"step": 2, "action": "Add AI content variation generator using Claude"},
            {"step": 3, "action": "Launch with creator influencer partnerships"},
            {"step": 4, "action": "Add analytics and optimal time recommendations"},
            {"step": 5, "action": "Expand to YouTube Shorts and LinkedIn"}
        ],
        "community_signals_chart": [
            {"platform": "YouTube", "score": 9, "members": 3500000, "engagement_rate": 0.06, "top_url": "https://youtube.com/creator-economy"},
            {"platform": "Reddit", "score": 7, "members": 890000, "engagement_rate": 0.04, "top_url": "https://reddit.com/r/content_marketing"},
            {"platform": "Facebook", "score": 6, "members": 120000, "engagement_rate": 0.03, "top_url": None}
        ],
        "trend_keywords": [
            {"keyword": "content scheduling tool", "volume": "45.2K", "growth": "+78%"},
            {"keyword": "AI social media manager", "volume": "22.8K", "growth": "+245%"},
            {"keyword": "creator tools", "volume": "89.4K", "growth": "+56%"},
            {"keyword": "cross-platform posting", "volume": "15.6K", "growth": "+112%"}
        ],
        "competitor_analysis": [
            {"name": "Buffer", "description": "Simple social media scheduling tool, lacks AI features", "url": "https://buffer.com", "market_position": "Legacy"},
            {"name": "Hootsuite", "description": "Enterprise social management, expensive for creators", "url": "https://hootsuite.com", "market_position": "Enterprise"},
            {"name": "Later", "description": "Instagram-first visual planner, limited platform support", "url": "https://later.com", "market_position": "Niche"}
        ],
        "signal_source": "Twitter",
        "signal_url": "https://twitter.com/example/status/1234567890",
        "signal_content": "I spend every Sunday scheduling content for the week. There has to be a better way that doesn't cost $200/month like Hootsuite."
    },
    {
        "problem_statement": "Small e-commerce brands lose 30% of potential revenue due to poor product recommendations",
        "proposed_solution": "AI-powered personalization engine that integrates with any e-commerce platform in minutes and delivers Amazon-quality recommendations",
        "market_size_estimate": "Large",
        "relevance_score": 0.85,
        "title": "E-commerce Personalization AI",
        "opportunity_score": 8,
        "problem_score": 8,
        "feasibility_score": 7,
        "why_now_score": 7,
        "go_to_market_score": 6,
        "founder_fit_score": 5,
        "execution_difficulty": 7,
        "revenue_potential": "$$$",
        "value_ladder": {
            "lead_magnet": {"name": "Free Recommendation Audit", "price": "$0", "value": "Analysis of current recommendation performance"},
            "frontend": {"name": "Starter", "price": "$49/mo", "value": "5K visitors, basic recommendations"},
            "core": {"name": "Growth", "price": "$149/mo", "value": "50K visitors, AI personalization"},
            "backend": {"name": "Scale", "price": "$499/mo", "value": "Unlimited, A/B testing, analytics"}
        },
        "market_gap_analysis": "Enterprise solutions like Dynamic Yield and Nosto cost $50K+/year. Small Shopify stores have no affordable option. Our approach uses pre-trained models that work out of the box with minimal data requirements.",
        "why_now_analysis": "E-commerce competition is fierce—brands need every edge. AI models have become affordable to run. Shopify's app ecosystem makes distribution easy. Third-party cookies are dying, making first-party personalization critical.",
        "proof_signals": [
            {"type": "Revenue Impact", "evidence": "Personalized recommendations drive 35% of Amazon's revenue"},
            {"type": "Market Gap", "evidence": "95% of Shopify stores have no personalization beyond Shopify's basic features"},
            {"type": "Competitor Success", "evidence": "Rebuy grew to $10M ARR serving this segment"}
        ],
        "execution_plan": [
            {"step": 1, "action": "Build Shopify app with one-click install"},
            {"step": 2, "action": "Train recommendation model on aggregate e-commerce data"},
            {"step": 3, "action": "Launch with revenue-share pilot program"},
            {"step": 4, "action": "Add WooCommerce and BigCommerce integrations"},
            {"step": 5, "action": "Build self-serve analytics dashboard"}
        ],
        "community_signals_chart": [
            {"platform": "Reddit", "score": 7, "members": 450000, "engagement_rate": 0.04, "top_url": "https://reddit.com/r/shopify"},
            {"platform": "Facebook", "score": 8, "members": 280000, "engagement_rate": 0.05, "top_url": None},
            {"platform": "YouTube", "score": 6, "members": 95000, "engagement_rate": 0.03, "top_url": None}
        ],
        "trend_keywords": [
            {"keyword": "AI product recommendations", "volume": "18.9K", "growth": "+167%"},
            {"keyword": "e-commerce personalization", "volume": "24.5K", "growth": "+98%"},
            {"keyword": "Shopify app recommendations", "volume": "31.2K", "growth": "+45%"},
            {"keyword": "conversion optimization AI", "volume": "12.1K", "growth": "+189%"}
        ],
        "competitor_analysis": [
            {"name": "Dynamic Yield", "description": "Enterprise personalization platform, $50K+ minimum", "url": "https://dynamicyield.com", "market_position": "Enterprise"},
            {"name": "Nosto", "description": "E-commerce personalization for mid-market", "url": "https://nosto.com", "market_position": "Mid-Market"},
            {"name": "Rebuy", "description": "Shopify-focused personalization, growing competitor", "url": "https://rebuyengine.com", "market_position": "Challenger"}
        ],
        "signal_source": "Reddit",
        "signal_url": "https://reddit.com/r/shopify/comments/example3",
        "signal_content": "My conversion rate is stuck at 2%. Amazon shows such relevant products but I can't afford the enterprise personalization tools."
    },
    {
        "problem_statement": "Remote teams struggle with asynchronous communication leading to 50% more meetings than necessary",
        "proposed_solution": "AI-powered async video communication platform that summarizes, transcribes, and creates action items from video messages",
        "market_size_estimate": "Medium",
        "relevance_score": 0.82,
        "title": "AI Async Video Platform",
        "opportunity_score": 7,
        "problem_score": 7,
        "feasibility_score": 8,
        "why_now_score": 8,
        "go_to_market_score": 7,
        "founder_fit_score": 6,
        "execution_difficulty": 5,
        "revenue_potential": "$$",
        "value_ladder": {
            "lead_magnet": {"name": "Free Loom Alternative", "price": "$0", "value": "25 videos/month with basic features"},
            "frontend": {"name": "Personal", "price": "$12/mo", "value": "Unlimited videos, AI summaries"},
            "core": {"name": "Team", "price": "$8/user/mo", "value": "Team workspace, integrations"},
            "backend": {"name": "Business", "price": "$15/user/mo", "value": "SSO, analytics, priority support"}
        },
        "market_gap_analysis": "Loom dominates async video but lacks AI capabilities. Competitors like Vidyard focus on sales. There's no async video tool optimized for team collaboration with AI-powered features like automatic action item extraction.",
        "why_now_analysis": "Remote work is permanent for many companies. AI transcription and summarization costs have dropped 90%. Meeting fatigue is at an all-time high. Teams need async tools that respect time zones.",
        "proof_signals": [
            {"type": "Loom Success", "evidence": "Loom acquired for $975M, validating async video market"},
            {"type": "Meeting Fatigue", "evidence": "85% of workers report video call fatigue (Zoom fatigue)"},
            {"type": "Remote Trend", "evidence": "65% of companies now have permanent remote policies"}
        ],
        "execution_plan": [
            {"step": 1, "action": "Build Chrome extension for easy recording"},
            {"step": 2, "action": "Integrate Whisper API for transcription"},
            {"step": 3, "action": "Add Claude for summaries and action items"},
            {"step": 4, "action": "Build Slack and Notion integrations"},
            {"step": 5, "action": "Launch B2B motion with team free trials"}
        ],
        "community_signals_chart": [
            {"platform": "Reddit", "score": 8, "members": 1200000, "engagement_rate": 0.05, "top_url": "https://reddit.com/r/remotework"},
            {"platform": "YouTube", "score": 6, "members": 75000, "engagement_rate": 0.02, "top_url": None},
            {"platform": "Other", "score": 7, "members": 350000, "engagement_rate": 0.04, "top_url": "https://linkedin.com/groups/remotework"}
        ],
        "trend_keywords": [
            {"keyword": "async video communication", "volume": "8.9K", "growth": "+234%"},
            {"keyword": "Loom alternative", "volume": "14.5K", "growth": "+156%"},
            {"keyword": "meeting reduction tools", "volume": "6.2K", "growth": "+312%"},
            {"keyword": "AI meeting notes", "volume": "22.8K", "growth": "+189%"}
        ],
        "competitor_analysis": [
            {"name": "Loom", "description": "Market leader in async video, acquired by Atlassian", "url": "https://loom.com", "market_position": "Leader"},
            {"name": "Vidyard", "description": "Video platform focused on sales and marketing", "url": "https://vidyard.com", "market_position": "Sales"},
            {"name": "Tella", "description": "Screen recording for product demos", "url": "https://tella.tv", "market_position": "Niche"}
        ],
        "signal_source": "Hacker News",
        "signal_url": "https://news.ycombinator.com/item?id=12345678",
        "signal_content": "I love Loom but wish it had AI features. Transcribing and summarizing my videos manually defeats the purpose of async."
    },
    {
        "problem_statement": "Indie hackers and solo founders waste months building MVPs that don't match market needs",
        "proposed_solution": "AI-powered idea validation and MVP planning platform that scores ideas, identifies market gaps, and generates actionable launch plans",
        "market_size_estimate": "Medium",
        "relevance_score": 0.95,
        "title": "AI Startup Idea Validator",
        "opportunity_score": 9,
        "problem_score": 9,
        "feasibility_score": 9,
        "why_now_score": 9,
        "go_to_market_score": 8,
        "founder_fit_score": 9,
        "execution_difficulty": 4,
        "revenue_potential": "$$",
        "value_ladder": {
            "lead_magnet": {"name": "Free Idea Score", "price": "$0", "value": "Basic 8-dimension scoring"},
            "frontend": {"name": "Founder", "price": "$29/mo", "value": "5 idea analyses, competitor research"},
            "core": {"name": "Pro", "price": "$79/mo", "value": "Unlimited analyses, AI research agent"},
            "backend": {"name": "Studio", "price": "$199/mo", "value": "Team access, API, white-label"}
        },
        "market_gap_analysis": "Existing tools like Exploding Topics focus only on trend data. IdeaBrowser has good ideas but limited analysis. No platform combines AI-powered scoring, competitive analysis, and actionable launch planning in one place.",
        "why_now_analysis": "AI tools have made starting a business easier than ever—but choosing the right idea is harder. Claude and GPT-4 can now do sophisticated market analysis. The indie hacker community is larger than ever and actively seeking validation tools.",
        "proof_signals": [
            {"type": "Community Size", "evidence": "Indie Hackers has 100K+ active members seeking ideas"},
            {"type": "Competitor Traction", "evidence": "IdeaBrowser and Exploding Topics have proven demand"},
            {"type": "AI Capability", "evidence": "LLMs can now perform research-grade market analysis"}
        ],
        "execution_plan": [
            {"step": 1, "action": "Build core scoring engine with 8-dimension analysis"},
            {"step": 2, "action": "Integrate with Reddit, Google Trends, Crunchbase APIs"},
            {"step": 3, "action": "Add AI research agent for deep-dive analysis"},
            {"step": 4, "action": "Launch on Product Hunt and Indie Hackers"},
            {"step": 5, "action": "Build integrations with Lovable, Bolt, and Cursor"}
        ],
        "community_signals_chart": [
            {"platform": "Reddit", "score": 9, "members": 2100000, "engagement_rate": 0.06, "top_url": "https://reddit.com/r/SideProject"},
            {"platform": "Other", "score": 8, "members": 100000, "engagement_rate": 0.08, "top_url": "https://indiehackers.com"},
            {"platform": "YouTube", "score": 7, "members": 450000, "engagement_rate": 0.04, "top_url": None}
        ],
        "trend_keywords": [
            {"keyword": "startup idea validation", "volume": "12.4K", "growth": "+145%"},
            {"keyword": "AI market research", "volume": "28.7K", "growth": "+267%"},
            {"keyword": "indie hacker tools", "volume": "9.8K", "growth": "+189%"},
            {"keyword": "MVP planning", "volume": "15.3K", "growth": "+78%"},
            {"keyword": "competitor analysis tool", "volume": "22.1K", "growth": "+92%"}
        ],
        "competitor_analysis": [
            {"name": "IdeaBrowser", "description": "Curated startup ideas with basic analysis", "url": "https://ideabrowser.com", "market_position": "Competitor"},
            {"name": "Exploding Topics", "description": "Trend discovery platform for marketers", "url": "https://explodingtopics.com", "market_position": "Adjacent"},
            {"name": "Gummy Search", "description": "Reddit audience research tool", "url": "https://gummysearch.com", "market_position": "Niche"}
        ],
        "signal_source": "Indie Hackers",
        "signal_url": "https://indiehackers.com/post/example5",
        "signal_content": "I've built 3 failed products because I didn't validate properly. Anyone know a tool that can help me score ideas before I waste months building?"
    }
]


async def seed_database():
    """Seed the database with sample insights that have full scoring data."""
    engine = create_async_engine(str(settings.database_url), echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        logger.info("Seeding Insights with full scoring data...")

        for i, data in enumerate(INSIGHTS_DATA):
            # First create the raw signal
            raw_signal = RawSignal(
                id=uuid4(),
                source=data["signal_source"],
                url=data["signal_url"],
                content=data["signal_content"],
                extra_metadata={
                    "community_signals": data["community_signals_chart"],
                    "trend_keywords": data["trend_keywords"]
                },
                created_at=datetime.utcnow() - timedelta(days=i * 2)
            )
            session.add(raw_signal)
            await session.flush()  # Get the raw_signal.id

            # Then create the insight with full data
            insight = Insight(
                id=uuid4(),
                raw_signal_id=raw_signal.id,
                problem_statement=data["problem_statement"],
                proposed_solution=data["proposed_solution"],
                market_size_estimate=data["market_size_estimate"],
                relevance_score=data["relevance_score"],
                title=data["title"],
                # 8-dimension scores
                opportunity_score=data["opportunity_score"],
                problem_score=data["problem_score"],
                feasibility_score=data["feasibility_score"],
                why_now_score=data["why_now_score"],
                go_to_market_score=data["go_to_market_score"],
                founder_fit_score=data["founder_fit_score"],
                execution_difficulty=data["execution_difficulty"],
                revenue_potential=data["revenue_potential"],
                # Advanced frameworks
                value_ladder=data["value_ladder"],
                market_gap_analysis=data["market_gap_analysis"],
                why_now_analysis=data["why_now_analysis"],
                proof_signals=data["proof_signals"],
                execution_plan=data["execution_plan"],
                # Visualization data
                community_signals_chart=data["community_signals_chart"],
                trend_keywords=data["trend_keywords"],
                competitor_analysis=data["competitor_analysis"],
                created_at=datetime.utcnow() - timedelta(days=i * 2)
            )
            session.add(insight)
            logger.info(f"Added insight: {data['title']}")

        await session.commit()
        logger.info(f"Successfully seeded {len(INSIGHTS_DATA)} insights with full scoring data!")


async def check_existing_insights():
    """Check if insights already exist with scoring data."""
    engine = create_async_engine(str(settings.database_url), echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        result = await session.execute(
            select(Insight).where(Insight.opportunity_score.isnot(None)).limit(5)
        )
        insights = result.scalars().all()

        if insights:
            logger.info(f"Found {len(insights)} insights with scoring data:")
            for insight in insights:
                logger.info(f"  - {insight.title}: Opp={insight.opportunity_score}, Prob={insight.problem_score}")
            return True
        else:
            logger.info("No insights with scoring data found.")
            return False


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--check":
        asyncio.run(check_existing_insights())
    else:
        asyncio.run(seed_database())
