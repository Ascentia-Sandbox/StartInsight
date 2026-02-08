#!/usr/bin/env python3
"""
Create super admin user in Supabase (via REST API) and local database.

Uses httpx for Supabase Auth Admin API and SQLAlchemy for local DB.
NO Supabase SDK per CLAUDE.md rules.
"""
import asyncio
import os
import sys

import httpx
from dotenv import load_dotenv
from sqlalchemy import select

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.db.session import AsyncSessionLocal  # noqa: E402
from app.models.admin_user import AdminUser  # noqa: E402
from app.models.user import User  # noqa: E402

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")


async def supabase_admin_request(
    method: str, path: str, json: dict | None = None
) -> dict:
    """Make an authenticated request to Supabase Auth Admin API."""
    async with httpx.AsyncClient() as client:
        response = await client.request(
            method,
            f"{SUPABASE_URL}/auth/v1/admin/{path}",
            headers={
                "apikey": SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
                "Content-Type": "application/json",
            },
            json=json,
        )
        response.raise_for_status()
        return response.json()


async def create_admin_user(admin_email: str, admin_password: str):
    """Create admin user with service role key."""

    print(f"Creating admin user: {admin_email}")

    try:
        # Create user via Supabase Auth Admin REST API
        user_data = await supabase_admin_request(
            "POST",
            "users",
            json={
                "email": admin_email,
                "password": admin_password,
                "email_confirm": True,
                "user_metadata": {"full_name": "Super Admin"},
            },
        )

        supabase_uid = user_data["id"]
        print(f"Supabase user created: {supabase_uid}")

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 422:
            print("User already exists in Supabase. Continuing to add admin privileges...")
            # Look up existing user in local DB
            supabase_uid = None
        else:
            print(f"Error creating Supabase user: {e}")
            raise

    # Add admin privileges via SQLAlchemy
    async with AsyncSessionLocal() as session:
        # Find user in local DB
        if supabase_uid:
            result = await session.execute(
                select(User).where(User.supabase_user_id == supabase_uid)
            )
        else:
            result = await session.execute(
                select(User).where(User.email == admin_email)
            )
        user = result.scalar_one_or_none()

        if not user:
            print("User profile not found in local database (trigger may have failed)")
            return

        # Check if already admin
        admin_result = await session.execute(
            select(AdminUser).where(AdminUser.user_id == user.id)
        )
        existing_admin = admin_result.scalar_one_or_none()

        if existing_admin:
            print("User is already an admin")
            return

        # Add admin privileges
        admin = AdminUser(
            user_id=user.id,
            role="super_admin",
            permissions={"*": True},
        )
        session.add(admin)
        await session.commit()

        print(f"Admin privileges granted: {admin.id}")
        print(f"\nSuper admin account ready!")
        print(f"Email: {admin_email}")
        print(f"Password: {admin_password}")
        print("\nSign in at: http://localhost:3000/auth/login")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python create_admin.py <email> <password>")
        sys.exit(1)
    asyncio.run(create_admin_user(sys.argv[1], sys.argv[2]))
