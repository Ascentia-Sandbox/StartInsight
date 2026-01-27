"""AdminUser database model - Admin portal role-based access.

Phase 4.2: Admin users with role-based permissions.
See architecture.md Section "Admin Portal Architecture" for full specification.
"""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AdminUser(Base):
    """
    AdminUser model - Role-based admin access control.

    Roles:
    - admin: Full access (pause/resume agents, edit insights, manage users)
    - moderator: Limited access (approve/reject insights)
    - viewer: Read-only access (view dashboard, metrics)

    RLS Policy: Only admins can access admin_users table.
    """

    __tablename__ = "admin_users"

    # Unique constraint on user_id
    __table_args__ = (UniqueConstraint("user_id", name="uq_admin_user"),)

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        doc="Unique identifier for this admin record",
    )

    # Foreign key to users table
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="User who has admin access",
    )

    # Role
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        doc="Admin role: admin, moderator, viewer",
    )

    # Granular permissions (optional override)
    permissions: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
        doc="Granular permissions override (can_pause_agents, can_edit_insights, etc.)",
    )

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="When admin access was granted",
    )

    # Relationship
    user: Mapped["User"] = relationship(
        "User",
        lazy="selectin",
        doc="The user with admin access",
    )

    def __repr__(self) -> str:
        """String representation of AdminUser."""
        return f"<AdminUser(user_id={self.user_id}, role='{self.role}')>"

    def has_permission(self, permission: str) -> bool:
        """Check if admin has specific permission."""
        # Check explicit permissions first
        if permission in self.permissions:
            return self.permissions[permission]

        # Default permissions by role
        role_permissions = {
            "admin": {
                "can_pause_agents",
                "can_resume_agents",
                "can_trigger_agents",
                "can_edit_insights",
                "can_delete_insights",
                "can_manage_users",
                "can_view_metrics",
            },
            "moderator": {
                "can_edit_insights",
                "can_view_metrics",
            },
            "viewer": {
                "can_view_metrics",
            },
        }

        return permission in role_permissions.get(self.role, set())
