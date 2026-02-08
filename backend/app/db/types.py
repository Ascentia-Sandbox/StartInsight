"""SQLAlchemy type utilities for cross-database compatibility.

Provides types that work with both PostgreSQL and SQLite for testing.
"""

import json
from typing import Any

from sqlalchemy import JSON, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.types import TypeDecorator


class PortableJSON(TypeDecorator):
    """JSON type that works with both PostgreSQL (JSONB) and SQLite (JSON).

    Uses JSONB on PostgreSQL for performance, falls back to JSON on other dialects.
    """

    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        else:
            return dialect.type_descriptor(JSON())

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name != "postgresql":
            return json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if dialect.name != "postgresql" and isinstance(value, str):
            return json.loads(value)
        return value


class PortableArray(TypeDecorator):
    """Array type that works with both PostgreSQL (ARRAY) and SQLite (JSON).

    Uses native ARRAY on PostgreSQL, stores as JSON array on SQLite.
    """

    impl = Text
    cache_ok = True

    def __init__(self, item_type=None):
        super().__init__()
        self.item_type = item_type

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            from sqlalchemy import String
            item_type = self.item_type or String(50)
            return dialect.type_descriptor(ARRAY(item_type))
        else:
            return dialect.type_descriptor(JSON())

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name != "postgresql":
            return json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if dialect.name != "postgresql" and isinstance(value, str):
            return json.loads(value)
        return value
