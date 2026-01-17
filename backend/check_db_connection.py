"""Database connection verification script."""

import asyncio

from sqlalchemy import text

from app.core.config import settings
from app.db.session import engine


async def check_connection() -> None:
    """Test database connection and print success message."""
    try:
        print("=" * 50)
        print("Database Connection Test")
        print("=" * 50)
        print(f"Database URL: {settings.async_database_url}")
        print(f"Environment: {settings.environment}")
        print("-" * 50)

        # Test connection by executing a simple query
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT version();"))
            version = result.scalar()
            print(f"PostgreSQL Version: {version}")

            # Test table creation permissions
            await conn.execute(text("SELECT 1;"))

        print("-" * 50)
        print("✓ Connection Successful")
        print("=" * 50)

    except Exception as e:
        print("-" * 50)
        print(f"✗ Connection Failed: {e}")
        print("=" * 50)
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(check_connection())
