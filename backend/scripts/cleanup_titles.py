"""Clean up insight proposed_solution fields to be concise product names.

Transforms verbose AI-generated titles like:
  "Develop an AI-powered platform that automates meeting summaries..."
Into concise product names like:
  "AI Meeting Summary & Task Extraction Platform"
"""

import asyncio
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy.ext.asyncio import (  # noqa: E402
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings  # noqa: E402

# Manual overrides for titles the automated rules can't handle well.
# Key = first 70 chars of original proposed_solution (avoids collisions)
OVERRIDE_KEY_LEN = 70
MANUAL_OVERRIDES: dict[str, str] = {
    # Titles where automated truncation leaves incomplete phrases
    "An AI-powered platform that generates complete brand asset packages fo": "AI Brand Asset Generator for Solopreneurs",
    "An AI-powered platform that automates API documentation and provides i": "AI API Documentation & Developer Support",
    "Develop an AI-powered tool that integrates with existing collaboration": "AI Collaboration Summarizer for Slack & Jira",
    "Develop an AI-powered platform that integrates with e-commerce platfor": "AI E-Commerce Marketing Intelligence",
    "An AI-powered content repurposing engine that automatically adapts con": "AI Content Repurposing Engine",
    "An AI-powered platform that helps career transitioners optimize their ": "AI Resume Optimizer for Career Changers",
    "Develop an AI-driven tool that analyzes websites and provides lead qua": "AI Website Lead Qualification Tool",
    "AI-powered content optimization tool focused on simplicity and afforda": "AI Content Optimizer for Small Businesses",
    "An AI-powered legal analysis platform trained on startup contracts tha": "AI Legal Analyzer for Startup Contracts",
    "An AI-powered platform that analyzes website visitor behavior in real-": "AI Website Visitor Behavior Analytics",
    "An AI customer support platform using advanced language models trained": "AI Customer Support with LLMs",
    "Develop an AI-powered platform for newsletter content curation and rep": "AI Newsletter Curation & Repurposing",
    "Develop an AI-powered tool that automatically repurposes existing cont": "AI Multi-Format Content Repurposer",
    "An AI content engine that ingests long-form content and automatically ": "AI Long-Form Content Distribution Engine",
    "Develop an AI-powered platform that automates meeting summaries, task ": "AI Meeting Summary & Task Extraction",
    "Develop an AI-powered platform that automatically repurposes long-form": "AI Long-Form Content Repurposer",
    "Develop an AI-powered CRM specifically designed for small construction": "AI CRM for Construction Businesses",
    "Develop an AI-powered platform that generates personalized side hustle": "AI Side Hustle Idea Generator",
    "AI ticketing system that auto-categorizes, suggests responses, and esc": "AI Ticketing with Auto-Categorization",
    "AI-powered platform automating invoice reconciliation for SMBs by inte": "AI Invoice Reconciliation for SMBs",
    "A visual integration platform designed specifically for non-technical ": "Visual Integration Builder for SMBs",
    "An AI-driven learning platform that assesses developer skills through ": "AI Developer Skill Assessment & Career Path",
    "Develop an AI-powered automated bookkeeping solution for solo founders": "AI Bookkeeping for Solo Founders",
    "An automated financial close platform designed for SMBs, integrating w": "Automated Financial Close for SMBs",
    "An AI-powered code review platform that learns from your codebase patt": "AI Code Review with Pattern Learning",
    "Develop an AI-powered code review tool that automates vulnerability de": "AI Code Review & Vulnerability Scanner",
    "Develop an AI-powered code review tool that automates the process and ": "AI Code Review with Instant Feedback",
    "AI-powered code review tool that learns team conventions and catches b": "AI Code Review with Convention Learning",
    "An AI-native meeting platform that uses advanced language models to un": "AI-Native Meeting Intelligence Platform",
    "A plug-and-play predictive maintenance platform using affordable retro": "Plug-and-Play Predictive Maintenance Platform",
    "An AI-driven inventory platform for e-commerce that integrates with ma": "AI Inventory & Demand Prediction for E-Commerce",
    "Cloud-based video editor with AI-powered editing suggestions, runs ent": "Cloud-Based AI Video Editor for Browser",
    "Real-time API monitoring with intelligent alerting and automatic root ": "Real-Time API Monitoring & Root Cause Analysis",
    "Develop an AI-powered user behavior analysis platform for e-commerce b": "AI User Behavior Analytics for E-Commerce",
}


def clean_title(raw: str) -> str:
    """Transform a verbose proposed_solution into a concise product name."""
    # Check manual overrides first
    prefix = raw.strip()[:OVERRIDE_KEY_LEN]
    if prefix in MANUAL_OVERRIDES:
        return MANUAL_OVERRIDES[prefix]

    title = raw.strip().rstrip(".")

    # Step 1: Strip leading verb phrases
    title = re.sub(
        r"^(Develop|Build|Create|Design|Implement|Launch)\s+(an?\s+)?",
        "",
        title,
        flags=re.IGNORECASE,
    )

    # Step 2: Strip leading articles for product-name style
    title = re.sub(r"^(An?\s+)", "", title, flags=re.IGNORECASE)

    # Capitalize first letter
    if title and title[0].islower():
        title = title[0].upper() + title[1:]

    # Step 3: For "X platform/tool/engine that Y" patterns, try to make a descriptive name
    # e.g. "AI-powered platform that automates meeting summaries" → "AI-Powered Meeting Summary Automation"
    # But only truncate if too long
    if len(title) > 60:
        # Cut at clause boundaries
        for pattern in [
            r"\s+that\s+",
            r"\s+which\s+",
            r"\s+designed\s+",
            r"\s+tailored\s+",
            r"\s+featuring\s+",
            r"\s+trained\s+",
            r"\s+integrating\s+with\s+",
            r"\s+using\s+",
            r"\s+to\s+(provide|save|help|enable|offer|automate|analyze|predict|improve|optimize|manage|generate|create)\s+",
            r"\s+by\s+(intelligently|automatically)\s+",
        ]:
            match = re.search(pattern, title, flags=re.IGNORECASE)
            if match and 20 < match.start() < 70:
                title = title[: match.start()].strip()
                break

    # Step 4: For "X for Y" - keep the "for Y" part if it's specific (SMBs, Gen Z, etc.)
    # but cut if it adds a second clause
    if len(title) > 60:
        # Try cutting at comma
        comma_pos = title.find(",")
        if comma_pos > 20:
            title = title[:comma_pos].strip()

    # Step 5: Hard truncate at word boundary if still too long
    if len(title) > 60:
        cut = title[:60].rfind(" ")
        if cut > 20:
            title = title[:cut].strip()

    # Step 6: Clean trailing noise
    # Remove trailing prepositions, conjunctions, articles, adverbs
    title = re.sub(
        r"\s+(for|and|with|to|in|by|from|of|the|an?|specifically|automatically|instantly|existing)\s*$",
        "",
        title,
        flags=re.IGNORECASE,
    )
    # Second pass (might expose another trailing word)
    title = re.sub(
        r"\s+(for|and|with|to|in|by|from|of|the|an?)\s*$",
        "",
        title,
        flags=re.IGNORECASE,
    )

    title = title.rstrip(".,;:")

    return title


async def main():
    engine = create_async_engine(settings.async_database_url, echo=False)
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with Session() as db:
        from sqlalchemy import text
        result = await db.execute(text("SELECT id, proposed_solution FROM insights ORDER BY created_at DESC"))
        rows = result.fetchall()

        print(f"Found {len(rows)} insights\n")

        updates = []
        for row in rows:
            old = row[1]
            new = clean_title(old)
            if old != new:
                updates.append((row[0], old, new))
                print(f"  OLD ({len(old):3d}ch): {old[:120]}")
                print(f"  NEW ({len(new):3d}ch): {new}")
                print()

        print(f"\n{'='*60}")
        print(f"Total: {len(updates)} titles to update out of {len(rows)}")

        if updates:
            confirm = input("\nApply changes? (y/n): ").strip().lower()
            if confirm == "y":
                for uid, old, new in updates:
                    await db.execute(
                        text("UPDATE insights SET proposed_solution = :new WHERE id = :id"),
                        {"new": new, "id": uid},
                    )
                await db.commit()
                print(f"\nUpdated {len(updates)} titles!")
            else:
                print("Aborted.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
