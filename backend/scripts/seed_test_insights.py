#!/usr/bin/env python3
"""
Seed test insights directly into the database for testing.

This script creates realistic startup opportunity insights without
needing external APIs, useful for development and testing.
"""

import asyncio
import random
import sys
import uuid
from datetime import datetime, timedelta

sys.path.insert(0, "/home/wysetime-pcc/Nero/StartInsight/backend")

from sqlalchemy import text

from app.db.session import AsyncSessionLocal
from app.models.insight import Insight
from app.models.raw_signal import RawSignal

# Sample startup opportunities data
STARTUP_IDEAS = [
    {
        "title": "AI-Powered Code Review Platform",
        "problem_statement": """Software development teams struggle with maintaining code quality as projects scale. Manual code reviews are time-consuming, inconsistent, and often miss subtle issues that lead to technical debt. According to recent industry surveys, developers spend an average of 4-6 hours per week on code reviews, yet 60% of bugs still make it to production.

The current solutions like GitHub's built-in review tools and basic linting provide only surface-level analysis. They fail to catch architectural issues, security vulnerabilities in context, or suggest meaningful improvements based on the specific codebase patterns.

Teams need intelligent code review assistants that understand their codebase, enforce custom standards, and provide actionable suggestions that reduce review time while improving code quality. This is particularly acute for small teams without dedicated QA resources and enterprises dealing with legacy code modernization.""",
        "proposed_solution": "An AI-powered code review platform that learns from your codebase patterns, integrates with existing CI/CD pipelines, and provides context-aware suggestions including security analysis, performance optimization, and best practice enforcement.",
        "relevance_score": 0.92,
        "opportunity_score": 9,
        "problem_score": 8,
        "feasibility_score": 7,
        "why_now_score": 9,
        "market_size_estimate": "$4.2B",
    },
    {
        "title": "No-Code API Integration Platform for SMBs",
        "problem_statement": """Small and medium businesses are increasingly reliant on multiple SaaS tools (CRM, accounting, marketing, operations), but these tools often don't communicate with each other. According to recent research, the average SMB uses 40+ different software applications, yet only 28% have any meaningful integration between them.

Existing solutions like Zapier and Make are powerful but require technical understanding that many small business owners lack. They also become expensive as automation needs scale, with costs quickly reaching hundreds of dollars monthly for basic integrations.

This creates a significant operational burden where employees manually transfer data between systems, leading to errors, delays, and lost productivity. Small businesses need accessible integration solutions that work without coding knowledge and scale affordably with their growth.""",
        "proposed_solution": "A visual integration platform designed specifically for non-technical SMB owners, featuring pre-built templates for common business workflows, plain-language automation rules, and transparent pricing that scales with business size rather than API call volume.",
        "relevance_score": 0.88,
        "opportunity_score": 8,
        "problem_score": 9,
        "feasibility_score": 8,
        "why_now_score": 8,
        "market_size_estimate": "$3.8B",
    },
    {
        "title": "AI Meeting Assistant for Remote Teams",
        "problem_statement": """Remote and hybrid work has fundamentally changed how teams collaborate, with video meetings becoming the default communication medium. Research shows knowledge workers now spend an average of 31 hours per week in meetings, up from 23 hours pre-pandemic. Yet 71% of meetings are considered unproductive.

Current tools like Otter.ai and Fireflies provide basic transcription, but they fail to capture action items reliably, don't integrate well with project management systems, and require manual review to extract value. The cognitive load of attending meetings, taking notes, and following up is overwhelming distributed teams.

Teams need intelligent meeting assistants that not only capture what was said but understand context, identify decisions and commitments, and automatically create the downstream artifacts that move work forward.""",
        "proposed_solution": "An AI-native meeting platform that uses advanced language models to understand meeting context, automatically generate structured summaries, identify action items with assignees and deadlines, and push these directly to the team's project management and communication tools.",
        "relevance_score": 0.91,
        "opportunity_score": 8,
        "problem_score": 8,
        "feasibility_score": 8,
        "why_now_score": 9,
        "market_size_estimate": "$6.1B",
    },
    {
        "title": "Personalized Developer Learning Platform",
        "problem_statement": """The technology landscape evolves rapidly, requiring developers to continuously learn new frameworks, languages, and tools. However, current learning platforms take a one-size-fits-all approach that doesn't account for individual knowledge gaps, learning styles, or career goals.

Traditional courses like those on Coursera or Udemy provide generic content that may include topics the developer already knows while missing critical gaps. Coding challenges on platforms like LeetCode focus on algorithms without teaching practical, job-relevant skills. The average developer spends 5-10 hours weekly on learning, but only 23% feel their learning is effective.

Developers need adaptive learning experiences that assess their current skills, identify gaps relevant to their career goals, and provide personalized paths that maximize learning efficiency while maintaining engagement.""",
        "proposed_solution": "An AI-driven learning platform that assesses developer skills through code analysis and brief assessments, maps career goals to required competencies, and generates personalized learning paths with project-based challenges calibrated to their skill level.",
        "relevance_score": 0.85,
        "opportunity_score": 8,
        "problem_score": 7,
        "feasibility_score": 7,
        "why_now_score": 8,
        "market_size_estimate": "$2.9B",
    },
    {
        "title": "AI-Powered Customer Support Automation",
        "problem_statement": """Customer support costs are spiraling for growing businesses, with average cost per support interaction reaching $8-12 for voice and $3-5 for chat. Yet customer expectations for instant, 24/7 support continue to rise. According to industry data, 82% of customers expect immediate responses to their inquiries, but only 28% of businesses can consistently meet this expectation.

Current chatbot solutions often frustrate users with their inability to understand context, handle complex issues, or seamlessly escalate to human agents. They typically require extensive manual configuration of response flows and fail to learn from interactions.

Businesses need intelligent support automation that can handle the majority of routine inquiries accurately while knowing when and how to involve human agents, all while continuously improving from every interaction.""",
        "proposed_solution": "An AI customer support platform using advanced language models trained on your support history and product documentation, capable of handling 70%+ of inquiries autonomously while seamlessly escalating complex cases to human agents with full context.",
        "relevance_score": 0.89,
        "opportunity_score": 9,
        "problem_score": 8,
        "feasibility_score": 8,
        "why_now_score": 9,
        "market_size_estimate": "$11.2B",
    },
    {
        "title": "Automated Financial Close Platform for SMBs",
        "problem_statement": """Month-end financial close is a painful process for small and medium businesses, typically taking 5-10 business days of manual work involving data gathering, reconciliation, and report generation. This delay means business decisions are made with outdated financial information, and finance teams are trapped in repetitive manual work.

While enterprise solutions like BlackLine exist for large companies, they're priced out of reach for SMBs (typically $50K+ annually) and overly complex for simpler business structures. Small businesses are stuck with spreadsheets or basic accounting software that requires extensive manual intervention.

SMBs need accessible automated close solutions that reduce their monthly close from days to hours, providing timely financial insights without enterprise-level complexity or cost.""",
        "proposed_solution": "An automated financial close platform designed for SMBs, integrating with popular accounting and banking systems to automatically reconcile accounts, generate reports, and identify anomalies, reducing close time by 80% at a fraction of enterprise solution costs.",
        "relevance_score": 0.87,
        "opportunity_score": 8,
        "problem_score": 8,
        "feasibility_score": 7,
        "why_now_score": 7,
        "market_size_estimate": "$1.8B",
    },
    {
        "title": "AI Content Repurposing Engine",
        "problem_statement": """Content marketers are expected to maintain presence across multiple platforms (blog, social media, newsletters, video) but creating unique content for each channel is time-prohibitive. Studies show marketers spend 26+ hours weekly on content creation, yet only 38% feel their content strategy is effective.

Current tools offer basic reformatting but don't truly adapt content to the unique requirements and audience expectations of each platform. A blog post manually converted to tweets loses the nuance and engagement that platform-native content provides.

Content teams need intelligent repurposing that understands the original content's key messages and automatically generates platform-optimized variations that maintain brand voice while maximizing engagement on each channel.""",
        "proposed_solution": "An AI content engine that ingests long-form content and automatically generates optimized versions for each target platform, including social posts, email snippets, video scripts, and more, while maintaining consistent messaging and brand voice.",
        "relevance_score": 0.86,
        "opportunity_score": 8,
        "problem_score": 7,
        "feasibility_score": 8,
        "why_now_score": 9,
        "market_size_estimate": "$5.4B",
    },
    {
        "title": "Predictive Equipment Maintenance for Manufacturing SMBs",
        "problem_statement": """Unplanned equipment downtime costs manufacturers an average of $260,000 per hour, yet most small and medium manufacturers still rely on reactive or simple time-based maintenance approaches. Only 12% of SMB manufacturers have implemented any form of predictive maintenance, primarily due to the high cost and complexity of existing solutions.

Enterprise IoT platforms require significant upfront investment in sensors, infrastructure, and expertise that puts them out of reach for smaller operations. These businesses continue to experience costly breakdowns and inefficient maintenance schedules that eat into already tight margins.

SMB manufacturers need accessible predictive maintenance solutions that work with existing equipment, require minimal technical expertise to deploy, and provide clear ROI through reduced downtime and optimized maintenance scheduling.""",
        "proposed_solution": "A plug-and-play predictive maintenance platform using affordable retrofit sensors and AI analysis to predict equipment failures before they occur, designed specifically for SMB manufacturers with simple deployment and clear cost-saving metrics.",
        "relevance_score": 0.83,
        "opportunity_score": 8,
        "problem_score": 9,
        "feasibility_score": 6,
        "why_now_score": 7,
        "market_size_estimate": "$12.3B",
    },
    {
        "title": "AI Legal Document Analysis for Startups",
        "problem_statement": """Startups face numerous legal documents throughout their lifecycle - term sheets, contracts, compliance requirements - yet most don't have the budget for continuous legal counsel. Founders often sign agreements without fully understanding the implications, leading to costly problems down the road. Research shows 67% of startup founders have signed contracts they later regretted.

Current solutions are either expensive legal services ($300-500/hour), basic template services that don't provide meaningful analysis, or generic AI tools that lack legal domain expertise. The gap between needing legal insight and being able to afford it creates significant risk for early-stage companies.

Startups need accessible legal document analysis that explains complex terms in plain language, highlights unusual or unfavorable clauses, and compares agreements against market standards, all at a price point appropriate for early-stage companies.""",
        "proposed_solution": "An AI-powered legal analysis platform trained on startup contracts that explains document terms in plain language, flags unusual clauses, benchmarks against market standards, and provides actionable recommendations, all at startup-friendly pricing.",
        "relevance_score": 0.84,
        "opportunity_score": 7,
        "problem_score": 8,
        "feasibility_score": 7,
        "why_now_score": 8,
        "market_size_estimate": "$3.2B",
    },
    {
        "title": "Real-Time Inventory Optimization for E-commerce",
        "problem_statement": """E-commerce businesses face constant tension between having enough inventory to meet demand and tying up capital in excess stock. Poor inventory management costs retailers $1.1 trillion annually in overstocks, stockouts, and markdowns. Yet most SMB e-commerce sellers rely on spreadsheets or basic inventory tools that can't handle the complexity of multi-channel selling.

Existing inventory management solutions either focus on basic tracking without predictive capabilities or are enterprise platforms designed for large retailers with complex requirements and high price tags. The growing trend of selling across multiple marketplaces (Amazon, Shopify, eBay) further complicates inventory planning.

E-commerce sellers need intelligent inventory systems that predict demand across channels, optimize stock levels to minimize both stockouts and carrying costs, and automatically reorder at the right time.""",
        "proposed_solution": "An AI-driven inventory platform for e-commerce that integrates with major selling channels, predicts demand using sales history and market signals, optimizes stock levels across warehouses, and automates purchase order recommendations.",
        "relevance_score": 0.90,
        "opportunity_score": 8,
        "problem_score": 8,
        "feasibility_score": 8,
        "why_now_score": 8,
        "market_size_estimate": "$7.8B",
    },
]


async def seed_insights():
    """Seed test insights into the database."""
    print("=" * 60)
    print("Seeding Test Insights")
    print("=" * 60)

    async with AsyncSessionLocal() as session:
        insights_created = 0

        for i, idea in enumerate(STARTUP_IDEAS):
            try:
                # First create a raw signal as the source
                signal = RawSignal(
                    source="seed_data",
                    url=f"https://startinsight.app/seed/{uuid.uuid4()}",
                    content=f"# {idea['title']}\n\n{idea['problem_statement'][:500]}...",
                    content_hash=f"seed_{uuid.uuid4().hex[:32]}",
                    extra_metadata={
                        "seed": True,
                        "title": idea["title"],
                        "seeded_at": datetime.utcnow().isoformat(),
                    },
                    processed=True,
                )
                session.add(signal)
                await session.flush()

                # Create the insight
                insight = Insight(
                    raw_signal_id=signal.id,
                    title=idea["title"],
                    problem_statement=idea["problem_statement"],
                    proposed_solution=idea["proposed_solution"],
                    relevance_score=idea["relevance_score"],
                    opportunity_score=idea["opportunity_score"],
                    problem_score=idea["problem_score"],
                    feasibility_score=idea["feasibility_score"],
                    why_now_score=idea["why_now_score"],
                    market_size_estimate=idea["market_size_estimate"],
                    # Additional scores for enhanced model
                    revenue_potential=random.choice(["$$$", "$$$$"]),  # String: $, $$, $$$, $$$$
                    execution_difficulty=random.randint(5, 8),
                    go_to_market_score=random.randint(6, 9),
                    founder_fit_score=random.randint(7, 9),
                    # Extra metadata - must match Pydantic schema
                    competitor_analysis=[
                        {"name": "Competitor A", "url": "https://example.com/a", "description": "Established player", "market_position": "Large"},
                        {"name": "Competitor B", "url": "https://example.com/b", "description": "Growing challenger", "market_position": "Medium"},
                    ],
                    value_ladder={
                        "tiers": [
                            {"name": "Free", "price": "$0", "features": ["Basic features"]},
                            {"name": "Pro", "price": "$49/mo", "features": ["Advanced features"]},
                            {"name": "Enterprise", "price": "Custom", "features": ["Full platform"]},
                        ]
                    },
                    enhanced_scores=[
                        {"dimension": "market_timing", "value": random.randint(7, 9), "label": "Strong"},
                        {"dimension": "competition_level", "value": random.randint(4, 6), "label": "Moderate"},
                        {"dimension": "technical_feasibility", "value": random.randint(7, 9), "label": "Excellent"},
                    ],
                    trend_keywords=[
                        {"keyword": idea["title"].split()[0], "volume": f"{random.randint(10, 100)}.{random.randint(0, 9)}K", "growth": f"+{random.randint(15, 45)}%"},
                        {"keyword": idea["title"].split()[-1], "volume": f"{random.randint(5, 50)}.{random.randint(0, 9)}K", "growth": f"+{random.randint(10, 30)}%"},
                    ],
                    created_at=datetime.utcnow() - timedelta(days=random.randint(0, 6)),
                )
                session.add(insight)
                insights_created += 1
                print(f"  ✓ Created insight: {idea['title']}")

            except Exception as e:
                print(f"  ✗ Failed to create insight: {e}")

        await session.commit()

    print("=" * 60)
    print(f"Seeding complete: {insights_created} insights created")
    print("=" * 60)

    return insights_created


if __name__ == "__main__":
    asyncio.run(seed_insights())
