"""Chat Strategist API routes - Phase B + Phase L: AI Chat Strategist.

Provides endpoints for AI-powered idea strategy conversations:
- 5 modes: general, pressure_test, gtm_planning, pricing_strategy, competitive
- SSE streaming for real-time AI responses
- Chat session CRUD with message history
"""

import asyncio
import json
import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.chat_agent import ChatContext, get_chat_response
from app.api.deps import get_current_user, get_db
from app.models.idea_chat import IdeaChat, IdeaChatMessage
from app.models.insight import Insight
from app.models.user import User
from app.schemas.chat import (
    ChatCreate,
    ChatListItem,
    ChatListResponse,
    ChatMessageCreate,
    ChatMessageResponse,
    ChatResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/idea-chats", tags=["Chat Strategist"])


# ============================================================
# Create Chat Session
# ============================================================


@router.post("", response_model=ChatResponse, status_code=201)
async def create_chat(
    payload: ChatCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Create a new chat session for an insight."""
    # Verify insight exists
    insight = await db.get(Insight, payload.insight_id)
    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found")

    mode_labels = {
        "general": "General",
        "pressure_test": "Pressure Test",
        "gtm_planning": "GTM Planning",
        "pricing_strategy": "Pricing Strategy",
        "competitive": "Competitive Analysis",
    }
    default_title = f"{mode_labels.get(payload.mode.value, 'Chat')}: {insight.title[:80]}"

    chat = IdeaChat(
        user_id=current_user.id,
        insight_id=payload.insight_id,
        title=payload.title or default_title,
        mode=payload.mode.value,
        message_count=0,
        total_tokens=0,
    )
    db.add(chat)
    await db.commit()
    await db.refresh(chat)

    return ChatResponse(
        id=chat.id,
        user_id=chat.user_id,
        insight_id=chat.insight_id,
        title=chat.title,
        mode=chat.mode,
        message_count=0,
        total_tokens=0,
        created_at=chat.created_at,
        updated_at=chat.updated_at,
        messages=[],
    )


# ============================================================
# List User's Chats
# ============================================================


@router.get("", response_model=ChatListResponse)
async def list_chats(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    insight_id: UUID | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """List user's chat sessions, optionally filtered by insight."""
    query = select(IdeaChat).where(IdeaChat.user_id == current_user.id)
    count_query = select(func.count()).select_from(IdeaChat).where(IdeaChat.user_id == current_user.id)

    if insight_id:
        query = query.where(IdeaChat.insight_id == insight_id)
        count_query = count_query.where(IdeaChat.insight_id == insight_id)

    query = query.order_by(IdeaChat.updated_at.desc()).limit(limit).offset(offset)

    result = await db.execute(query)
    chats = result.scalars().all()

    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    return ChatListResponse(
        items=[
            ChatListItem(
                id=c.id,
                insight_id=c.insight_id,
                title=c.title,
                mode=c.mode,
                message_count=c.message_count,
                updated_at=c.updated_at,
            )
            for c in chats
        ],
        total=total,
    )


# ============================================================
# Get Chat with Messages
# ============================================================


@router.get("/{chat_id}", response_model=ChatResponse)
async def get_chat(
    chat_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get a chat session with all messages."""
    chat = await db.get(IdeaChat, chat_id)
    if not chat or chat.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Chat not found")

    return ChatResponse(
        id=chat.id,
        user_id=chat.user_id,
        insight_id=chat.insight_id,
        title=chat.title,
        mode=chat.mode,
        message_count=chat.message_count,
        total_tokens=chat.total_tokens,
        created_at=chat.created_at,
        updated_at=chat.updated_at,
        messages=[
            ChatMessageResponse(
                id=m.id,
                role=m.role,
                content=m.content,
                tokens_used=m.tokens_used,
                created_at=m.created_at,
            )
            for m in sorted(chat.messages, key=lambda x: x.created_at)
        ],
    )


# ============================================================
# Send Message (SSE Streaming)
# ============================================================


@router.post("/{chat_id}/messages")
async def send_message(
    chat_id: UUID,
    payload: ChatMessageCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Send a message and get AI response via SSE streaming."""
    chat = await db.get(IdeaChat, chat_id)
    if not chat or chat.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Chat not found")

    # Save user message
    user_msg = IdeaChatMessage(
        chat_id=chat.id,
        role=IdeaChatMessage.ROLE_USER,
        content=payload.content,
    )
    db.add(user_msg)
    chat.message_count += 1
    await db.commit()
    await db.refresh(user_msg)

    # Build context from the linked insight
    insight = chat.insight
    scores = {}
    for field in [
        "opportunity_score", "problem_score", "feasibility_score",
        "why_now_score", "execution_difficulty", "go_to_market_score",
        "founder_fit_score",
    ]:
        val = getattr(insight, field, None)
        if val is not None:
            scores[field.replace("_score", "").replace("_", " ").title()] = val

    context = ChatContext(
        insight_title=insight.title or "",
        problem_statement=insight.problem_statement or "",
        proposed_solution=insight.proposed_solution or "",
        market_size=insight.market_size_estimate,
        relevance_score=insight.relevance_score,
        scores=scores if scores else None,
    )

    # Build conversation history from existing messages
    conversation_history = [
        {"role": m.role, "content": m.content}
        for m in sorted(chat.messages, key=lambda x: x.created_at)
    ]

    async def generate_sse():
        """SSE event generator."""
        try:
            # Send user message event
            yield f"data: {json.dumps({'type': 'user_message', 'id': str(user_msg.id), 'content': payload.content})}\n\n"

            # Send thinking indicator
            yield f"data: {json.dumps({'type': 'thinking'})}\n\n"

            # Get AI response
            agent_response = await get_chat_response(
                mode=chat.mode or "pressure_test",
                user_message=payload.content,
                context=context,
                conversation_history=conversation_history,
            )

            # Save assistant message
            assistant_msg = IdeaChatMessage(
                chat_id=chat.id,
                role=IdeaChatMessage.ROLE_ASSISTANT,
                content=agent_response.response,
            )
            db.add(assistant_msg)
            chat.message_count += 1
            await db.commit()
            await db.refresh(assistant_msg)

            # Send assistant message event
            yield f"data: {json.dumps({'type': 'assistant_message', 'id': str(assistant_msg.id), 'content': agent_response.response})}\n\n"

            # Send done event
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            logger.error(f"Chat agent error: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'message': 'Failed to generate response. Please try again.'})}\n\n"

    return StreamingResponse(
        generate_sse(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ============================================================
# Delete Chat
# ============================================================


@router.delete("/{chat_id}", status_code=204)
async def delete_chat(
    chat_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Delete a chat session and all its messages."""
    chat = await db.get(IdeaChat, chat_id)
    if not chat or chat.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Chat not found")

    await db.delete(chat)
    await db.commit()
