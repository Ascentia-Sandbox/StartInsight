"""Export API Routes - Phase 5.3.

Endpoints for exporting insights and analyses in various formats (PDF, CSV, JSON).
"""

import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import PlainTextResponse, Response
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models import CustomAnalysis, Insight, User
from app.services.export_service import (
    ExportFormat,
    export_analysis_csv,
    export_analysis_json,
    export_analysis_pdf,
    export_insight_csv,
    export_insight_pdf,
    get_export_response,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/export", tags=["Export"])


# ============================================================
# Export Response Schemas
# ============================================================


class ExportResponse(BaseModel):
    """Export operation response."""

    format: str
    filename: str
    content_type: str
    content_length: int


# ============================================================
# Insight Export Endpoints
# ============================================================


@router.get("/insight/{insight_id}/pdf")
async def export_insight_as_pdf(
    insight_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    """
    Export a single insight as PDF (HTML format for client-side conversion).

    Requires authentication.
    """
    # Fetch insight
    result = await db.execute(
        select(Insight).where(Insight.id == insight_id)
    )
    insight = result.scalar_one_or_none()

    if not insight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Insight not found",
        )

    # Convert to dict for export
    insight_data = {
        "id": str(insight.id),
        "problem_statement": insight.problem_statement,
        "proposed_solution": insight.proposed_solution,
        "market_size_estimate": insight.market_size_estimate,
        "relevance_score": insight.relevance_score,
        "opportunity_score": insight.opportunity_score,
        "problem_score": insight.problem_score,
        "feasibility_score": insight.feasibility_score,
        "why_now_score": insight.why_now_score,
        "revenue_potential": insight.revenue_potential,
        "execution_difficulty": insight.execution_difficulty,
        "go_to_market_score": insight.go_to_market_score,
        "founder_fit_score": insight.founder_fit_score,
        "competitors": insight.competitors or [],
    }

    html_content = export_insight_pdf(insight_data)

    return Response(
        content=html_content,
        media_type="text/html",
        headers={
            "Content-Disposition": f'attachment; filename="insight-{insight_id}.html"',
        },
    )


@router.get("/insights/csv")
async def export_insights_as_csv(
    min_score: float = Query(default=0.0, ge=0, le=1),
    limit: int = Query(default=100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    """
    Export multiple insights as CSV.

    Requires authentication. Supports filtering by minimum relevance score.
    """
    # Fetch insights
    query = (
        select(Insight)
        .where(Insight.relevance_score >= min_score)
        .order_by(Insight.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(query)
    insights = result.scalars().all()

    # Convert to list of dicts
    insights_data = [
        {
            "id": str(i.id),
            "problem_statement": i.problem_statement,
            "proposed_solution": i.proposed_solution,
            "market_size_estimate": i.market_size_estimate,
            "relevance_score": i.relevance_score,
            "opportunity_score": i.opportunity_score,
            "problem_score": i.problem_score,
            "feasibility_score": i.feasibility_score,
            "why_now_score": i.why_now_score,
            "revenue_potential": i.revenue_potential,
            "execution_difficulty": i.execution_difficulty,
            "go_to_market_score": i.go_to_market_score,
            "founder_fit_score": i.founder_fit_score,
            "created_at": i.created_at.isoformat() if i.created_at else "",
        }
        for i in insights
    ]

    csv_content = export_insight_csv(insights_data)

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="insights-export-{datetime.now().strftime("%Y%m%d")}.csv"',
        },
    )


# ============================================================
# Research Analysis Export Endpoints
# ============================================================


@router.get("/analysis/{analysis_id}/pdf")
async def export_analysis_as_pdf(
    analysis_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    """
    Export a research analysis as PDF (HTML format for client-side conversion).

    Requires authentication. Only exports analyses owned by the current user.
    """
    # Fetch analysis
    result = await db.execute(
        select(CustomAnalysis).where(
            CustomAnalysis.id == analysis_id,
            CustomAnalysis.user_id == current_user.id,
        )
    )
    analysis = result.scalar_one_or_none()

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found or access denied",
        )

    # Convert to dict for export
    analysis_data = {
        "id": str(analysis.id),
        "idea_description": analysis.idea_description,
        "target_market": analysis.target_market,
        "budget_range": analysis.budget_range,
        "status": analysis.status,
        "opportunity_score": analysis.opportunity_score,
        "market_fit_score": analysis.market_fit_score,
        "execution_readiness": analysis.execution_readiness,
        "market_analysis": analysis.market_analysis,
        "competitor_landscape": analysis.competitor_landscape,
        "value_equation": analysis.value_equation,
        "market_matrix": analysis.market_matrix,
        "acp_framework": analysis.acp_framework,
        "validation_signals": analysis.validation_signals,
        "execution_roadmap": analysis.execution_roadmap,
        "risk_assessment": analysis.risk_assessment,
        "created_at": analysis.created_at.isoformat() if analysis.created_at else "",
    }

    html_content = export_analysis_pdf(analysis_data)

    return Response(
        content=html_content,
        media_type="text/html",
        headers={
            "Content-Disposition": f'attachment; filename="analysis-{analysis_id}.html"',
        },
    )


@router.get("/analysis/{analysis_id}/json")
async def export_analysis_as_json(
    analysis_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    """
    Export a research analysis as JSON.

    Requires authentication. Only exports analyses owned by the current user.
    """
    # Fetch analysis
    result = await db.execute(
        select(CustomAnalysis).where(
            CustomAnalysis.id == analysis_id,
            CustomAnalysis.user_id == current_user.id,
        )
    )
    analysis = result.scalar_one_or_none()

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found or access denied",
        )

    # Convert to dict for export
    analysis_data = {
        "id": str(analysis.id),
        "idea_description": analysis.idea_description,
        "target_market": analysis.target_market,
        "budget_range": analysis.budget_range,
        "status": analysis.status,
        "progress_percent": analysis.progress_percent,
        "opportunity_score": analysis.opportunity_score,
        "market_fit_score": analysis.market_fit_score,
        "execution_readiness": analysis.execution_readiness,
        "market_analysis": analysis.market_analysis,
        "competitor_landscape": analysis.competitor_landscape,
        "value_equation": analysis.value_equation,
        "market_matrix": analysis.market_matrix,
        "acp_framework": analysis.acp_framework,
        "validation_signals": analysis.validation_signals,
        "execution_roadmap": analysis.execution_roadmap,
        "risk_assessment": analysis.risk_assessment,
        "created_at": analysis.created_at.isoformat() if analysis.created_at else "",
        "completed_at": analysis.completed_at.isoformat() if analysis.completed_at else None,
    }

    json_content = export_analysis_json(analysis_data)

    return Response(
        content=json_content,
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="analysis-{analysis_id}.json"',
        },
    )


@router.get("/analyses/csv")
async def export_analyses_as_csv(
    status_filter: str | None = Query(default=None, description="Filter by status"),
    limit: int = Query(default=100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    """
    Export multiple research analyses as CSV.

    Requires authentication. Only exports analyses owned by the current user.
    """
    # Build query
    query = (
        select(CustomAnalysis)
        .where(CustomAnalysis.user_id == current_user.id)
        .order_by(CustomAnalysis.created_at.desc())
        .limit(limit)
    )

    if status_filter:
        query = query.where(CustomAnalysis.status == status_filter)

    result = await db.execute(query)
    analyses = result.scalars().all()

    # Convert to list of dicts
    analyses_data = [
        {
            "id": str(a.id),
            "idea_description": a.idea_description,
            "target_market": a.target_market,
            "budget_range": a.budget_range,
            "status": a.status,
            "opportunity_score": a.opportunity_score,
            "market_fit_score": a.market_fit_score,
            "execution_readiness": a.execution_readiness,
            "market_analysis": a.market_analysis,
            "risk_assessment": a.risk_assessment,
            "created_at": a.created_at.isoformat() if a.created_at else "",
        }
        for a in analyses
    ]

    csv_content = export_analysis_csv(analyses_data)

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="analyses-export-{datetime.now().strftime("%Y%m%d")}.csv"',
        },
    )
