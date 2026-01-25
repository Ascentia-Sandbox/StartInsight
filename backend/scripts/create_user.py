#!/usr/bin/env python3
"""
Create regular user in Supabase
"""
import asyncio
import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

async def create_user(email: str, password: str, full_name: str = None):
    """Create regular user with service role key"""
    # Use service role client (bypasses RLS)
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

    print(f"Creating user: {email}")

    try:
        # Create user using Admin API
        response = supabase.auth.admin.create_user({
            "email": email,
            "password": password,
            "email_confirm": True,  # Auto-confirm email
            "user_metadata": {
                "full_name": full_name or email.split('@')[0]
            }
        })

        user = response.user
        print(f"✅ User created successfully: {user.id}")

        # The trigger should have created the user profile automatically
        # Verify it was created
        user_query = supabase.table("users").select("*").eq("supabase_user_id", user.id).execute()

        if not user_query.data:
            print("❌ User profile not found in users table (trigger may have failed)")
            return

        print(f"✅ User profile created in database")
        print(f"\n🎉 User account created successfully!")
        print(f"Email: {email}")
        print(f"Password: {password}")
        print(f"Subscription: free")
        print(f"\nYou can now sign in at: http://localhost:3000/auth/login")

    except Exception as e:
        print(f"❌ Error creating user: {e}")
        # If user already exists
        if "already registered" in str(e).lower() or "duplicate" in str(e).lower():
            print("\n⚠️ User already exists with this email")

if __name__ == "__main__":
    # Get email and password from command line or use defaults
    if len(sys.argv) >= 3:
        email = sys.argv[1]
        password = sys.argv[2]
        full_name = sys.argv[3] if len(sys.argv) > 3 else None
    else:
        email = "user1@testing.com"
        password = "Abcd1234"
        full_name = "Test User 1"

    asyncio.run(create_user(email, password, full_name))
