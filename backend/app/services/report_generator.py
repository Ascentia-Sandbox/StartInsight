"""Report generation pipeline service for the conviction funnel.

Orchestrates the full lifecycle of a paid category report:
  pending → generating → rendered → delivered

Each step is wrapped with Sentry tracing and fail-safe error handling.
Gemini calls use tenacity retry (3 attempts, exponential backoff) for 429s.
WeasyPrint failure falls back to plain-text email delivery.
"""

from __future__ import annotations

import asyncio
import base64
import logging
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field
from pydantic_ai import Agent
from sqlalchemy import select, text, update
from sqlalchemy.ext.asyncio import AsyncSession
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.models.insight import Insight
from app.models.report_request import ReportRequest
from app.services.email_service import send_email

logger = logging.getLogger(__name__)


# ============================================================================
# CATEGORY CONFIGURATION
# ============================================================================

CATEGORY_CONFIG: dict[str, dict[str, str]] = {
    "fintech-malaysia": {
        "title": "Fintech Malaysia",
        "description": "AI-powered analysis of fintech market gaps in Malaysia",
    },
    "fnb-malaysia": {
        "title": "F&B Malaysia",
        "description": "AI-powered analysis of food & beverage market gaps in Malaysia",
    },
    "logistics-singapore": {
        "title": "Logistics Singapore",
        "description": "AI-powered analysis of logistics market gaps in Singapore",
    },
}


# ============================================================================
# PYDANTIC SCHEMAS
# ============================================================================


class ReportSection(BaseModel):
    """A single section within the generated report."""

    heading: str = Field(description="Section heading (max 80 chars)")
    body: str = Field(description="Section body with analysis (200-400 words)")
    key_takeaway: str = Field(description="One-sentence takeaway for founders (max 120 chars)")


class CategoryReportContent(BaseModel):
    """Structured output from Gemini for a category report.

    Five sections covering the full founder decision surface.
    """

    executive_summary: str = Field(
        description="2-3 paragraph executive summary of the market opportunity"
    )
    demand_signals: ReportSection = Field(
        description="Quantified demand signals and user pain points from raw data"
    )
    underserved_niche: ReportSection = Field(
        description="The most underserved niche within this category and why"
    )
    competitor_map: ReportSection = Field(
        description="Current competitive landscape: who is winning, who is losing, why"
    )
    customer_pain_points: ReportSection = Field(
        description="Top 3-5 customer pain points with evidence from market signals"
    )
    first_wedge: ReportSection = Field(
        description="Recommended first-wedge entry point for a new founder"
    )


# ============================================================================
# AI AGENT
# ============================================================================

_report_agent = Agent(
    model="google-gla:gemini-2.0-flash",
    output_type=CategoryReportContent,
    system_prompt="""You are a senior market analyst specialising in Southeast Asia startup ecosystems.

Your task is to synthesise raw market signals into an actionable investor-grade category report.

Rules:
- Every claim must include a specific data point or signal reference.
- Write for a technical founder who can execute, not a generalist investor.
- Be specific about geography, timing, and customer segment.
- No marketing fluff. No vague "there is opportunity" statements.
- Use plain, direct language. Short paragraphs (3-4 sentences max).
- Sections should be 200-400 words of substantive analysis.
""",
)


# ============================================================================
# RETRY HELPERS
# ============================================================================


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=5, max=30),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
async def _run_report_agent_with_retry(prompt: str) -> CategoryReportContent:
    """Call Gemini via PydanticAI with retry on 429 / transient errors."""
    result = await asyncio.wait_for(_report_agent.run(prompt), timeout=120)
    return result.output


# ============================================================================
# HTML TEMPLATE
# ============================================================================


def _build_report_html(
    category_title: str,
    category_description: str,
    content: CategoryReportContent,
    generated_date: str,
) -> str:
    """Render a WeasyPrint-compatible HTML report with inline CSS.

    Uses system-ui as the body font fallback (WeasyPrint cannot load web fonts).
    Brand colour: teal #0D7377.
    """

    def render_section(section: ReportSection, section_number: int) -> str:
        return f"""
        <div style="margin-bottom: 32px; page-break-inside: avoid;">
            <h2 style="
                font-family: Georgia, 'Times New Roman', serif;
                font-size: 18px;
                font-weight: 700;
                color: #0D7377;
                border-bottom: 2px solid #0D7377;
                padding-bottom: 6px;
                margin-bottom: 12px;
            ">{section_number}. {section.heading}</h2>
            <p style="
                font-family: system-ui, -apple-system, Arial, sans-serif;
                font-size: 13px;
                line-height: 1.7;
                color: #1a1a1a;
                margin: 0 0 12px 0;
                white-space: pre-line;
            ">{section.body}</p>
            <div style="
                background: #f0fafa;
                border-left: 4px solid #0D7377;
                padding: 10px 14px;
                border-radius: 0 4px 4px 0;
            ">
                <p style="
                    font-family: system-ui, -apple-system, Arial, sans-serif;
                    font-size: 12px;
                    font-weight: 600;
                    color: #0D7377;
                    margin: 0;
                ">Key Takeaway: {section.key_takeaway}</p>
            </div>
        </div>
        """

    sections_html = "".join(
        [
            render_section(content.demand_signals, 1),
            render_section(content.underserved_niche, 2),
            render_section(content.competitor_map, 3),
            render_section(content.customer_pain_points, 4),
            render_section(content.first_wedge, 5),
        ]
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <title>{category_title} Market Report — StartInsight</title>
    <style>
        @page {{
            margin: 2cm 2.5cm;
            size: A4;
            @bottom-center {{
                content: "StartInsight — " string(category) " — Confidential";
                font-size: 9px;
                color: #9ca3af;
            }}
            @top-right {{
                content: counter(page) " / " counter(pages);
                font-size: 9px;
                color: #9ca3af;
            }}
        }}
        body {{
            font-family: system-ui, -apple-system, Arial, sans-serif;
            font-size: 13px;
            line-height: 1.6;
            color: #1a1a1a;
            margin: 0;
            padding: 0;
        }}
    </style>
</head>
<body>

    <!-- HEADER -->
    <div style="
        border-bottom: 3px solid #0D7377;
        padding-bottom: 20px;
        margin-bottom: 28px;
    ">
        <div style="
            font-family: system-ui, -apple-system, Arial, sans-serif;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 2px;
            text-transform: uppercase;
            color: #0D7377;
            margin-bottom: 8px;
        ">StartInsight Market Intelligence</div>

        <h1 style="
            font-family: Georgia, 'Times New Roman', serif;
            font-size: 28px;
            font-weight: 700;
            color: #0a0a0a;
            margin: 0 0 8px 0;
            line-height: 1.2;
        ">{category_title}</h1>

        <p style="
            font-family: system-ui, -apple-system, Arial, sans-serif;
            font-size: 14px;
            color: #4b5563;
            margin: 0 0 12px 0;
        ">{category_description}</p>

        <div style="
            font-family: system-ui, -apple-system, Arial, sans-serif;
            font-size: 11px;
            color: #9ca3af;
        ">Generated {generated_date} &nbsp;&middot;&nbsp; Confidential &nbsp;&middot;&nbsp; startinsight.co</div>
    </div>

    <!-- EXECUTIVE SUMMARY -->
    <div style="
        background: #f9fafb;
        border: 1px solid #e5e7eb;
        border-radius: 6px;
        padding: 20px 24px;
        margin-bottom: 32px;
    ">
        <h2 style="
            font-family: Georgia, 'Times New Roman', serif;
            font-size: 16px;
            font-weight: 700;
            color: #0a0a0a;
            margin: 0 0 12px 0;
        ">Executive Summary</h2>
        <p style="
            font-family: system-ui, -apple-system, Arial, sans-serif;
            font-size: 13px;
            line-height: 1.7;
            color: #1a1a1a;
            margin: 0;
            white-space: pre-line;
        ">{content.executive_summary}</p>
    </div>

    <!-- REPORT SECTIONS -->
    {sections_html}

    <!-- FOOTER CTA -->
    <div style="
        margin-top: 40px;
        border-top: 2px solid #e5e7eb;
        padding-top: 20px;
        text-align: center;
    ">
        <p style="
            font-family: system-ui, -apple-system, Arial, sans-serif;
            font-size: 13px;
            color: #4b5563;
            margin: 0 0 8px 0;
        ">Want more category reports and daily signals?</p>
        <p style="
            font-family: system-ui, -apple-system, Arial, sans-serif;
            font-size: 13px;
            font-weight: 600;
            color: #0D7377;
            margin: 0;
        ">Visit startinsight.co to explore 500+ curated startup opportunities.</p>
        <p style="
            font-family: system-ui, -apple-system, Arial, sans-serif;
            font-size: 11px;
            color: #9ca3af;
            margin-top: 16px;
        ">This report is for personal use only. Do not distribute without permission.</p>
    </div>

</body>
</html>"""


# ============================================================================
# PDF GENERATION
# ============================================================================


async def _generate_pdf_bytes(html: str) -> bytes:
    """Render HTML to PDF bytes using WeasyPrint in a thread pool.

    WeasyPrint is synchronous — run it in asyncio's default executor to avoid
    blocking the event loop.
    """

    def _render() -> bytes:
        from weasyprint import HTML  # type: ignore[import-untyped]

        return HTML(string=html).write_pdf()

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _render)


# ============================================================================
# EMAIL DELIVERY WITH PDF ATTACHMENT
# ============================================================================


async def _send_report_email(
    email: str,
    category_title: str,
    report_html: str,
    pdf_bytes: bytes | None,
    plain_text_fallback: str | None = None,
) -> dict[str, Any]:
    """Send the completed report via Resend with optional PDF attachment.

    If pdf_bytes is None (WeasyPrint failed), we fall back to embedding the
    report HTML directly in the email body and setting a note explaining it.

    Returns a dict with status and optional message id.
    """
    from app.core.config import settings

    resend_client = None
    try:
        import resend

        resend.api_key = settings.resend_api_key
        resend_client = resend
    except ImportError:
        logger.warning("resend not installed — report email skipped")
        return {"status": "skipped", "reason": "resend_not_installed"}

    if not settings.resend_api_key:
        logger.warning("RESEND_API_KEY not set — report email skipped")
        return {"status": "skipped", "reason": "not_configured"}

    subject = f"Your {category_title} Report is Ready — StartInsight"

    if pdf_bytes:
        # PDF delivery path
        html_body = f"""
        <div style="font-family: system-ui, -apple-system, Arial, sans-serif; max-width: 600px; margin: 0 auto; color: #1a1a1a;">
            <div style="border-bottom: 3px solid #0D7377; padding-bottom: 16px; margin-bottom: 24px;">
                <p style="font-size: 11px; font-weight: 700; letter-spacing: 2px; text-transform: uppercase; color: #0D7377; margin: 0 0 8px 0;">StartInsight</p>
                <h1 style="font-family: Georgia, serif; font-size: 24px; color: #0a0a0a; margin: 0;">Your {category_title} Report is Ready</h1>
            </div>
            <p style="font-size: 14px; line-height: 1.6;">Your paid market intelligence report is attached as a PDF.</p>
            <p style="font-size: 14px; line-height: 1.6;">The report covers:</p>
            <ul style="font-size: 14px; line-height: 1.8; color: #374151;">
                <li>Demand signals and quantified pain points</li>
                <li>The most underserved niche in this market</li>
                <li>Competitive landscape analysis</li>
                <li>Customer pain points with evidence</li>
                <li>Recommended first-wedge entry strategy</li>
            </ul>
            <p style="font-size: 14px; line-height: 1.6;">Open the attached PDF on any device.</p>
            <div style="margin-top: 24px; padding: 16px; background: #f0fafa; border-left: 4px solid #0D7377; border-radius: 0 4px 4px 0;">
                <p style="font-size: 13px; color: #0D7377; font-weight: 600; margin: 0;">Want more reports?</p>
                <p style="font-size: 13px; color: #4b5563; margin: 8px 0 0 0;">Visit <a href="https://startinsight.co" style="color: #0D7377;">startinsight.co</a> to explore 500+ curated startup opportunities.</p>
            </div>
            <p style="font-size: 12px; color: #9ca3af; margin-top: 24px;">This report is for personal use only. Do not distribute without permission.</p>
        </div>
        """
        pdf_b64 = base64.b64encode(pdf_bytes).decode("utf-8")
        params: dict[str, Any] = {
            "from": f"{settings.email_from_name} <{settings.email_from_address}>",
            "to": [email],
            "subject": subject,
            "html": html_body,
            "attachments": [
                {
                    "filename": f"startinsight-{category_title.lower().replace(' ', '-')}-report.pdf",
                    "content": pdf_b64,
                    "content_type": "application/pdf",
                }
            ],
        }
    else:
        # Plain-text fallback when WeasyPrint failed
        html_body = plain_text_fallback or report_html
        params = {
            "from": f"{settings.email_from_name} <{settings.email_from_address}>",
            "to": [email],
            "subject": subject,
            "html": html_body,
        }

    try:
        response = await asyncio.to_thread(resend_client.Emails.send, params)
        return {"status": "sent", "id": response.get("id")}
    except Exception as exc:
        logger.error(f"Resend send failed: {exc}")
        return {"status": "error", "error": str(exc)}


# ============================================================================
# CORE PIPELINE
# ============================================================================


async def generate_report(
    category: str,
    payment_intent_id: str,
    email: str,
    db: AsyncSession,
) -> None:
    """Run the full report generation pipeline for one ReportRequest.

    Steps:
        1. Mark status → generating
        2. Fetch top 10 insights for category (score >= 7.0)
        3. Call Gemini 2.0 Flash via PydanticAI (with retry)
        4. Mark status → rendered, store report_html
        5. Generate PDF with WeasyPrint
        6. Send email via Resend (PDF attachment or plain-text fallback)
        7. Mark status → delivered, set report_delivered_at

    Each step is wrapped in try/except. On failure: status → failed, failed_step set.
    Sentry spans wrap the AI call and email delivery.
    """
    import sentry_sdk

    category_cfg = CATEGORY_CONFIG.get(category, {})
    category_title = category_cfg.get("title", category)
    category_description = category_cfg.get("description", "")

    # Helper: update report_request row
    async def _set_status(
        status: str,
        *,
        failed_step: str | None = None,
        report_html: str | None = None,
        report_delivered_at: datetime | None = None,
    ) -> None:
        values: dict[str, Any] = {"status": status, "updated_at": datetime.now(UTC)}
        if failed_step is not None:
            values["failed_step"] = failed_step
        if report_html is not None:
            values["report_html"] = report_html
        if report_delivered_at is not None:
            values["report_delivered_at"] = report_delivered_at
        await db.execute(
            update(ReportRequest)
            .where(ReportRequest.stripe_payment_intent_id == payment_intent_id)
            .values(**values)
        )
        await db.commit()

    # ── Step 1: Mark generating ───────────────────────────────────────────
    try:
        await _set_status("generating")
        logger.info(f"[report] started generation category={category} pi={payment_intent_id}")
    except Exception as exc:
        logger.error(f"[report] failed to set generating status: {exc}")
        return  # Cannot proceed without DB write

    # ── Step 2: Fetch insights ────────────────────────────────────────────
    try:
        result = await db.execute(
            select(Insight)
            .where(
                text("category ILIKE :cat").bindparams(cat=f"%{category}%"),
                Insight.relevance_score >= 7.0,
            )
            .order_by(Insight.relevance_score.desc())
            .limit(10)
        )
        insights = result.scalars().all()
        logger.info(f"[report] fetched {len(insights)} insights for category={category}")
    except Exception as exc:
        logger.error(f"[report] failed to fetch insights: {exc}", exc_info=True)
        await _set_status("failed", failed_step="db_fetch")
        return

    # Build a compact signal summary for the LLM prompt
    signal_lines: list[str] = []
    for ins in insights:
        title = getattr(ins, "title", None) or ins.proposed_solution[:80]
        score = ins.relevance_score
        problem = ins.problem_statement[:200]
        market = ins.market_size_estimate
        signal_lines.append(f"- [{score:.1f}] {title} | Market: {market} | Problem: {problem}")

    signals_block = (
        "\n".join(signal_lines)
        if signal_lines
        else "(no signals found — synthesise from general knowledge of this market)"
    )

    prompt = f"""Generate a structured market intelligence report for the following category:

Category: {category_title}
Description: {category_description}

Market signals (top {len(insights)} by relevance score):
{signals_block}

Produce a thorough, data-driven report following the output schema.
Ground every claim in the signals above where possible.
"""

    # ── Step 3: Call Gemini ───────────────────────────────────────────────
    content: CategoryReportContent | None = None
    try:
        with sentry_sdk.start_span(op="gen_ai.request", description="report_generation") as span:
            span.set_data("category", category)
            span.set_data("signal_count", len(insights))
            content = await _run_report_agent_with_retry(prompt)
        logger.info(f"[report] Gemini generation complete category={category}")
    except Exception as exc:
        logger.error(f"[report] Gemini call failed: {exc}", exc_info=True)
        await _set_status("failed", failed_step="gemini")
        return

    # ── Step 4: Build HTML, mark rendered ─────────────────────────────────
    generated_date = datetime.now(UTC).strftime("%B %d, %Y")
    report_html = _build_report_html(
        category_title=category_title,
        category_description=category_description,
        content=content,
        generated_date=generated_date,
    )
    try:
        await _set_status("rendered", report_html=report_html)
        logger.info(f"[report] HTML rendered category={category}")
    except Exception as exc:
        logger.error(f"[report] failed to store rendered HTML: {exc}", exc_info=True)
        await _set_status("failed", failed_step="db_render")
        return

    # ── Step 5: Generate PDF ──────────────────────────────────────────────
    pdf_bytes: bytes | None = None
    try:
        pdf_bytes = await _generate_pdf_bytes(report_html)
        logger.info(f"[report] PDF generated ({len(pdf_bytes)} bytes) category={category}")
    except Exception as exc:
        # Non-fatal: fall back to plain-text email delivery
        logger.warning(f"[report] WeasyPrint failed — falling back to HTML email: {exc}")
        pdf_bytes = None

    # ── Step 6: Send email ─────────────────────────────────────────────────
    plain_text_fallback: str | None = None
    if pdf_bytes is None:
        # Build a readable plain-HTML fallback version of the report body
        plain_text_fallback = report_html

    send_result: dict[str, Any] = {"status": "error"}
    for attempt in range(1, 3):  # Retry up to 2 times
        try:
            with sentry_sdk.start_span(op="email.send", description="report_delivery") as span:
                span.set_data("category", category)
                span.set_data("email", email)
                span.set_data("has_pdf", pdf_bytes is not None)
                send_result = await _send_report_email(
                    email=email,
                    category_title=category_title,
                    report_html=report_html,
                    pdf_bytes=pdf_bytes,
                    plain_text_fallback=plain_text_fallback,
                )
            if send_result.get("status") in ("sent", "skipped"):
                break
            logger.warning(f"[report] email attempt {attempt} failed: {send_result}")
        except Exception as exc:
            logger.warning(f"[report] email attempt {attempt} exception: {exc}")
            send_result = {"status": "error", "error": str(exc)}

    if send_result.get("status") not in ("sent", "skipped"):
        logger.error(f"[report] email delivery failed after retries: {send_result}")
        await _set_status("failed", failed_step="resend")
        return

    # ── Step 7: Mark delivered ─────────────────────────────────────────────
    try:
        await _set_status("delivered", report_delivered_at=datetime.now(UTC))
        logger.info(f"[report] delivered category={category} pi={payment_intent_id}")
    except Exception as exc:
        logger.error(f"[report] failed to mark delivered: {exc}", exc_info=True)
        # Not critical — report was sent; log but don't re-fail


# ============================================================================
# CONFIRMATION EMAIL
# ============================================================================


async def send_confirmation_email(email: str, category: str) -> dict[str, Any]:
    """Send immediate post-payment confirmation email.

    Tells the buyer their report is being generated and will arrive within 15 minutes.
    Uses the 'report_confirmation' template.
    """
    category_cfg = CATEGORY_CONFIG.get(category, {})
    category_title = category_cfg.get("title", category)

    return await send_email(
        to=email,
        template="report_confirmation",
        variables={
            "category_title": category_title,
            "eta_minutes": "15",
        },
    )
