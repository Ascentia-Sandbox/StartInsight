"""Success Stories Agent - Auto-generates founder case studies every 7 days.

This agent:
1. Checks if it's enabled via AgentConfiguration
2. Queries top-performing insights from the last 7 days
3. Generates realistic success story narratives from insight data
4. Creates new SuccessStory entries with metrics and timelines
5. Logs execution to AgentExecutionLog for admin monitoring

Schedule: Every 7 days (Sundays at 05:00 UTC)
"""

import logging
import random
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.models.agent_control import AgentConfiguration
from app.models.agent_execution_log import AgentExecutionLog
from app.models.insight import Insight
from app.models.success_story import SuccessStory

logger = logging.getLogger(__name__)

AGENT_NAME = "success_stories_agent"

# Templates for generating realistic story narratives
JOURNEY_TEMPLATES = [
    (
        "{founder} noticed a gap in the {market} market while working at a {prev_role}. "
        "After validating the idea through StartInsight's scoring engine, they built {company} "
        "to solve {problem}. Within {months} months, they achieved {mrr} MRR with "
        "{users} active users."
    ),
    (
        "While researching {market} trends on StartInsight, {founder} discovered that "
        "{problem}. They launched {company} as a lean MVP and iterated based on user feedback. "
        "The product resonated with {target_audience}, growing to {mrr} MRR in just {months} months."
    ),
    (
        "{founder} used StartInsight's AI analysis to validate a {market} opportunity. "
        "The data showed strong demand for solutions to {problem}. After building {company}, "
        "they secured {funding} in seed funding and now serve {users} customers."
    ),
]

FOUNDER_NAMES = [
    ("Alex Rivera", "AR"), ("Jordan Park", "JP"), ("Taylor Kim", "TK"),
    ("Morgan Chen", "MC"), ("Casey Brooks", "CB"), ("Riley Patel", "RP"),
    ("Avery Zhang", "AZ"), ("Quinn Douglas", "QD"), ("Jamie Torres", "JT"),
    ("Dakota Lee", "DL"), ("Sage Williams", "SW"), ("Phoenix Adams", "PA"),
]

PREV_ROLES = [
    "tech startup", "enterprise SaaS company", "fintech firm",
    "consulting agency", "Fortune 500 company", "AI research lab",
]

TARGET_AUDIENCES = [
    "small business owners", "SaaS founders", "enterprise teams",
    "solo entrepreneurs", "remote-first companies", "developer teams",
]


def _generate_company_name(insight: Insight) -> str:
    """Generate a plausible company name from insight data."""
    solution = insight.proposed_solution or "AI Tool"
    words = solution.split()[:2]
    suffixes = ["AI", "HQ", "Lab", "Hub", "ify", "ly", "io", "Stack"]
    return "".join(w.capitalize() for w in words) + random.choice(suffixes)


def _generate_metrics(score: float) -> dict:
    """Generate realistic metrics based on insight score."""
    base_mrr = int(score * random.randint(3000, 8000))
    return {
        "mrr": f"${base_mrr:,}",
        "users": str(random.randint(100, 5000)),
        "funding": random.choice([
            "$500K Pre-Seed", "$1.2M Seed", "$2M Seed",
            "$3.5M Series A", "Bootstrapped", "$750K Angel",
        ]),
        "growth_rate": f"{random.randint(15, 45)}% MoM",
    }


def _generate_timeline(months: int) -> list[dict]:
    """Generate a plausible startup timeline."""
    base = datetime.now(UTC) - timedelta(days=months * 30)
    events = [
        {"date": base.strftime("%Y-%m"), "milestone": "Idea validated on StartInsight"},
        {"date": (base + timedelta(days=30)).strftime("%Y-%m"), "milestone": "MVP launched"},
        {"date": (base + timedelta(days=90)).strftime("%Y-%m"), "milestone": "First 100 users"},
    ]
    if months > 4:
        events.append({
            "date": (base + timedelta(days=120)).strftime("%Y-%m"),
            "milestone": "Seed funding secured",
        })
    if months > 6:
        events.append({
            "date": (base + timedelta(days=180)).strftime("%Y-%m"),
            "milestone": "1,000 users milestone",
        })
    return events


async def _is_agent_enabled(db: AsyncSession) -> bool:
    """Check if the success stories agent is enabled."""
    result = await db.execute(
        select(AgentConfiguration).where(AgentConfiguration.agent_name == AGENT_NAME)
    )
    config = result.scalar_one_or_none()

    if not config:
        config = AgentConfiguration(
            agent_name=AGENT_NAME,
            is_enabled=True,
            model_name="gemini-1.5-flash",
            temperature=Decimal("0.8"),
            rate_limit_per_hour=5,
            cost_limit_daily_usd=Decimal("5.00"),
        )
        db.add(config)
        await db.commit()
        return True

    return config.is_enabled


async def update_success_stories_task(ctx: dict) -> dict:
    """Generate new success stories from top insights.

    Called by the scheduler every 7 days (Sundays at 05:00 UTC).
    Picks top insights from the past 7 days and creates founder case studies.
    """
    started_at = datetime.now(UTC)

    async with AsyncSessionLocal() as db:
        if not await _is_agent_enabled(db):
            logger.info(f"Agent {AGENT_NAME} is disabled, skipping")
            db.add(AgentExecutionLog(
                agent_type=AGENT_NAME,
                source="success_stories",
                status="skipped",
                started_at=started_at,
                completed_at=datetime.now(UTC),
                items_processed=0,
                extra_metadata={"reason": "agent_disabled"},
            ))
            await db.commit()
            return {"status": "skipped", "reason": "agent_disabled"}

        try:
            # Get top insights from last 7 days
            cutoff = datetime.now(UTC) - timedelta(days=7)
            result = await db.execute(
                select(Insight)
                .where(Insight.created_at >= cutoff)
                .order_by(Insight.relevance_score.desc())
                .limit(3)
            )
            insights = result.scalars().all()

            if not insights:
                completed_at = datetime.now(UTC)
                db.add(AgentExecutionLog(
                    agent_type=AGENT_NAME,
                    source="success_stories",
                    status="completed",
                    started_at=started_at,
                    completed_at=completed_at,
                    duration_ms=int((completed_at - started_at).total_seconds() * 1000),
                    items_processed=0,
                    extra_metadata={"reason": "no_new_insights"},
                ))
                await db.commit()
                logger.info("Success stories agent: no new insights in last 7 days")
                return {"status": "completed", "items": 0}

            # Check existing company names to avoid duplicates
            existing_names = await db.execute(
                select(SuccessStory.company_name)
            )
            existing = {r[0].lower() for r in existing_names.fetchall()}

            stories_created = 0
            available_founders = list(FOUNDER_NAMES)
            random.shuffle(available_founders)

            for insight in insights:
                company_name = _generate_company_name(insight)

                # Skip if similar company name exists
                if company_name.lower() in existing:
                    continue

                if not available_founders:
                    break

                founder_name, _ = available_founders.pop()
                months = random.randint(4, 12)
                score = insight.relevance_score or 7.0
                metrics = _generate_metrics(score)
                market = "technology"
                problem = (
                    insight.problem_statement[:100]
                    if insight.problem_statement
                    else "a critical industry pain point"
                )

                template = random.choice(JOURNEY_TEMPLATES)
                narrative = template.format(
                    founder=founder_name,
                    market=market,
                    prev_role=random.choice(PREV_ROLES),
                    company=company_name,
                    problem=problem,
                    months=months,
                    mrr=metrics["mrr"],
                    users=metrics["users"],
                    funding=metrics["funding"],
                    target_audience=random.choice(TARGET_AUDIENCES),
                )

                story = SuccessStory(
                    founder_name=founder_name,
                    company_name=company_name,
                    tagline=insight.proposed_solution or f"AI-powered {market} solution",
                    idea_summary=(
                        insight.problem_statement[:300]
                        if insight.problem_statement
                        else f"Solving key challenges in the {market} space"
                    ),
                    journey_narrative=narrative,
                    metrics=metrics,
                    timeline=_generate_timeline(months),
                    is_featured=score >= 8.0,
                    is_published=True,
                )
                db.add(story)
                existing.add(company_name.lower())
                stories_created += 1

            await db.commit()

            completed_at = datetime.now(UTC)
            db.add(AgentExecutionLog(
                agent_type=AGENT_NAME,
                source="success_stories",
                status="completed",
                started_at=started_at,
                completed_at=completed_at,
                duration_ms=int((completed_at - started_at).total_seconds() * 1000),
                items_processed=stories_created,
                extra_metadata={
                    "insights_evaluated": len(insights),
                    "stories_created": stories_created,
                },
            ))
            await db.commit()

            logger.info(
                f"Success stories agent: created {stories_created} stories "
                f"from {len(insights)} top insights"
            )
            return {"status": "completed", "items": stories_created}

        except Exception as e:
            completed_at = datetime.now(UTC)
            db.add(AgentExecutionLog(
                agent_type=AGENT_NAME,
                source="success_stories",
                status="failed",
                started_at=started_at,
                completed_at=completed_at,
                duration_ms=int((completed_at - started_at).total_seconds() * 1000),
                items_processed=0,
                error_message=str(e),
            ))
            await db.commit()
            logger.exception(f"Success stories agent failed: {e}")
            return {"status": "failed", "error": str(e)}
