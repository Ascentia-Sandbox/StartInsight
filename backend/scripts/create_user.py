#!/usr/bin/env python3
"""
Create regular user in Supabase (via REST API).

Uses httpx for Supabase Auth Admin API.
NO Supabase SDK per CLAUDE.md rules.
"""
import asyncio
import os
import sys

import httpx
from dotenv import load_dotenv

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


async def create_user(email: str, password: str, full_name: str | None = None):
    """Create regular user with service role key."""
    print(f"Creating user: {email}")

    try:
        user_data = await supabase_admin_request(
            "POST",
            "users",
            json={
                "email": email,
                "password": password,
                "email_confirm": True,
                "user_metadata": {
                    "full_name": full_name or email.split("@")[0]
                },
            },
        )

        print(f"User created successfully: {user_data['id']}")
        print("\nUser account created!")
        print(f"Email: {email}")
        print(f"Password: {password}")
        print("\nSign in at: http://localhost:3000/auth/login")

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 422:
            print("User already exists with this email")
        else:
            print(f"Error creating user: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python create_user.py <email> <password> [full_name]")
        sys.exit(1)
    email = sys.argv[1]
    password = sys.argv[2]
    full_name = sys.argv[3] if len(sys.argv) > 3 else None

    asyncio.run(create_user(email, password, full_name))
