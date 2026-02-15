#!/usr/bin/env python3
"""
Content Quality Validation Script

Purpose: Validate that enhanced analyzer produces insights exceeding IdeaBrowser benchmarks
Target: 450+ word problem statements with 8 psychological triggers and 8-dimension scoring
Status: Runtime validation for enhanced_analyzer fix in worker.py

Usage:
    uv run python test_content_quality.py

Requirements:
    - Backend server running (uvicorn app.main:app --reload)
    - Database with at least 1 processed insight (or unprocessed signal to trigger analysis)
    - Arq worker running (optional, for processing unprocessed signals)
"""

import asyncio
import sys
from datetime import datetime
from typing import Any

import httpx
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models import Insight

console = Console()

# ============================================================================
# CONFIGURATION
# ============================================================================

API_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"

# IdeaBrowser Benchmarks (9/10 Quality)
IDEABROWSER_WORD_COUNT = 400
IDEABROWSER_DIMENSIONS = 4
IDEABROWSER_KEYWORDS = 2
IDEABROWSER_QUALITY_SCORE = 9

# StartInsight Targets (10/10 Quality)
TARGET_WORD_COUNT = 450  # +12.5% vs IdeaBrowser
TARGET_DIMENSIONS = 8  # +100% vs IdeaBrowser
TARGET_KEYWORDS = 2  # Parity with IdeaBrowser minimum
TARGET_TRIGGERS = 6  # 6 of 8 psychological triggers required
TARGET_QUALITY_SCORE = 10  # Exceeds IdeaBrowser

# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================


def count_words(text: str) -> int:
    """Count words in text."""
    return len(text.split())


def check_psychological_triggers(problem_statement: str) -> dict[str, bool]:
    """
    Check for 8 psychological triggers in problem statement.

    Returns dict of trigger_name -> present (bool)
    """
    triggers = {
        "specificity": False,  # Numbers, timestamps, names
        "status_quo_breakdown": False,  # Moment when old way stops working
        "urgency": False,  # Measurable loss per hour/day
        "loss_aversion": False,  # What's being lost NOW
        "protagonist": False,  # Named character with specific role
        "sensory_details": False,  # Visual, temporal, emotional
        "contrast": False,  # Before/after contrast
        "risk_acknowledgment": False,  # Mentions objections, then counters
    }

    text_lower = problem_statement.lower()

    # 1. Specificity: Numbers, percentages, dollar amounts
    if any(char.isdigit() for char in problem_statement):
        if ("$" in problem_statement or "%" in problem_statement or
            "million" in text_lower or "billion" in text_lower or
            any(word in text_lower for word in ["users", "people", "customers", "clients"])):
            triggers["specificity"] = True

    # 2. Status Quo Breakdown: Keywords like "but", "however", "stopped working"
    if any(word in text_lower for word in ["but", "however", "stopped", "failed", "couldn't", "can't"]):
        triggers["status_quo_breakdown"] = True

    # 3. Urgency: Time-based language
    if any(word in text_lower for word in ["daily", "per day", "per hour", "overnight", "immediately", "urgent"]):
        triggers["urgency"] = True

    # 4. Loss Aversion: Language about losing, missing, wasting
    if any(word in text_lower for word in ["lose", "lost", "losing", "wasted", "missing", "gone"]):
        triggers["loss_aversion"] = True

    # 5. Protagonist: Proper names (capital letter followed by lowercase in middle of sentence)
    sentences = problem_statement.split(". ")
    for sentence in sentences[1:]:  # Skip first sentence (always capitalized)
        words = sentence.split()
        for word in words:
            if word and word[0].isupper() and len(word) > 1 and word[1:].islower():
                triggers["protagonist"] = True
                break

    # 6. Sensory Details: Colors, times, emotions
    if any(word in text_lower for word in [
        "red", "blue", "green", "bright", "dark",
        "11pm", "midnight", "morning", "evening",
        "frustrated", "anxious", "excited", "worried"
    ]):
        triggers["sensory_details"] = True

    # 7. Contrast: Before/after, old/new
    if any(pair[0] in text_lower and pair[1] in text_lower for pair in [
        ("before", "after"),
        ("old", "new"),
        ("previously", "now"),
        ("used to", "today")
    ]):
        triggers["contrast"] = True

    # 8. Risk Acknowledgment: "but", "however", "despite"
    if any(word in text_lower for word in ["despite", "although", "even though"]):
        triggers["risk_acknowledgment"] = True

    return triggers


def validate_scoring_dimensions(insight: dict[str, Any]) -> dict[str, int | str | None]:
    """Extract and validate 8-dimension scoring."""
    return {
        "opportunity_score": insight.get("opportunity_score"),
        "problem_score": insight.get("problem_score"),
        "feasibility_score": insight.get("feasibility_score"),
        "why_now_score": insight.get("why_now_score"),
        "revenue_potential": insight.get("revenue_potential"),
        "execution_difficulty": insight.get("execution_difficulty"),
        "go_to_market_score": insight.get("go_to_market_score"),
        "founder_fit_score": insight.get("founder_fit_score"),
    }


def calculate_quality_score(
    word_count: int,
    triggers: dict[str, bool],
    dimensions: dict[str, int | str | None],
    enhanced_fields: dict[str, Any],
) -> int:
    """
    Calculate overall quality score (0-10).

    Rubric:
    - Problem statement length: 2 points (450+ words)
    - Narrative quality: 2 points (6+ psychological triggers)
    - Scoring dimensions: 2 points (8 dimensions present)
    - Enhanced fields: 2 points (market gap, why now, value ladder)
    - Community + trends: 1 point (3-4 platforms, 2-5 keywords)
    - Execution plan: 1 point (5-7 steps)
    """
    score = 0

    # 1. Problem statement length (2 points)
    if word_count >= TARGET_WORD_COUNT:
        score += 2
    elif word_count >= IDEABROWSER_WORD_COUNT:
        score += 1

    # 2. Narrative quality (2 points)
    trigger_count = sum(triggers.values())
    if trigger_count >= TARGET_TRIGGERS:
        score += 2
    elif trigger_count >= 4:
        score += 1

    # 3. Scoring dimensions (2 points)
    dimensions_present = sum(1 for v in dimensions.values() if v is not None)
    if dimensions_present == TARGET_DIMENSIONS:
        score += 2
    elif dimensions_present >= IDEABROWSER_DIMENSIONS:
        score += 1

    # 4. Enhanced fields (2 points)
    market_gap = enhanced_fields.get("market_gap_analysis", "")
    why_now = enhanced_fields.get("why_now_analysis", "")
    value_ladder = enhanced_fields.get("value_ladder")

    enhanced_score = 0
    if market_gap and count_words(market_gap) >= 200:
        enhanced_score += 1
    if why_now and count_words(why_now) >= 200:
        enhanced_score += 1
    if value_ladder and isinstance(value_ladder, dict) and len(value_ladder) >= 3:
        enhanced_score += 0.5

    score += min(2, int(enhanced_score))

    # 5. Community + trends (1 point)
    community_signals = enhanced_fields.get("community_signals_chart", {})
    trend_keywords = enhanced_fields.get("trend_keywords", [])

    if isinstance(community_signals, dict) and len(community_signals) >= 3:
        score += 0.5
    if isinstance(trend_keywords, list) and len(trend_keywords) >= TARGET_KEYWORDS:
        score += 0.5

    # 6. Execution plan (1 point)
    execution_plan = enhanced_fields.get("execution_plan", {})
    if isinstance(execution_plan, dict):
        steps = execution_plan.get("steps", [])
        if isinstance(steps, list) and 5 <= len(steps) <= 7:
            score += 1

    return int(score)


# ============================================================================
# MAIN VALIDATION
# ============================================================================


async def fetch_latest_insight() -> dict[str, Any] | None:
    """Fetch latest insight from API."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{API_URL}/api/insights?limit=1")
            response.raise_for_status()
            data = response.json()
            insights = data.get("insights", [])
            return insights[0] if insights else None
        except Exception as e:
            console.print(f"[red]Error fetching insight: {e}[/red]")
            return None


async def fetch_latest_insight_from_db() -> Insight | None:
    """Fetch latest insight directly from database."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Insight).order_by(Insight.created_at.desc()).limit(1)
        )
        return result.scalar_one_or_none()


async def validate_content_quality() -> None:
    """Main validation function."""
    console.print(Panel.fit(
        "[bold cyan]StartInsight Content Quality Validation[/bold cyan]\n"
        "Target: Exceed IdeaBrowser benchmarks (9/10 → 10/10 quality)",
        border_style="cyan"
    ))

    # Step 1: Fetch latest insight
    console.print("\n[yellow]Step 1:[/yellow] Fetching latest insight...")

    insight = await fetch_latest_insight()
    if not insight:
        console.print("[red]No insights found via API. Trying database...[/red]")
        db_insight = await fetch_latest_insight_from_db()
        if not db_insight:
            console.print("[red]❌ No insights found in database.[/red]")
            console.print("\n[yellow]Next steps:[/yellow]")
            console.print("1. Start backend server: uvicorn app.main:app --reload")
            console.print("2. Start Arq worker: uv run arq app.worker.WorkerSettings")
            console.print("3. Wait for signal processing to generate insights")
            console.print("4. Re-run this script")
            sys.exit(1)

        # Convert DB model to dict
        insight = {
            "id": str(db_insight.id),
            "problem_statement": db_insight.problem_statement,
            "proposed_solution": db_insight.proposed_solution,
            "opportunity_score": db_insight.opportunity_score,
            "problem_score": db_insight.problem_score,
            "feasibility_score": db_insight.feasibility_score,
            "why_now_score": db_insight.why_now_score,
            "revenue_potential": db_insight.revenue_potential,
            "execution_difficulty": db_insight.execution_difficulty,
            "go_to_market_score": db_insight.go_to_market_score,
            "founder_fit_score": db_insight.founder_fit_score,
            "market_gap_analysis": db_insight.market_gap_analysis,
            "why_now_analysis": db_insight.why_now_analysis,
            "community_signals_chart": db_insight.community_signals_chart,
            "trend_keywords": db_insight.trend_keywords,
            "value_ladder": db_insight.value_ladder,
            "execution_plan": db_insight.execution_plan,
            "created_at": db_insight.created_at.isoformat() if db_insight.created_at else None,
        }

    console.print(f"[green]✓ Found insight: {insight['id']}[/green]")
    console.print(f"  Created: {insight.get('created_at', 'N/A')}")

    # Step 2: Validate problem statement word count
    console.print("\n[yellow]Step 2:[/yellow] Validating problem statement length...")

    problem_statement = insight.get("problem_statement", "")
    word_count = count_words(problem_statement)

    console.print(f"  Word count: {word_count}")
    console.print(f"  Target: {TARGET_WORD_COUNT}+ words (IdeaBrowser: {IDEABROWSER_WORD_COUNT}+)")

    if word_count >= TARGET_WORD_COUNT:
        console.print(f"  [green]✓ PASS[/green] (+{word_count - IDEABROWSER_WORD_COUNT} words vs IdeaBrowser)")
    elif word_count >= IDEABROWSER_WORD_COUNT:
        console.print("  [yellow]⚠ PARTIAL[/yellow] (Exceeds IdeaBrowser but below target)")
    else:
        console.print("  [red]✗ FAIL[/red] (Below IdeaBrowser benchmark)")

    # Step 3: Validate psychological triggers
    console.print("\n[yellow]Step 3:[/yellow] Checking psychological triggers...")

    triggers = check_psychological_triggers(problem_statement)
    trigger_count = sum(triggers.values())

    trigger_table = Table(title="Psychological Triggers")
    trigger_table.add_column("Trigger", style="cyan")
    trigger_table.add_column("Present", style="green")

    for trigger_name, present in triggers.items():
        trigger_table.add_row(
            trigger_name.replace("_", " ").title(),
            "✓" if present else "✗"
        )

    console.print(trigger_table)
    console.print(f"\n  Triggers present: {trigger_count}/8")
    console.print(f"  Target: {TARGET_TRIGGERS}+ triggers")

    if trigger_count >= TARGET_TRIGGERS:
        console.print("  [green]✓ PASS[/green]")
    else:
        console.print(f"  [red]✗ FAIL[/red] (Need {TARGET_TRIGGERS - trigger_count} more)")

    # Step 4: Validate 8-dimension scoring
    console.print("\n[yellow]Step 4:[/yellow] Validating scoring dimensions...")

    dimensions = validate_scoring_dimensions(insight)
    dimensions_present = sum(1 for v in dimensions.values() if v is not None)

    dimension_table = Table(title="8-Dimension Scoring")
    dimension_table.add_column("Dimension", style="cyan")
    dimension_table.add_column("Value", style="green")

    for dim_name, value in dimensions.items():
        dimension_table.add_row(
            dim_name.replace("_", " ").title(),
            str(value) if value is not None else "[red]Missing[/red]"
        )

    console.print(dimension_table)
    console.print(f"\n  Dimensions present: {dimensions_present}/{TARGET_DIMENSIONS}")
    console.print(f"  IdeaBrowser: {IDEABROWSER_DIMENSIONS} dimensions")

    if dimensions_present == TARGET_DIMENSIONS:
        console.print(f"  [green]✓ PASS[/green] (+{TARGET_DIMENSIONS - IDEABROWSER_DIMENSIONS} vs IdeaBrowser)")
    else:
        console.print(f"  [red]✗ FAIL[/red] (Missing {TARGET_DIMENSIONS - dimensions_present} dimensions)")

    # Step 5: Validate enhanced fields
    console.print("\n[yellow]Step 5:[/yellow] Validating enhanced fields...")

    enhanced_fields = {
        "market_gap_analysis": insight.get("market_gap_analysis", ""),
        "why_now_analysis": insight.get("why_now_analysis", ""),
        "community_signals_chart": insight.get("community_signals_chart", {}),
        "trend_keywords": insight.get("trend_keywords", []),
        "value_ladder": insight.get("value_ladder", {}),
        "execution_plan": insight.get("execution_plan", {}),
    }

    enhanced_table = Table(title="Enhanced Fields")
    enhanced_table.add_column("Field", style="cyan")
    enhanced_table.add_column("Status", style="green")
    enhanced_table.add_column("Details", style="yellow")

    # Market gap analysis
    market_gap = enhanced_fields["market_gap_analysis"]
    market_gap_words = count_words(market_gap) if market_gap else 0
    enhanced_table.add_row(
        "Market Gap Analysis",
        "✓" if market_gap_words >= 200 else "✗",
        f"{market_gap_words} words (target: 200+)"
    )

    # Why now analysis
    why_now = enhanced_fields["why_now_analysis"]
    why_now_words = count_words(why_now) if why_now else 0
    enhanced_table.add_row(
        "Why Now Analysis",
        "✓" if why_now_words >= 200 else "✗",
        f"{why_now_words} words (target: 200+)"
    )

    # Community signals
    community_signals = enhanced_fields["community_signals_chart"]
    community_count = len(community_signals) if isinstance(community_signals, dict) else 0
    enhanced_table.add_row(
        "Community Signals",
        "✓" if community_count >= 3 else "✗",
        f"{community_count} platforms (target: 3-4)"
    )

    # Trend keywords
    trend_keywords = enhanced_fields["trend_keywords"]
    keyword_count = len(trend_keywords) if isinstance(trend_keywords, list) else 0
    enhanced_table.add_row(
        "Trend Keywords",
        "✓" if keyword_count >= TARGET_KEYWORDS else "✗",
        f"{keyword_count} keywords (target: 2-5)"
    )

    # Value ladder
    value_ladder = enhanced_fields["value_ladder"]
    value_ladder_tiers = len(value_ladder) if isinstance(value_ladder, dict) else 0
    enhanced_table.add_row(
        "Value Ladder",
        "✓" if value_ladder_tiers >= 3 else "✗",
        f"{value_ladder_tiers} tiers (target: 4)"
    )

    # Execution plan
    execution_plan = enhanced_fields["execution_plan"]
    execution_steps = 0
    if isinstance(execution_plan, dict):
        steps = execution_plan.get("steps", [])
        execution_steps = len(steps) if isinstance(steps, list) else 0
    enhanced_table.add_row(
        "Execution Plan",
        "✓" if 5 <= execution_steps <= 7 else "✗",
        f"{execution_steps} steps (target: 5-7)"
    )

    console.print(enhanced_table)

    # Step 6: Calculate overall quality score
    console.print("\n[yellow]Step 6:[/yellow] Calculating overall quality score...")

    quality_score = calculate_quality_score(
        word_count, triggers, dimensions, enhanced_fields
    )

    console.print(f"\n  Overall Quality Score: {quality_score}/10")
    console.print(f"  IdeaBrowser Benchmark: {IDEABROWSER_QUALITY_SCORE}/10")
    console.print(f"  StartInsight Target: {TARGET_QUALITY_SCORE}/10")

    # Final result
    console.print("\n" + "=" * 60)

    if quality_score >= TARGET_QUALITY_SCORE:
        console.print(Panel.fit(
            f"[bold green]✓ VALIDATION PASSED[/bold green]\n\n"
            f"Quality Score: {quality_score}/10 (Target: {TARGET_QUALITY_SCORE}/10)\n"
            f"Word Count: {word_count} words (Target: {TARGET_WORD_COUNT}+)\n"
            f"Triggers: {trigger_count}/8 (Target: {TARGET_TRIGGERS}+)\n"
            f"Dimensions: {dimensions_present}/8 (Target: {TARGET_DIMENSIONS})\n\n"
            f"[bold]StartInsight content quality EXCEEDS IdeaBrowser benchmarks![/bold]",
            border_style="green"
        ))
        sys.exit(0)
    elif quality_score >= IDEABROWSER_QUALITY_SCORE:
        console.print(Panel.fit(
            f"[bold yellow]⚠ PARTIAL PASS[/bold yellow]\n\n"
            f"Quality Score: {quality_score}/10 (Target: {TARGET_QUALITY_SCORE}/10)\n"
            f"IdeaBrowser Benchmark: {IDEABROWSER_QUALITY_SCORE}/10\n\n"
            f"Content quality matches IdeaBrowser but doesn't exceed targets.\n"
            f"Review enhanced_analyzer.py system prompt for improvements.",
            border_style="yellow"
        ))
        sys.exit(1)
    else:
        console.print(Panel.fit(
            f"[bold red]✗ VALIDATION FAILED[/bold red]\n\n"
            f"Quality Score: {quality_score}/10 (Target: {TARGET_QUALITY_SCORE}/10)\n"
            f"IdeaBrowser Benchmark: {IDEABROWSER_QUALITY_SCORE}/10\n\n"
            f"Content quality BELOW IdeaBrowser benchmarks.\n"
            f"Verify worker.py is using enhanced_analyzer (line 348).",
            border_style="red"
        ))
        sys.exit(1)


if __name__ == "__main__":
    console.print(f"[cyan]Starting validation at {datetime.now().isoformat()}[/cyan]\n")
    asyncio.run(validate_content_quality())
