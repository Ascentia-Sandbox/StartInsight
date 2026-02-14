"""Idea Chat models for Phase 9.2: AI Idea Chat Assistant.

Provides:
- IdeaChat: Chat session per user/insight
- IdeaChatMessage: Individual chat messages
"""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.insight import Insight
    from app.models.user import User


class IdeaChat(Base):
    """Chat session for AI-assisted idea exploration."""

    __tablename__ = "idea_chats"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    insight_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("insights.id", ondelete="CASCADE"), nullable=False)

    # Chat metadata
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mode: Mapped[str | None] = mapped_column(String(30), nullable=True)  # pressure_test, gtm_planning, pricing_strategy
    message_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], lazy="selectin")
    insight: Mapped["Insight"] = relationship("Insight", foreign_keys=[insight_id], lazy="selectin")
    messages: Mapped[list["IdeaChatMessage"]] = relationship("IdeaChatMessage", back_populates="chat", cascade="all, delete-orphan", lazy="selectin")

    def __repr__(self) -> str:
        return f"<IdeaChat(user={self.user_id}, insight={self.insight_id}, messages={self.message_count})>"


class IdeaChatMessage(Base):
    """Individual message in an idea chat session."""

    __tablename__ = "idea_chat_messages"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    chat_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("idea_chats.id", ondelete="CASCADE"), nullable=False)

    # Message content
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # user, assistant
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tokens_used: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    chat: Mapped["IdeaChat"] = relationship("IdeaChat", back_populates="messages")

    # Role constants
    ROLE_USER = "user"
    ROLE_ASSISTANT = "assistant"

    def __repr__(self) -> str:
        return f"<IdeaChatMessage(chat={self.chat_id}, role={self.role})>"
