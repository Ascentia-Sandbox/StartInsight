"""SQLAlchemy declarative base for all database models."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy models.

    All database models should inherit from this class.
    Using SQLAlchemy 2.0 declarative base with type annotations.

    Example:
        from sqlalchemy import String
        from sqlalchemy.orm import Mapped, mapped_column

        class User(Base):
            __tablename__ = "users"

            id: Mapped[int] = mapped_column(primary_key=True)
            name: Mapped[str] = mapped_column(String(100))
    """

    pass
