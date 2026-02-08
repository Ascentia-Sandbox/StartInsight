#!/usr/bin/env python3
"""
Update user password in Supabase (via REST API).

Uses httpx for Supabase Auth Admin API and SQLAlchemy for local DB lookups.
NO Supabase SDK per CLAUDE.md rules.
"""
import asyncio
import os
import sys

import httpx
from dotenv import load_dotenv
from sqlalchemy import select

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.db.session import AsyncSessionLocal  # noqa: E402
from app.models.user import User  # noqa: E402

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")


async def update_password(email: str, new_password: str):
    """Update user password with service role key."""
    print(f"Updating password for: {email}")

    # Look up supabase_user_id from local DB
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User.supabase_user_id).where(User.email == email)
        )
        supabase_user_id = result.scalar_one_or_none()

    if not supabase_user_id:
        print(f"User not found: {email}")
        return

    try:
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{SUPABASE_URL}/auth/v1/admin/users/{supabase_user_id}",
                headers={
                    "apikey": SUPABASE_SERVICE_ROLE_KEY,
                    "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
                    "Content-Type": "application/json",
                },
                json={"password": new_password},
            )
            response.raise_for_status()

        print(f"Password updated successfully for {email}")
        print(f"\nNew credentials:")
        print(f"Email: {email}")
        print(f"Password: {new_password}")
        print("\nSign in at: http://localhost:3000/auth/login")

    except httpx.HTTPStatusError as e:
        print(f"Error updating password: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python update_user_password.py <email> <new_password>")
        sys.exit(1)
    email = sys.argv[1]
    password = sys.argv[2]

    asyncio.run(update_password(email, password))
