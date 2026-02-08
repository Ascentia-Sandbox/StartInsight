#!/usr/bin/env python3
"""
Confirm user email in Supabase (via REST API).

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


async def confirm_email(email: str):
    """Confirm user email with service role key."""
    print(f"Confirming email for: {email}")

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
                json={"email_confirm": True},
            )
            response.raise_for_status()

        print(f"Email confirmed successfully for {email}")
        print("\nUser can now sign in at: http://localhost:3000/auth/login")

    except httpx.HTTPStatusError as e:
        print(f"Error confirming email: {e}")


if __name__ == "__main__":
    if len(sys.argv) >= 2:
        email = sys.argv[1]
    else:
        email = "user1@testing.com"

    asyncio.run(confirm_email(email))
