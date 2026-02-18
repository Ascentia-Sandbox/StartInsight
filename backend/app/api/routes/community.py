"""Community API routes - Phase 9.3: Validation Acceleration.

Provides endpoints for:
- Idea voting (upvote/downvote)
- Idea comments with threading
- Polls for validation
"""

import logging
from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.community import (
    CommentUpvote,
    IdeaComment,
    IdeaPoll,
    IdeaVote,
    PollResponse,
)
from app.models.insight import Insight
from app.models.user import User
from app.services.sanitization import sanitize_html

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/community", tags=["Community"])


# ============================================
# Schemas
# ============================================

class VoteCreate(BaseModel):
    vote_type: str = Field(..., pattern="^(up|down)$")


class VoteResponse(BaseModel):
    id: UUID
    user_id: UUID
    insight_id: UUID
    vote_type: str
    created_at: datetime

    class Config:
        from_attributes = True


class VoteSummary(BaseModel):
    insight_id: UUID
    upvotes: int
    downvotes: int
    user_vote: str | None


class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)
    parent_id: UUID | None = None


class CommentUpdate(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)


class CommentResponse(BaseModel):
    id: UUID
    user_id: UUID
    insight_id: UUID
    parent_id: UUID | None
    content: str
    upvotes: int
    is_expert: bool
    is_pinned: bool
    created_at: datetime
    updated_at: datetime
    author_name: str | None = None
    reply_count: int = 0

    class Config:
        from_attributes = True


class PollCreate(BaseModel):
    question: str = Field(..., min_length=5, max_length=255)
    poll_type: str = Field(default="yes_no", pattern="^(yes_no|scale|multiple)$")
    options: dict | None = None


class PollResponse(BaseModel):
    id: UUID
    insight_id: UUID
    question: str
    poll_type: str
    options: dict | None
    is_active: bool
    expires_at: datetime | None
    created_at: datetime
    response_count: int = 0
    results: dict | None = None

    class Config:
        from_attributes = True


class PollVote(BaseModel):
    response: str = Field(..., max_length=100)


# ============================================
# Voting Endpoints
# ============================================

@router.post("/insights/{insight_id}/vote", response_model=VoteResponse)
async def vote_on_insight(
    insight_id: UUID,
    vote: VoteCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Vote on an insight (upvote or downvote). Replaces previous vote if exists."""
    # Verify insight exists
    result = await db.execute(select(Insight).where(Insight.id == insight_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Insight not found")

    # Check for existing vote
    result = await db.execute(
        select(IdeaVote).where(
            IdeaVote.user_id == current_user.id,
            IdeaVote.insight_id == insight_id,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        if existing.vote_type == vote.vote_type:
            # Remove vote (toggle off)
            await db.delete(existing)
            await db.commit()
            return VoteResponse(
                id=existing.id,
                user_id=existing.user_id,
                insight_id=existing.insight_id,
                vote_type="none",
                created_at=existing.created_at,
            )
        else:
            # Change vote
            existing.vote_type = vote.vote_type
            existing.created_at = datetime.now(UTC)
            await db.commit()
            await db.refresh(existing)
            return VoteResponse.model_validate(existing)

    # Create new vote
    new_vote = IdeaVote(
        user_id=current_user.id,
        insight_id=insight_id,
        vote_type=vote.vote_type,
    )
    db.add(new_vote)
    await db.commit()
    await db.refresh(new_vote)

    logger.info(f"User {current_user.id} voted {vote.vote_type} on insight {insight_id}")
    return VoteResponse.model_validate(new_vote)


@router.get("/insights/{insight_id}/votes", response_model=VoteSummary)
async def get_vote_summary(
    insight_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)] = None,
):
    """Get vote summary for an insight."""
    # Count upvotes
    up_result = await db.execute(
        select(func.count()).where(
            IdeaVote.insight_id == insight_id,
            IdeaVote.vote_type == "up",
        )
    )
    upvotes = up_result.scalar() or 0

    # Count downvotes
    down_result = await db.execute(
        select(func.count()).where(
            IdeaVote.insight_id == insight_id,
            IdeaVote.vote_type == "down",
        )
    )
    downvotes = down_result.scalar() or 0

    # Get current user's vote
    user_vote = None
    if current_user:
        result = await db.execute(
            select(IdeaVote).where(
                IdeaVote.user_id == current_user.id,
                IdeaVote.insight_id == insight_id,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            user_vote = existing.vote_type

    return VoteSummary(
        insight_id=insight_id,
        upvotes=upvotes,
        downvotes=downvotes,
        user_vote=user_vote,
    )


# ============================================
# Comments Endpoints
# ============================================

@router.post("/insights/{insight_id}/comments", response_model=CommentResponse)
async def create_comment(
    insight_id: UUID,
    comment: CommentCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Add a comment to an insight."""
    # Verify insight exists
    result = await db.execute(select(Insight).where(Insight.id == insight_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Insight not found")

    # Verify parent comment if provided
    if comment.parent_id:
        result = await db.execute(
            select(IdeaComment).where(
                IdeaComment.id == comment.parent_id,
                IdeaComment.insight_id == insight_id,
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Parent comment not found")

    # Sanitize comment content to prevent XSS
    sanitized_content = sanitize_html(comment.content)

    new_comment = IdeaComment(
        user_id=current_user.id,
        insight_id=insight_id,
        parent_id=comment.parent_id,
        content=sanitized_content,
    )
    db.add(new_comment)
    await db.commit()
    await db.refresh(new_comment)

    logger.info(f"User {current_user.id} commented on insight {insight_id}")
    return CommentResponse(
        id=new_comment.id,
        user_id=new_comment.user_id,
        insight_id=new_comment.insight_id,
        parent_id=new_comment.parent_id,
        content=new_comment.content,
        upvotes=new_comment.upvotes,
        is_expert=new_comment.is_expert,
        is_pinned=new_comment.is_pinned,
        created_at=new_comment.created_at,
        updated_at=new_comment.updated_at,
        author_name=current_user.full_name or current_user.email,
    )


@router.get("/insights/{insight_id}/comments", response_model=list[CommentResponse])
async def list_comments(
    insight_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    parent_id: UUID | None = None,
    limit: int = Query(50, le=100),
    offset: int = 0,
):
    """List comments for an insight, optionally filtered by parent."""
    query = (
        select(IdeaComment)
        .where(
            IdeaComment.insight_id == insight_id,
            IdeaComment.is_deleted == False,
        )
        .order_by(IdeaComment.is_pinned.desc(), IdeaComment.created_at.desc())
        .offset(offset)
        .limit(limit)
    )

    if parent_id:
        query = query.where(IdeaComment.parent_id == parent_id)
    else:
        query = query.where(IdeaComment.parent_id.is_(None))

    result = await db.execute(query)
    comments = result.scalars().all()

    responses = []
    for c in comments:
        # Count replies
        reply_count_result = await db.execute(
            select(func.count()).where(
                IdeaComment.parent_id == c.id,
                IdeaComment.is_deleted == False,
            )
        )
        reply_count = reply_count_result.scalar() or 0

        responses.append(CommentResponse(
            id=c.id,
            user_id=c.user_id,
            insight_id=c.insight_id,
            parent_id=c.parent_id,
            content=c.content,
            upvotes=c.upvotes,
            is_expert=c.is_expert,
            is_pinned=c.is_pinned,
            created_at=c.created_at,
            updated_at=c.updated_at,
            reply_count=reply_count,
        ))

    return responses


@router.patch("/comments/{comment_id}", response_model=CommentResponse)
async def update_comment(
    comment_id: UUID,
    updates: CommentUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Update own comment."""
    result = await db.execute(
        select(IdeaComment).where(IdeaComment.id == comment_id)
    )
    comment = result.scalar_one_or_none()

    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Can only edit own comments")

    comment.content = sanitize_html(updates.content)
    comment.updated_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(comment)

    return CommentResponse.model_validate(comment)


@router.delete("/comments/{comment_id}")
async def delete_comment(
    comment_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Soft delete own comment."""
    result = await db.execute(
        select(IdeaComment).where(IdeaComment.id == comment_id)
    )
    comment = result.scalar_one_or_none()

    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Can only delete own comments")

    comment.is_deleted = True
    comment.content = "[deleted]"
    comment.updated_at = datetime.now(UTC)
    await db.commit()

    return {"status": "deleted"}


@router.post("/comments/{comment_id}/upvote")
async def upvote_comment(
    comment_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Upvote a comment. Toggle off if already upvoted."""
    result = await db.execute(
        select(IdeaComment).where(IdeaComment.id == comment_id)
    )
    comment = result.scalar_one_or_none()

    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    # Check existing upvote
    result = await db.execute(
        select(CommentUpvote).where(
            CommentUpvote.user_id == current_user.id,
            CommentUpvote.comment_id == comment_id,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        # Remove upvote
        await db.delete(existing)
        comment.upvotes = max(0, comment.upvotes - 1)
        await db.commit()
        return {"status": "removed", "upvotes": comment.upvotes}

    # Add upvote
    upvote = CommentUpvote(user_id=current_user.id, comment_id=comment_id)
    db.add(upvote)
    comment.upvotes += 1
    await db.commit()

    return {"status": "added", "upvotes": comment.upvotes}


# ============================================
# Polls Endpoints
# ============================================

@router.post("/insights/{insight_id}/polls", response_model=PollResponse)
async def create_poll(
    insight_id: UUID,
    poll: PollCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Create a poll on an insight."""
    # Verify insight exists
    result = await db.execute(select(Insight).where(Insight.id == insight_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Insight not found")

    # Sanitize poll question and options to prevent XSS
    sanitized_question = sanitize_html(poll.question)
    sanitized_options = [sanitize_html(opt) for opt in poll.options] if poll.options else []

    new_poll = IdeaPoll(
        insight_id=insight_id,
        created_by=current_user.id,
        question=sanitized_question,
        poll_type=poll.poll_type,
        options=sanitized_options,
    )
    db.add(new_poll)
    await db.commit()
    await db.refresh(new_poll)

    logger.info(f"User {current_user.id} created poll on insight {insight_id}")
    return PollResponse(
        id=new_poll.id,
        insight_id=new_poll.insight_id,
        question=new_poll.question,
        poll_type=new_poll.poll_type,
        options=new_poll.options,
        is_active=new_poll.is_active,
        expires_at=new_poll.expires_at,
        created_at=new_poll.created_at,
    )


@router.get("/insights/{insight_id}/polls", response_model=list[PollResponse])
async def list_polls(
    insight_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List polls for an insight."""
    result = await db.execute(
        select(IdeaPoll)
        .where(IdeaPoll.insight_id == insight_id, IdeaPoll.is_active == True)
        .order_by(IdeaPoll.created_at.desc())
    )
    polls = result.scalars().all()

    responses = []
    for p in polls:
        # Count responses
        count_result = await db.execute(
            select(func.count()).where(PollResponse.poll_id == p.id)
        )
        response_count = count_result.scalar() or 0

        # Get results
        results_query = await db.execute(
            select(PollResponse.response, func.count())
            .where(PollResponse.poll_id == p.id)
            .group_by(PollResponse.response)
        )
        results = {row[0]: row[1] for row in results_query.fetchall()}

        responses.append(PollResponse(
            id=p.id,
            insight_id=p.insight_id,
            question=p.question,
            poll_type=p.poll_type,
            options=p.options,
            is_active=p.is_active,
            expires_at=p.expires_at,
            created_at=p.created_at,
            response_count=response_count,
            results=results,
        ))

    return responses


@router.post("/polls/{poll_id}/respond")
async def respond_to_poll(
    poll_id: UUID,
    vote: PollVote,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Submit a response to a poll."""
    result = await db.execute(select(IdeaPoll).where(IdeaPoll.id == poll_id))
    poll = result.scalar_one_or_none()

    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")
    if not poll.is_active:
        raise HTTPException(status_code=400, detail="Poll is closed")

    # Check existing response
    result = await db.execute(
        select(PollResponse).where(
            PollResponse.poll_id == poll_id,
            PollResponse.user_id == current_user.id,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        # Update response
        existing.response = vote.response
        existing.created_at = datetime.now(UTC)
        await db.commit()
        return {"status": "updated", "response": vote.response}

    # Create response
    response = PollResponse(
        poll_id=poll_id,
        user_id=current_user.id,
        response=vote.response,
    )
    db.add(response)
    await db.commit()

    return {"status": "recorded", "response": vote.response}
