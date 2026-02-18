"""Seed AgentConfiguration records for the three quality/publishing agents.

Run: cd backend && uv run python scripts/seed_agent_configs.py
"""

import asyncio
import logging

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.agent_control import AgentConfiguration

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

AGENT_CONFIGS = [
    {
        "agent_name": "market_insight_publisher",
        "is_enabled": True,
        "model_name": "gemini-1.5-flash",
        "temperature": 0.7,
        "max_tokens": 8192,
        "rate_limit_per_hour": 10,
        "cost_limit_daily_usd": 5.0,
        "custom_prompts": {
            "description": "Generates professional data-driven market insight articles every 3 days.",
            "schedule": "Every 3 days at 06:00 UTC",
            "output": "Draft MarketInsight articles for quality review",
        },
    },
    {
        "agent_name": "market_insight_quality_reviewer",
        "is_enabled": True,
        "model_name": "gemini-1.5-flash",
        "temperature": 0.3,
        "max_tokens": 4096,
        "rate_limit_per_hour": 20,
        "cost_limit_daily_usd": 3.0,
        "custom_prompts": {
            "description": "Reviews draft market insight articles for quality. Auto-publishes articles scoring 7+/10.",
            "schedule": "Every 3 days at 08:30 UTC (2.5h after publisher)",
            "output": "Quality scores, publish/reject decisions",
        },
    },
    {
        "agent_name": "insight_quality_reviewer",
        "is_enabled": True,
        "model_name": "gemini-1.5-flash",
        "temperature": 0.2,
        "max_tokens": 4096,
        "rate_limit_per_hour": 50,
        "cost_limit_daily_usd": 10.0,
        "custom_prompts": {
            "description": "Audits all startup insights for data completeness, score consistency, and title quality.",
            "schedule": "Weekly on Mondays at 03:00 UTC",
            "output": "Quality audit reports, flags insights needing re-analysis",
        },
    },
]


async def seed_agent_configs():
    """Upsert agent configurations."""
    async with AsyncSessionLocal() as session:
        for config_data in AGENT_CONFIGS:
            # Check if already exists
            result = await session.execute(
                select(AgentConfiguration).where(
                    AgentConfiguration.agent_name == config_data["agent_name"]
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                logger.info(f"Agent '{config_data['agent_name']}' already exists, updating...")
                for key, value in config_data.items():
                    if key != "agent_name":
                        setattr(existing, key, value)
            else:
                logger.info(f"Creating agent config: '{config_data['agent_name']}'")
                agent = AgentConfiguration(**config_data)
                session.add(agent)

        await session.commit()
        logger.info(f"Seeded {len(AGENT_CONFIGS)} agent configurations")


if __name__ == "__main__":
    asyncio.run(seed_agent_configs())
