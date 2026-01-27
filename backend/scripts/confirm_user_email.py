#!/usr/bin/env python3
"""
Confirm user email in Supabase
"""
import asyncio
import os
import sys

from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

async def confirm_email(email: str):
    """Confirm user email with service role key"""
    # Use service role client (bypasses RLS)
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

    print(f"Confirming email for: {email}")

    try:
        # First, get the user by email
        user_query = supabase.table("users").select("supabase_user_id").eq("email", email).execute()

        if not user_query.data:
            print(f"❌ User not found: {email}")
            return

        supabase_user_id = user_query.data[0]["supabase_user_id"]

        # Confirm email using Admin API
        response = supabase.auth.admin.update_user_by_id(
            supabase_user_id,
            {
                "email_confirm": True
            }
        )

        print(f"✅ Email confirmed successfully for {email}")
        print("\nUser can now sign in at: http://localhost:3000/auth/login")

    except Exception as e:
        print(f"❌ Error confirming email: {e}")

if __name__ == "__main__":
    # Get email from command line
    if len(sys.argv) >= 2:
        email = sys.argv[1]
    else:
        email = "user1@testing.com"

    asyncio.run(confirm_email(email))
