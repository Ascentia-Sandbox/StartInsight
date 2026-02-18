"""Chat schemas for Phase B + Phase L: AI Chat Strategist.

Pydantic V2 schemas for idea chat sessions with 5 strategist modes.
"""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class ChatMode(str, Enum):
    """Chat strategist modes."""

    GENERAL = "general"
    PRESSURE_TEST = "pressure_test"
    GTM_PLANNING = "gtm_planning"
    PRICING_STRATEGY = "pricing_strategy"
    COMPETITIVE = "competitive"


class ChatCreate(BaseModel):
    """Create a new chat session."""

    insight_id: UUID
    mode: ChatMode = ChatMode.GENERAL
    title: str | None = Field(None, max_length=255)


class ChatMessageCreate(BaseModel):
    """Send a user message."""

    content: str = Field(..., min_length=1, max_length=5000)


class ChatMessageResponse(BaseModel):
    """Chat message response."""

    id: UUID
    role: str
    content: str
    tokens_used: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatResponse(BaseModel):
    """Full chat session with messages."""

    id: UUID
    user_id: UUID
    insight_id: UUID
    title: str | None = None
    mode: str | None = None
    message_count: int = 0
    total_tokens: int = 0
    created_at: datetime
    updated_at: datetime
    messages: list[ChatMessageResponse] = []

    model_config = {"from_attributes": True}


class ChatListItem(BaseModel):
    """Chat session summary for listing."""

    id: UUID
    insight_id: UUID
    title: str | None = None
    mode: str | None = None
    message_count: int = 0
    updated_at: datetime

    model_config = {"from_attributes": True}


class ChatListResponse(BaseModel):
    """Paginated list of chat sessions."""

    items: list[ChatListItem]
    total: int
