"""API endpoints for Tools directory (Phase 12.3: IdeaBrowser Replication).

Provides CRUD operations for the 54-tool startup resource directory.
"""

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AdminUser
from app.db.session import get_db
from app.models.tool import Tool
from app.schemas.public_content import (
    ToolCreate,
    ToolListResponse,
    ToolResponse,
    ToolUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tools", tags=["tools"])


@router.get("", response_model=ToolListResponse)
async def list_tools(
    category: Annotated[
        str | None, Query(description="Filter by category")
    ] = None,
    pricing: Annotated[
        str | None, Query(description="Filter by pricing (Free, Freemium, Paid)")
    ] = None,
    featured: Annotated[
        bool | None, Query(description="Filter by featured status")
    ] = None,
    search: Annotated[
        str | None, Query(description="Search by name or tagline")
    ] = None,
    limit: Annotated[int, Query(ge=1, le=100, description="Number of results")] = 12,
    offset: Annotated[int, Query(ge=0, description="Pagination offset")] = 0,
    db: AsyncSession = Depends(get_db),
) -> ToolListResponse:
    """
    List all tools with filtering and pagination.

    - **category**: Filter by tool category (e.g., 'Payments', 'No-Code')
    - **pricing**: Filter by pricing type (Free, Freemium, Paid)
    - **featured**: Filter by featured status
    - **search**: Search in name and tagline
    - **limit**: Number of results per page (default 12, max 100)
    - **offset**: Pagination offset
    """
    # Build query
    query = select(Tool)

    # Apply filters
    if category:
        query = query.where(Tool.category == category)
    if pricing:
        query = query.where(Tool.pricing.ilike(f"%{pricing}%"))
    if featured is not None:
        query = query.where(Tool.is_featured == featured)
    if search:
        query = query.where(
            (Tool.name.ilike(f"%{search}%")) | (Tool.tagline.ilike(f"%{search}%"))
        )

    # Sort by sort_order, then by name
    query = query.order_by(Tool.sort_order.asc(), Tool.name.asc())

    # Pagination
    query = query.limit(limit).offset(offset)

    # Execute
    result = await db.execute(query)
    tools = result.scalars().all()

    # Get total count
    count_query = select(func.count(Tool.id))
    if category:
        count_query = count_query.where(Tool.category == category)
    if pricing:
        count_query = count_query.where(Tool.pricing.ilike(f"%{pricing}%"))
    if featured is not None:
        count_query = count_query.where(Tool.is_featured == featured)
    if search:
        count_query = count_query.where(
            (Tool.name.ilike(f"%{search}%")) | (Tool.tagline.ilike(f"%{search}%"))
        )

    total = await db.scalar(count_query)

    logger.info(f"Listed {len(tools)} tools (category={category}, total={total})")

    return ToolListResponse(
        tools=[ToolResponse.model_validate(t) for t in tools],
        total=total or 0,
        limit=limit,
        offset=offset,
    )


@router.get("/featured", response_model=list[ToolResponse])
async def get_featured_tools(
    limit: Annotated[int, Query(ge=1, le=20, description="Number of featured tools")] = 6,
    db: AsyncSession = Depends(get_db),
) -> list[ToolResponse]:
    """
    Get featured tools for homepage display.

    Returns tools marked as featured, sorted by sort_order.
    """
    query = (
        select(Tool)
        .where(Tool.is_featured == True)
        .order_by(Tool.sort_order.asc())
        .limit(limit)
    )

    result = await db.execute(query)
    tools = result.scalars().all()

    logger.info(f"Retrieved {len(tools)} featured tools")

    return [ToolResponse.model_validate(t) for t in tools]


@router.get("/{tool_id}", response_model=ToolResponse)
async def get_tool(
    tool_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> ToolResponse:
    """
    Get a single tool by ID.
    """
    query = select(Tool).where(Tool.id == tool_id)
    result = await db.execute(query)
    tool = result.scalar_one_or_none()

    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")

    return ToolResponse.model_validate(tool)


@router.post("", response_model=ToolResponse, status_code=201)
async def create_tool(
    tool_data: ToolCreate,
    admin: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> ToolResponse:
    """
    Create a new tool (admin only).
    """

    tool = Tool(**tool_data.model_dump())
    db.add(tool)
    await db.commit()
    await db.refresh(tool)

    logger.info(f"Created tool: {tool.name} (id={tool.id})")

    return ToolResponse.model_validate(tool)


@router.patch("/{tool_id}", response_model=ToolResponse)
async def update_tool(
    tool_id: UUID,
    tool_data: ToolUpdate,
    admin: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> ToolResponse:
    """
    Update an existing tool (admin only).
    """

    query = select(Tool).where(Tool.id == tool_id)
    result = await db.execute(query)
    tool = result.scalar_one_or_none()

    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")

    # Update only provided fields
    update_data = tool_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tool, field, value)

    await db.commit()
    await db.refresh(tool)

    logger.info(f"Updated tool: {tool.name} (id={tool.id})")

    return ToolResponse.model_validate(tool)


@router.delete("/{tool_id}", status_code=204)
async def delete_tool(
    tool_id: UUID,
    admin: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete a tool (admin only).
    """

    query = select(Tool).where(Tool.id == tool_id)
    result = await db.execute(query)
    tool = result.scalar_one_or_none()

    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")

    await db.delete(tool)
    await db.commit()

    logger.info(f"Deleted tool: {tool.name} (id={tool_id})")
