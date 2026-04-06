"""Report API Routes — conviction funnel for paid category reports.

Endpoints:
  POST /api/webhooks/stripe/reports      — Stripe webhook (payment_intent.succeeded)
  GET  /api/reports/create-checkout      — Create one-time Stripe Checkout session
  GET  /api/insights/category/{cat}      — Public teaser (3 insights, no auth)
  POST /api/reports/track-view           — Track teaser views (no auth)
  POST /api/admin/reports/{id}/retry     — Admin retry for failed reports
  GET  /api/reports/funnel-stats         — Admin per-channel kill criteria
  GET  /api/reports/weekly-pdf           — Weekly AI Trend Report PDF (free/pro tiers)
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any
from urllib.parse import urlparse
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request, status
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy import desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_optional, require_admin
from app.core.config import settings
from app.db.session import AsyncSessionLocal, get_db
from app.models.insight import Insight
from app.models.report_request import ReportRequest
from app.models.user import User
from app.services.report_generator import (
    CATEGORY_CONFIG,
    generate_report,
    send_confirmation_email,
)
from app.services.weekly_report_pdf import build_weekly_report_html, generate_weekly_report_pdf

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# REQUEST / RESPONSE SCHEMAS
# ============================================================================


class CategoryInsightTeaser(BaseModel):
    """Lightweight insight card for public category teasers."""

    id: UUID
    title: str | None
    problem_statement: str
    proposed_solution: str
    market_size_estimate: str
    relevance_score: float
    opportunity_score: int | None
    revenue_potential: str | None

    model_config = {"from_attributes": True}


class CategoryTeaserResponse(BaseModel):
    """Response for GET /api/insights/category/{category}."""

    category: str
    category_title: str
    category_description: str
    insights: list[CategoryInsightTeaser]
    partial: bool = Field(
        default=False,
        description="True when fewer than 3 insights are available for this category.",
    )


class CheckoutSessionResponse(BaseModel):
    """Response for GET /api/reports/create-checkout."""

    checkout_url: str
    session_id: str


class TrackViewRequest(BaseModel):
    """Body for POST /api/reports/track-view."""

    category: str
    source: str = "direct"
    email: str | None = None


class FunnelChannelStats(BaseModel):
    """Per-channel funnel metrics for kill criteria analysis."""

    source: str
    teaser_views: int
    checkout_starts: int
    payments: int
    conversion_rate_pct: float


class FunnelStatsResponse(BaseModel):
    """Response for GET /api/reports/funnel-stats."""

    by_source: list[FunnelChannelStats]
    total_teaser_views: int
    total_payments: int
    overall_conversion_pct: float


# ============================================================================
# HELPERS
# ============================================================================


def _verify_stripe_signature(payload: bytes, signature: str, secret: str) -> dict[str, Any]:
    """Verify Stripe webhook signature and return the parsed event dict.

    Raises ValueError if signature is invalid or secret is not configured.
    """
    import stripe  # type: ignore[import-untyped]

    if not secret:
        raise ValueError("STRIPE_WEBHOOK_SECRET not configured")

    try:
        event = stripe.Webhook.construct_event(payload, signature, secret)
    except stripe.error.SignatureVerificationError as exc:
        raise ValueError(f"Invalid Stripe signature: {exc}") from exc

    return dict(event)


def _get_stripe_client():
    """Return a configured Stripe module or None if unavailable."""
    try:
        import stripe as _stripe  # type: ignore[import-untyped]

        if not settings.stripe_secret_key:
            return None
        _stripe.api_key = settings.stripe_secret_key
        return _stripe
    except ImportError:
        logger.warning("Stripe package not installed")
        return None


def _validate_url_for_production(url: str, label: str) -> None:
    """Raise ValueError if the URL is unsafe for production usage."""
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise ValueError(f"{label} must use HTTPS in production")
    if ".." in url:
        raise ValueError(f"{label} contains path traversal")
    depth = len(parsed.path.split("/")) if parsed.path else 0
    if depth > 10:
        raise ValueError(f"{label} path depth exceeds maximum")


# ============================================================================
# GET /api/reports/create-checkout
# ============================================================================


@router.get(
    "/api/reports/create-checkout",
    response_model=CheckoutSessionResponse,
    tags=["Reports"],
    summary="Create a one-time Stripe Checkout session for a category report",
)
async def create_report_checkout(
    category: Annotated[
        str,
        Query(description="Report category slug (e.g. fintech-malaysia)"),
    ],
    source: Annotated[
        str,
        Query(description="UTM/acquisition source stored as Stripe session metadata"),
    ] = "direct",
) -> CheckoutSessionResponse:
    """Create a Stripe Checkout Session for a one-time RM 49 category report.

    Public endpoint — no authentication required.

    Query params:
        category: One of the allowed category slugs.
        source:   UTM source string read from sessionStorage by the frontend.

    Returns:
        checkout_url: Stripe-hosted checkout page URL.
        session_id:   Stripe session ID.
    """
    if category not in CATEGORY_CONFIG:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unknown category '{category}'. Allowed: {sorted(CATEGORY_CONFIG.keys())}",
        )

    base = settings.app_url.rstrip("/")
    success_url = f"{base}/reports/{category}?success=true"
    cancel_url = f"{base}/reports/{category}"

    if settings.environment == "production":
        try:
            _validate_url_for_production(success_url, "success_url")
            _validate_url_for_production(cancel_url, "cancel_url")
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(exc),
            ) from exc

    stripe = _get_stripe_client()

    if not stripe or not settings.stripe_secret_key:
        if settings.environment == "production":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Payment service unavailable — Stripe not configured",
            )
        # Development mock
        logger.warning("Stripe not configured — returning mock checkout URL (development only)")
        return CheckoutSessionResponse(
            checkout_url=success_url,
            session_id="mock_session_report",
        )

    # Use dedicated report price ID; fall back to stripe_price_starter
    price_id: str | None = getattr(settings, "stripe_price_report", None)
    if not price_id:
        price_id = settings.stripe_price_starter  # type: ignore[assignment]

    if not price_id:
        logger.error(
            "No Stripe price ID configured for report checkout "
            "(set STRIPE_PRICE_REPORT or STRIPE_PRICE_STARTER)"
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment service configuration error",
        )

    try:
        session = stripe.checkout.Session.create(
            mode="payment",
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "category": category,
                "source": source,
                "product": "category_report",
            },
        )

        logger.info(
            "Created report checkout session",
            extra={
                "category": category,
                "source": source,
                "session_id": session.id,
            },
        )

        return CheckoutSessionResponse(
            checkout_url=session.url,
            session_id=session.id,
        )

    except Exception as exc:
        logger.exception("Failed to create Stripe report checkout session: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create checkout session",
        ) from exc


# ============================================================================
# STRIPE WEBHOOK — reports
# ============================================================================


@router.post("/api/webhooks/stripe/reports", tags=["Reports"])
async def stripe_reports_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Handle Stripe payment_intent.succeeded for category report purchases.

    Security: verifies Stripe webhook signature before processing.
    Idempotency: skips duplicate payment_intent IDs already in report_requests.
    Side-effects: creates ReportRequest, sends confirmation email, launches
    background report generation.
    """
    payload = await request.body()
    signature = request.headers.get("stripe-signature", "")

    # Verify signature
    try:
        event = _verify_stripe_signature(payload, signature, settings.stripe_webhook_secret or "")
    except ValueError as exc:
        logger.warning(f"[reports-webhook] signature verification failed: {exc}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    event_type: str = event.get("type", "")
    if event_type != "payment_intent.succeeded":
        # Acknowledge non-target events without processing
        return {"status": "ignored", "event_type": event_type}

    pi_data: dict[str, Any] = event.get("data", {}).get("object", {})
    payment_intent_id: str = pi_data.get("id", "")
    email: str = pi_data.get("receipt_email") or pi_data.get("metadata", {}).get("email", "") or ""
    metadata: dict[str, str] = pi_data.get("metadata", {})
    category: str = metadata.get("category", "")
    source: str = metadata.get("source", "direct")

    if not payment_intent_id or not email or not category:
        logger.warning(
            f"[reports-webhook] missing required fields pi={payment_intent_id} "
            f"email={bool(email)} category={bool(category)}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing payment_intent id, email, or category in event payload",
        )

    if category not in CATEGORY_CONFIG:
        logger.warning(f"[reports-webhook] unknown category={category}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown category: {category}",
        )

    # Idempotency check
    existing_result = await db.execute(
        select(ReportRequest).where(ReportRequest.stripe_payment_intent_id == payment_intent_id)
    )
    if existing_result.scalar_one_or_none() is not None:
        logger.info(f"[reports-webhook] duplicate pi={payment_intent_id} — skipped")
        return {"status": "duplicate", "payment_intent_id": payment_intent_id}

    # Create ReportRequest
    report_req = ReportRequest(
        stripe_payment_intent_id=payment_intent_id,
        category=category,
        email=email,
        source=source,
        status="pending",
        paid_at=datetime.now(UTC),
    )
    db.add(report_req)
    await db.commit()
    await db.refresh(report_req)

    logger.info(
        f"[reports-webhook] created report_request id={report_req.id} "
        f"category={category} pi={payment_intent_id}"
    )

    # Send confirmation email immediately (fire-and-forget in background)
    background_tasks.add_task(send_confirmation_email, email, category)

    # Launch report generation pipeline
    background_tasks.add_task(
        _run_generate_report_background,
        category=category,
        payment_intent_id=payment_intent_id,
        email=email,
    )

    return {"status": "accepted", "report_request_id": str(report_req.id)}


async def _run_generate_report_background(
    category: str,
    payment_intent_id: str,
    email: str,
) -> None:
    """Create a fresh DB session and run the report generation pipeline.

    BackgroundTasks execute after the request response is sent, so we must
    open a new AsyncSession rather than reusing the request-scoped one.
    """
    async with AsyncSessionLocal() as db:
        await generate_report(
            category=category,
            payment_intent_id=payment_intent_id,
            email=email,
            db=db,
        )


# ============================================================================
# PUBLIC: category teaser
# ============================================================================


@router.get(
    "/api/insights/category/{category}",
    response_model=CategoryTeaserResponse,
    tags=["Reports"],
)
async def get_category_insights_teaser(
    category: str,
    db: AsyncSession = Depends(get_db),
) -> CategoryTeaserResponse:
    """Return up to 3 high-scoring insights for a category as a public teaser.

    Used on the category landing page to demonstrate content quality before
    the visitor proceeds to Stripe Checkout. No authentication required.
    """
    if category not in CATEGORY_CONFIG:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category '{category}' not found. Valid: {list(CATEGORY_CONFIG.keys())}",
        )

    cfg = CATEGORY_CONFIG[category]

    # Map category slug to search keywords (insights table has no "category" column)
    category_keywords: dict[str, list[str]] = {
        "fintech-malaysia": ["fintech", "payment", "banking", "Malaysia", "lending"],
        "fnb-malaysia": ["food", "beverage", "F&B", "restaurant", "Malaysia"],
        "logistics-singapore": ["logistics", "supply chain", "shipping", "Singapore"],
    }
    keywords = category_keywords.get(category, [category.replace("-", " ")])
    keyword_filters = []
    for kw in keywords:
        pattern = f"%{kw}%"
        keyword_filters.append(Insight.title.ilike(pattern))
        keyword_filters.append(Insight.problem_statement.ilike(pattern))
        keyword_filters.append(Insight.proposed_solution.ilike(pattern))

    result = await db.execute(
        select(Insight)
        .where(
            or_(*keyword_filters),
            Insight.relevance_score >= 0.5,
        )
        .order_by(Insight.relevance_score.desc())
        .limit(3)
    )
    insights = result.scalars().all()

    teasers = [
        CategoryInsightTeaser(
            id=ins.id,
            title=getattr(ins, "title", None),
            problem_statement=ins.problem_statement,
            proposed_solution=ins.proposed_solution,
            market_size_estimate=ins.market_size_estimate,
            relevance_score=ins.relevance_score,
            opportunity_score=getattr(ins, "opportunity_score", None),
            revenue_potential=getattr(ins, "revenue_potential", None),
        )
        for ins in insights
    ]

    return CategoryTeaserResponse(
        category=category,
        category_title=cfg["title"],
        category_description=cfg["description"],
        insights=teasers,
        partial=len(teasers) < 3,
    )


# ============================================================================
# PUBLIC: track teaser view
# ============================================================================


@router.post("/api/reports/track-view", tags=["Reports"])
async def track_report_teaser_view(
    body: TrackViewRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Log a teaser page view for funnel analytics.

    If an email is provided and a pending ReportRequest already exists for
    this (category, email) pair, we update teaser_viewed_at.
    No authentication required.
    """
    if body.category not in CATEGORY_CONFIG:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown category: {body.category}",
        )

    if body.email:
        result = await db.execute(
            select(ReportRequest)
            .where(
                ReportRequest.category == body.category,
                ReportRequest.email == body.email,
                ReportRequest.teaser_viewed_at.is_(None),
            )
            .order_by(ReportRequest.created_at.desc())
            .limit(1)
        )
        existing = result.scalar_one_or_none()
        if existing:
            existing.teaser_viewed_at = datetime.now(UTC)
            await db.commit()

    logger.info(f"[reports] teaser viewed category={body.category} source={body.source}")
    return {"status": "ok"}


# ============================================================================
# ADMIN: retry failed report
# ============================================================================


@router.post(
    "/api/admin/reports/{report_id}/retry",
    tags=["Admin", "Reports"],
)
async def retry_failed_report(
    report_id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    _admin: Any = Depends(require_admin),
) -> dict[str, str]:
    """Re-launch the report generation pipeline for a failed report.

    Requires admin authentication. Only allowed when report status is 'failed'.
    """
    result = await db.execute(select(ReportRequest).where(ReportRequest.id == report_id))
    report_req = result.scalar_one_or_none()

    if report_req is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ReportRequest {report_id} not found",
        )

    if report_req.status != "failed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot retry report in status '{report_req.status}' — must be 'failed'",
        )

    logger.info(
        f"[reports] admin retry report_id={report_id} "
        f"failed_step={report_req.failed_step} category={report_req.category}"
    )

    # Reset status so pipeline restarts from the top
    report_req.status = "pending"
    report_req.failed_step = None
    await db.commit()

    background_tasks.add_task(
        _run_generate_report_background,
        category=report_req.category,
        payment_intent_id=report_req.stripe_payment_intent_id,
        email=report_req.email,
    )

    return {"status": "retry_launched", "report_request_id": str(report_id)}


# ============================================================================
# ADMIN: funnel kill criteria stats
# ============================================================================


@router.get(
    "/api/reports/funnel-stats",
    response_model=FunnelStatsResponse,
    tags=["Admin", "Reports"],
)
async def get_funnel_stats(
    db: AsyncSession = Depends(get_db),
    _admin: Any = Depends(require_admin),
) -> FunnelStatsResponse:
    """Return per-channel funnel stats for kill criteria analysis.

    Aggregates teaser views, checkout starts, and paid conversions broken down
    by source (pdf / seo / direct). Requires admin authentication.
    """
    rows_result = await db.execute(
        select(
            ReportRequest.source,
            func.count(ReportRequest.id).label("total"),
            func.count(ReportRequest.teaser_viewed_at).label("teaser_views"),
            func.count(ReportRequest.checkout_started_at).label("checkout_starts"),
            func.count(ReportRequest.paid_at).label("payments"),
        )
        .group_by(ReportRequest.source)
        .order_by(func.count(ReportRequest.paid_at).desc())
    )
    rows = rows_result.all()

    by_source: list[FunnelChannelStats] = []
    total_teaser_views = 0
    total_payments = 0

    for row in rows:
        teaser = int(row.teaser_views or 0)
        checkouts = int(row.checkout_starts or 0)
        payments = int(row.payments or 0)
        conversion = round(payments / teaser * 100, 1) if teaser > 0 else 0.0

        by_source.append(
            FunnelChannelStats(
                source=row.source,
                teaser_views=teaser,
                checkout_starts=checkouts,
                payments=payments,
                conversion_rate_pct=conversion,
            )
        )
        total_teaser_views += teaser
        total_payments += payments

    overall_conversion = (
        round(total_payments / total_teaser_views * 100, 1) if total_teaser_views > 0 else 0.0
    )

    return FunnelStatsResponse(
        by_source=by_source,
        total_teaser_views=total_teaser_views,
        total_payments=total_payments,
        overall_conversion_pct=overall_conversion,
    )


# ============================================================================
# WEEKLY PDF REPORT
# ============================================================================


@router.get(
    "/api/reports/weekly-pdf",
    tags=["Reports"],
    summary="Download the weekly AI Trend Report as a branded PDF",
    responses={
        200: {
            "content": {"application/pdf": {}},
            "description": "PDF file — free (top 10 summaries) or pro (full analysis)",
        }
    },
)
async def get_weekly_pdf_report(
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> Response:
    """Generate and return the weekly AI Trend Report as a downloadable PDF.

    - Unauthenticated / free-tier users receive the teaser PDF (top 10 summaries
      with a paywall CTA page).
    - Pro / enterprise users receive the full-detail PDF (market size, revenue
      potential, opportunity score, proposed solution).

    The top 10 insights are the same set used by the Monday weekly digest email,
    ranked by relevance_score from the past 7 days (falls back to all-time top 10
    if no insights were published this week).
    """
    is_pro = current_user is not None and current_user.subscription_tier in (
        "pro",
        "enterprise",
        "api",
    )

    # Fetch top 10 insights — same query as weekly digest task
    one_week_ago = datetime.now(UTC) - timedelta(days=7)
    result = await db.execute(
        select(Insight)
        .where(Insight.created_at >= one_week_ago)
        .order_by(desc(Insight.relevance_score))
        .limit(10)
    )
    insights = result.scalars().all()

    # Fallback: if no insights published this week, use all-time top 10
    if not insights:
        result = await db.execute(select(Insight).order_by(desc(Insight.relevance_score)).limit(10))
        insights = result.scalars().all()

    if not insights:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No insights available to generate report",
        )

    # Build insight dicts matching the weekly digest shape
    today = datetime.now(UTC).date()
    week_number = today.isocalendar()[1]
    _utm = "utm_source=pdf&utm_medium=report&utm_campaign=weekly_pdf"

    insight_list = [
        {
            "title": ins.title or (ins.proposed_solution or "")[:80],
            "problem_statement": ins.problem_statement or "",
            "relevance_score": f"{(ins.relevance_score or 0) * 100:.0f}%",
            "market_size": ins.market_size_estimate or "—",
            "revenue_potential": getattr(ins, "revenue_potential", None) or "—",
            "opportunity_score": getattr(ins, "opportunity_score", None),
            "proposed_solution": ins.proposed_solution or "",
            "insight_url": f"https://startinsight.co/insights/{ins.id}?{_utm}",
        }
        for ins in insights
    ]

    try:
        html = build_weekly_report_html(insight_list, week_number, is_pro=is_pro)
        pdf_bytes = await generate_weekly_report_pdf(html)
    except Exception:
        logger.exception("[weekly-pdf] PDF generation failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="PDF generation failed — please try again",
        )

    filename = f"startinsight-weekly-{today.isoformat()}-{'pro' if is_pro else 'preview'}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
