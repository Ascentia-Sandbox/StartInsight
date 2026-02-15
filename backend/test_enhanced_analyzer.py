#!/usr/bin/env python3
"""
Enhanced Analyzer Direct Test

Purpose: Test that enhanced_analyzer produces 450+ word problem statements
Status: Direct validation of enhanced analyzer fix

Usage:
    uv run python test_enhanced_analyzer.py
"""

import asyncio
from datetime import datetime

from rich.console import Console
from rich.panel import Panel

from app.agents.enhanced_analyzer import analyze_signal_enhanced_with_retry
from app.models import RawSignal

console = Console()


async def test_enhanced_analyzer():
    """Test enhanced analyzer with a sample signal."""
    console.print(Panel.fit(
        "[bold cyan]Enhanced Analyzer Direct Test[/bold cyan]\n"
        "Testing enhanced analyzer produces 450+ word problem statements",
        border_style="cyan"
    ))

    # Create a test signal
    test_signal = RawSignal(
        source="reddit",
        url="https://reddit.com/r/startups/test",
        content="""
        Title: Can't find affordable SMS automation for small business aftercare

        I run a piercing studio and the biggest issue we have is clients not following
        aftercare instructions. We give them a paper sheet but 80% lose it within 2 days.

        Infections are common (about 35% of our clients) and it's costing us reputation.
        One bad review can cost us thousands in lost business.

        I looked into app-based solutions but our clients (mostly 18-25) don't want
        to download another app. SMS would be perfect but services like Twilio are
        too complex for me to set up.

        I'd pay $99/month for a simple SMS service that sends automated aftercare
        reminders. Send them daily care instructions for 6 weeks. That's it.

        The piercing industry is $2.1 billion in the US. There are 27 million
        piercings done each year. Studios would pay for this if it prevents infections.

        Comments: "I have the same problem with my tattoo studio!", "Check out
        MedReminder but it's $500/month", "You could use Zapier + Twilio but setup
        takes 10 hours"
        """,
        extra_metadata={"upvotes": 142, "comments": 28},
        created_at=datetime.utcnow(),
        processed=False,
    )

    console.print("\n[yellow]Step 1:[/yellow] Calling enhanced analyzer...")
    console.print(f"  Signal source: {test_signal.source}")
    console.print(f"  Signal content length: {len(test_signal.content)} chars\n")

    # Call enhanced analyzer
    try:
        insight = await analyze_signal_enhanced_with_retry(test_signal)

        console.print("[green]✓ Enhanced analyzer completed successfully[/green]\n")

        # Validate problem statement
        console.print("[yellow]Step 2:[/yellow] Validating problem statement...")

        problem_statement = insight.problem_statement
        word_count = len(problem_statement.split())

        console.print(f"  Word count: {word_count}")
        console.print("  Target: 450+ words")

        if word_count >= 450:
            console.print(f"  [green]✓ PASS[/green] (Exceeds target by {word_count - 450} words)\n")
        elif word_count >= 400:
            console.print("  [yellow]⚠ PARTIAL[/yellow] (Exceeds IdeaBrowser 400+ but below target)\n")
        else:
            console.print(f"  [red]✗ FAIL[/red] (Below target by {450 - word_count} words)\n")

        # Show snippet
        console.print("[yellow]Problem Statement Preview:[/yellow]")
        console.print(f"{problem_statement[:500]}...\n")

        # Validate enhanced fields
        console.print("[yellow]Step 3:[/yellow] Validating enhanced fields...")

        checks = []

        # Market gap analysis
        market_gap_words = len(insight.market_gap_analysis.split()) if insight.market_gap_analysis else 0
        checks.append(("Market Gap Analysis", market_gap_words >= 200, f"{market_gap_words} words"))

        # Why now analysis
        why_now_words = len(insight.why_now_analysis.split()) if insight.why_now_analysis else 0
        checks.append(("Why Now Analysis", why_now_words >= 200, f"{why_now_words} words"))

        # Community signals
        community_count = len(insight.community_signals_chart) if insight.community_signals_chart else 0
        checks.append(("Community Signals", community_count >= 3, f"{community_count} platforms"))

        # Trend keywords
        keyword_count = len(insight.trend_keywords) if insight.trend_keywords else 0
        checks.append(("Trend Keywords", keyword_count >= 2, f"{keyword_count} keywords"))

        # Value ladder
        value_ladder_tiers = len(insight.value_ladder) if insight.value_ladder else 0
        checks.append(("Value Ladder", value_ladder_tiers >= 3, f"{value_ladder_tiers} tiers"))

        # Execution plan
        execution_steps = 0
        if insight.execution_plan and isinstance(insight.execution_plan, dict):
            steps = insight.execution_plan.get("steps", [])
            execution_steps = len(steps) if isinstance(steps, list) else 0
        checks.append(("Execution Plan", 5 <= execution_steps <= 7, f"{execution_steps} steps"))

        for field_name, passed, details in checks:
            status = "[green]✓[/green]" if passed else "[red]✗[/red]"
            console.print(f"  {status} {field_name}: {details}")

        # Overall result
        passed_checks = sum(1 for _, passed, _ in checks)
        total_checks = len(checks)

        console.print(f"\n[yellow]Enhanced Fields:[/yellow] {passed_checks}/{total_checks} passed")

        # Validate scoring dimensions
        console.print("\n[yellow]Step 4:[/yellow] Validating 8-dimension scoring...")

        dimensions = [
            ("Opportunity Score", insight.opportunity_score),
            ("Problem Score", insight.problem_score),
            ("Feasibility Score", insight.feasibility_score),
            ("Why Now Score", insight.why_now_score),
            ("Revenue Potential", insight.revenue_potential),
            ("Execution Difficulty", insight.execution_difficulty),
            ("Go To Market Score", insight.go_to_market_score),
            ("Founder Fit Score", insight.founder_fit_score),
        ]

        dimensions_present = sum(1 for _, value in dimensions if value is not None)

        for dim_name, value in dimensions:
            status = "[green]✓[/green]" if value is not None else "[red]✗[/red]"
            console.print(f"  {status} {dim_name}: {value}")

        console.print(f"\n[yellow]Dimensions:[/yellow] {dimensions_present}/8 present")

        # Final verdict
        console.print("\n" + "=" * 60)

        if word_count >= 450 and passed_checks >= 5 and dimensions_present == 8:
            console.print(Panel.fit(
                f"[bold green]✓ ENHANCED ANALYZER TEST PASSED[/bold green]\n\n"
                f"Word Count: {word_count} (Target: 450+)\n"
                f"Enhanced Fields: {passed_checks}/{total_checks}\n"
                f"Dimensions: {dimensions_present}/8\n\n"
                f"[bold]Enhanced analyzer is working correctly![/bold]",
                border_style="green"
            ))
            return True
        else:
            console.print(Panel.fit(
                f"[bold red]✗ ENHANCED ANALYZER TEST FAILED[/bold red]\n\n"
                f"Word Count: {word_count} (Target: 450+)\n"
                f"Enhanced Fields: {passed_checks}/{total_checks}\n"
                f"Dimensions: {dimensions_present}/8\n\n"
                f"Enhanced analyzer needs improvements.",
                border_style="red"
            ))
            return False

    except Exception as e:
        console.print(f"[red]✗ Error calling enhanced analyzer: {e}[/red]")
        console.print("\n[yellow]Traceback:[/yellow]")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    console.print(f"[cyan]Starting test at {datetime.now().isoformat()}[/cyan]\n")
    result = asyncio.run(test_enhanced_analyzer())
    exit(0 if result else 1)
