"""Weekly AI Trend Report PDF — branded WeasyPrint template.

Generates a downloadable PDF lead magnet for the PLG funnel.

Free version (no auth / free tier):
  - Cover page with issue number + date
  - Top 10 trend summaries (title + problem + relevance score)
  - Upgrade CTA page (teases full analysis)

Pro version (pro/enterprise tier):
  - Same cover
  - Top 10 trends with full detail (market size, revenue potential, opportunity score, solution)
  - No paywall page

Entry point:
  build_weekly_report_html(insights, week_number, is_pro) -> str
  generate_weekly_report_pdf(html) -> bytes  (runs WeasyPrint in executor)
"""

from __future__ import annotations

import asyncio
import logging
from datetime import date, timedelta
from typing import Any

logger = logging.getLogger(__name__)

# ─── Brand tokens (DESIGN.md) ────────────────────────────────────────────────
TEAL = "#0D7377"
TEAL_LIGHT = "#E6F4F4"
AMBER = "#C48B0A"
AMBER_LIGHT = "#FDF5DC"
INK = "#1C1C1E"
MUTED = "#6B7280"
BG = "#FAF9F7"
CARD_BG = "#FFFFFF"
BORDER = "#E5E0D8"
# ─────────────────────────────────────────────────────────────────────────────


def _score_bar(score_pct: int, width: int = 120) -> str:
    """Return inline HTML for a teal score bar + label."""
    fill = max(4, int(width * score_pct / 100))
    return f"""
    <div style="display:inline-block; vertical-align:middle;">
      <div style="
        background:{BORDER}; border-radius:3px;
        width:{width}px; height:6px; overflow:hidden;
      ">
        <div style="background:{TEAL}; width:{fill}px; height:6px; border-radius:3px;"></div>
      </div>
    </div>
    <span style="
      font-family:monospace; font-size:11px;
      color:{TEAL}; font-weight:700; margin-left:6px;
      vertical-align:middle;
    ">{score_pct}%</span>
    """


def _free_insight_card(idx: int, insight: dict[str, Any]) -> str:
    """Render a single trend card for the free (teaser) version."""
    title = insight.get("title") or "Untitled"
    problem = insight.get("problem_statement") or ""
    score_raw = insight.get("relevance_score", "0%")
    score_pct = int(score_raw.replace("%", "")) if isinstance(score_raw, str) else 0

    return f"""
    <div style="
      background:{CARD_BG}; border:1px solid {BORDER};
      border-radius:6px; padding:16px 20px;
      margin-bottom:12px; page-break-inside:avoid;
    ">
      <div style="display:flex; align-items:center; margin-bottom:8px;">
        <span style="
          font-family:monospace; font-size:11px; font-weight:700;
          color:{TEAL}; background:{TEAL_LIGHT};
          padding:2px 8px; border-radius:3px; margin-right:10px;
          min-width:22px; text-align:center;
        ">#{idx}</span>
        <span style="
          font-family:Georgia,'Times New Roman',serif;
          font-size:14px; font-weight:700; color:{INK};
        ">{title}</span>
      </div>
      <p style="
        font-family:system-ui,-apple-system,Arial,sans-serif;
        font-size:12px; color:{MUTED}; line-height:1.55;
        margin:0 0 10px 0;
      ">{problem[:180]}{"…" if len(problem) > 180 else ""}</p>
      <div>
        <span style="
          font-family:system-ui,sans-serif; font-size:10px;
          color:{MUTED}; text-transform:uppercase; letter-spacing:0.06em;
          margin-right:8px; vertical-align:middle;
        ">Relevance</span>
        {_score_bar(score_pct)}
      </div>
    </div>
    """


def _pro_insight_card(idx: int, insight: dict[str, Any]) -> str:
    """Render a full-detail trend card for pro subscribers."""
    title = insight.get("title") or "Untitled"
    problem = insight.get("problem_statement") or ""
    solution = insight.get("proposed_solution") or ""
    score_raw = insight.get("relevance_score", "0%")
    score_pct = int(score_raw.replace("%", "")) if isinstance(score_raw, str) else 0
    market_size = insight.get("market_size") or insight.get("market_size_estimate") or "—"
    revenue = insight.get("revenue_potential") or "—"
    opp_score = insight.get("opportunity_score")
    url = insight.get("insight_url") or ""

    opp_html = ""
    if opp_score:
        opp_html = f"""
        <span style="
          font-family:monospace; font-size:10px; font-weight:700;
          color:{AMBER}; background:{AMBER_LIGHT};
          padding:2px 7px; border-radius:3px; margin-left:8px;
        ">Opp {opp_score}/100</span>"""

    solution_html = ""
    if solution:
        solution_html = f"""
        <div style="
          background:{TEAL_LIGHT}; border-left:3px solid {TEAL};
          border-radius:0 4px 4px 0; padding:8px 12px;
          margin-top:10px;
        ">
          <span style="
            font-family:system-ui,sans-serif; font-size:10px;
            color:{TEAL}; text-transform:uppercase; letter-spacing:0.06em;
            font-weight:700; display:block; margin-bottom:4px;
          ">Proposed solution</span>
          <p style="
            font-family:system-ui,sans-serif; font-size:12px;
            color:{INK}; line-height:1.55; margin:0;
          ">{solution[:240]}{"…" if len(solution) > 240 else ""}</p>
        </div>"""

    link_html = ""
    if url:
        link_html = f"""
        <a href="{url}" style="
          font-family:system-ui,sans-serif; font-size:10px;
          color:{TEAL}; text-decoration:none;
          display:inline-block; margin-top:8px;
        ">View full analysis →</a>"""

    return f"""
    <div style="
      background:{CARD_BG}; border:1px solid {BORDER};
      border-radius:6px; padding:16px 20px;
      margin-bottom:14px; page-break-inside:avoid;
    ">
      <div style="display:flex; align-items:center; margin-bottom:8px;">
        <span style="
          font-family:monospace; font-size:11px; font-weight:700;
          color:{TEAL}; background:{TEAL_LIGHT};
          padding:2px 8px; border-radius:3px; margin-right:10px;
          min-width:22px; text-align:center;
        ">#{idx}</span>
        <span style="
          font-family:Georgia,'Times New Roman',serif;
          font-size:14px; font-weight:700; color:{INK};
        ">{title}</span>
        {opp_html}
      </div>

      <p style="
        font-family:system-ui,-apple-system,Arial,sans-serif;
        font-size:12px; color:{MUTED}; line-height:1.55;
        margin:0 0 10px 0;
      ">{problem[:220]}{"…" if len(problem) > 220 else ""}</p>

      <div style="display:flex; gap:24px; margin-bottom:8px; flex-wrap:wrap;">
        <div>
          <span style="
            font-family:system-ui,sans-serif; font-size:10px;
            color:{MUTED}; text-transform:uppercase; letter-spacing:0.06em;
            display:block; margin-bottom:2px;
          ">Market Size</span>
          <span style="
            font-family:monospace; font-size:12px;
            font-weight:700; color:{INK};
          ">{market_size}</span>
        </div>
        <div>
          <span style="
            font-family:system-ui,sans-serif; font-size:10px;
            color:{MUTED}; text-transform:uppercase; letter-spacing:0.06em;
            display:block; margin-bottom:2px;
          ">Revenue Potential</span>
          <span style="
            font-family:monospace; font-size:12px;
            font-weight:700; color:{INK};
          ">{revenue}</span>
        </div>
        <div>
          <span style="
            font-family:system-ui,sans-serif; font-size:10px;
            color:{MUTED}; text-transform:uppercase; letter-spacing:0.06em;
            display:block; margin-bottom:2px;
          ">Relevance</span>
          {_score_bar(score_pct, width=80)}
        </div>
      </div>

      {solution_html}
      {link_html}
    </div>
    """


def _cover_page(week_number: int, week_start: date, week_end: date, is_pro: bool) -> str:
    tier_badge = (
        f'<span style="font-family:monospace; font-size:11px; font-weight:700; '
        f'color:{TEAL}; background:{TEAL_LIGHT}; padding:3px 10px; border-radius:3px;">PRO</span>'
        if is_pro
        else f'<span style="font-family:monospace; font-size:11px; font-weight:700; '
        f'color:{AMBER}; background:{AMBER_LIGHT}; padding:3px 10px; border-radius:3px;">FREE PREVIEW</span>'
    )

    return f"""
    <div style="
      page-break-after:always;
      background:{BG};
      padding:60px 48px 48px 48px;
      min-height:842px;
      box-sizing:border-box;
      display:flex;
      flex-direction:column;
    ">
      <!-- Wordmark -->
      <div style="margin-bottom:60px;">
        <span style="
          font-family:Georgia,'Times New Roman',serif;
          font-size:22px; font-weight:700; color:{TEAL};
          letter-spacing:-0.01em;
        ">StartInsight</span>
        <span style="
          font-family:system-ui,sans-serif; font-size:12px;
          color:{MUTED}; margin-left:10px;
        ">AI Startup Intelligence</span>
      </div>

      <!-- Hero block -->
      <div style="flex:1; display:flex; flex-direction:column; justify-content:center;">
        <div style="margin-bottom:12px;">{tier_badge}</div>

        <h1 style="
          font-family:Georgia,'Times New Roman',serif;
          font-size:36px; font-weight:400; color:{INK};
          line-height:1.2; letter-spacing:-0.02em;
          margin:0 0 16px 0;
        ">Weekly AI<br>Trend Report</h1>

        <div style="
          font-family:monospace; font-size:13px;
          color:{TEAL}; letter-spacing:0.04em;
          margin-bottom:8px;
        ">Issue #{week_number:03d}</div>

        <div style="
          font-family:system-ui,sans-serif; font-size:13px;
          color:{MUTED};
        ">{week_start.strftime("%-d %b")} – {week_end.strftime("%-d %b %Y")}</div>

        <div style="
          border-top:2px solid {TEAL}; width:48px;
          margin:32px 0;
        "></div>

        <p style="
          font-family:system-ui,sans-serif; font-size:13px;
          color:{MUTED}; line-height:1.6; max-width:420px; margin:0;
        ">
          The top 10 startup opportunities detected across Reddit, Hacker News,
          Product Hunt, and Google Trends — curated by AI, ranked by signal strength.
        </p>
      </div>

      <!-- Footer -->
      <div style="
        border-top:1px solid {BORDER}; padding-top:20px;
        display:flex; justify-content:space-between; align-items:center;
      ">
        <span style="
          font-family:system-ui,sans-serif; font-size:10px; color:{MUTED};
        ">startinsight.co</span>
        <span style="
          font-family:monospace; font-size:10px; color:{MUTED};
        ">{date.today().strftime("%Y")}</span>
      </div>
    </div>
    """


def _upgrade_cta_page() -> str:
    """Paywall page appended to the free version."""
    return f"""
    <div style="
      page-break-before:always;
      background:{BG}; padding:60px 48px;
      min-height:500px; box-sizing:border-box;
      text-align:center;
    ">
      <!-- Blurred teaser cards -->
      <div style="
        background:{CARD_BG}; border:1px solid {BORDER};
        border-radius:6px; padding:16px 20px;
        margin-bottom:8px; filter:blur(3px);
        opacity:0.5;
      ">
        <div style="height:12px; background:{BORDER}; border-radius:3px; width:60%; margin:0 auto 8px auto;"></div>
        <div style="height:8px; background:{BORDER}; border-radius:3px; width:90%; margin:0 auto;"></div>
      </div>
      <div style="
        background:{CARD_BG}; border:1px solid {BORDER};
        border-radius:6px; padding:16px 20px;
        margin-bottom:24px; filter:blur(3px);
        opacity:0.3;
      ">
        <div style="height:12px; background:{BORDER}; border-radius:3px; width:50%; margin:0 auto 8px auto;"></div>
        <div style="height:8px; background:{BORDER}; border-radius:3px; width:80%; margin:0 auto;"></div>
      </div>

      <!-- CTA box -->
      <div style="
        background:{TEAL}; border-radius:8px;
        padding:32px 40px; max-width:480px; margin:0 auto;
      ">
        <h2 style="
          font-family:Georgia,'Times New Roman',serif;
          font-size:22px; font-weight:400;
          color:#FFFFFF; margin:0 0 12px 0;
          line-height:1.3;
        ">Unlock the full analysis</h2>
        <p style="
          font-family:system-ui,sans-serif; font-size:13px;
          color:rgba(255,255,255,0.85); line-height:1.6;
          margin:0 0 20px 0;
        ">
          Pro subscribers get market size estimates, revenue potential,
          proposed solutions, and direct links to every insight.
          <br><br>
          Upgrade for RM&nbsp;49/mo — cancel any time.
        </p>
        <div style="
          font-family:monospace; font-size:13px;
          font-weight:700; color:#FFFFFF;
          background:rgba(255,255,255,0.15);
          padding:10px 24px; border-radius:4px;
          display:inline-block; letter-spacing:0.03em;
        ">startinsight.co/pricing</div>
      </div>
    </div>
    """


def build_weekly_report_html(
    insights: list[dict[str, Any]],
    week_number: int,
    is_pro: bool = False,
) -> str:
    """Build a complete WeasyPrint-compatible HTML document for the weekly report.

    Args:
        insights:    List of insight dicts (same shape as weekly digest task).
        week_number: ISO week number for the issue label.
        is_pro:      If True, renders full-detail cards; if False, renders teaser + CTA.

    Returns:
        HTML string ready for WeasyPrint.
    """
    today = date.today()
    # Week boundaries: Monday → Sunday of the displayed week
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    cover = _cover_page(week_number, week_start, week_end, is_pro)

    section_header = f"""
    <div style="margin-bottom:20px; page-break-after:avoid;">
      <h2 style="
        font-family:Georgia,'Times New Roman',serif;
        font-size:20px; font-weight:400; color:{INK};
        margin:0 0 4px 0;
      ">This week's top trends</h2>
      <p style="
        font-family:system-ui,sans-serif; font-size:12px;
        color:{MUTED}; margin:0;
      ">Ranked by AI signal strength across 6 data sources · Week {week_number}</p>
    </div>
    """

    cards_html = ""
    for idx, insight in enumerate(insights[:10], start=1):
        if is_pro:
            cards_html += _pro_insight_card(idx, insight)
        else:
            cards_html += _free_insight_card(idx, insight)

    cta_html = "" if is_pro else _upgrade_cta_page()

    footer_note = (
        f'<p style="font-family:system-ui,sans-serif; font-size:10px; color:{MUTED}; '
        f'text-align:center; margin-top:32px;">Generated by StartInsight · startinsight.co</p>'
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>StartInsight — Weekly AI Trend Report #{week_number:03d}</title>
  <style>
    @page {{
      size: A4;
      margin: 2cm 2.2cm;
    }}
    body {{
      background: {BG};
      margin: 0;
      padding: 0;
      color: {INK};
    }}
    a {{ color: {TEAL}; }}
  </style>
</head>
<body>
  {cover}

  <div style="padding:8px 0;">
    {section_header}
    {cards_html}
    {cta_html}
    {footer_note}
  </div>
</body>
</html>"""


async def generate_weekly_report_pdf(html: str) -> bytes:
    """Render HTML to PDF bytes using WeasyPrint in a thread pool.

    Mirrors the pattern from report_generator._generate_pdf_bytes.
    WeasyPrint is synchronous — off-loaded to executor to avoid blocking.
    """
    def _render() -> bytes:
        from weasyprint import HTML  # type: ignore[import-untyped]  # noqa: N811
        return HTML(string=html).write_pdf()

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _render)
