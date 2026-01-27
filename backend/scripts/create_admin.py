#!/usr/bin/env python3
"""
Create super admin user in Supabase
"""
import asyncio
import os

from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

async def create_admin_user():
    """Create admin user with service role key"""
    # Use service role client (bypasses RLS)
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

    admin_email = "ascentiaholding@gmail.com"
    admin_password = "admin"

    print(f"Creating admin user: {admin_email}")

    try:
        # Create user using Admin API
        response = supabase.auth.admin.create_user({
            "email": admin_email,
            "password": admin_password,
            "email_confirm": True,  # Auto-confirm email
            "user_metadata": {
                "full_name": "Super Admin"
            }
        })

        user = response.user
        print(f"✅ User created successfully: {user.id}")

        # The trigger should have created the user profile automatically
        # Now we need to add them to admin_users table

        # First get the internal user ID from our users table
        user_query = supabase.table("users").select("id").eq("supabase_user_id", user.id).execute()

        if not user_query.data:
            print("❌ User profile not found in users table (trigger may have failed)")
            return

        internal_user_id = user_query.data[0]["id"]

        # Add to admin_users table
        admin_result = supabase.table("admin_users").insert({
            "user_id": internal_user_id,
            "role": "super_admin",
            "permissions": ["*"]  # All permissions
        }).execute()

        print(f"✅ Admin privileges granted: {admin_result.data[0]['id']}")
        print("\n🎉 Super admin account created successfully!")
        print(f"Email: {admin_email}")
        print(f"Password: {admin_password}")
        print("\nYou can now sign in at: http://localhost:3000/auth/login")

    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        # If user already exists, try to add admin privileges
        if "already registered" in str(e).lower() or "duplicate" in str(e).lower():
            print("\nUser already exists. Trying to add admin privileges...")
            try:
                # Get user by email
                existing_user = supabase.table("users").select("id, supabase_user_id").eq("email", admin_email).execute()

                if existing_user.data:
                    internal_user_id = existing_user.data[0]["id"]

                    # Check if already admin
                    admin_check = supabase.table("admin_users").select("*").eq("user_id", internal_user_id).execute()

                    if admin_check.data:
                        print("✅ User is already an admin")
                    else:
                        # Add admin privileges
                        admin_result = supabase.table("admin_users").insert({
                            "user_id": internal_user_id,
                            "role": "super_admin",
                            "permissions": ["*"]
                        }).execute()
                        print("✅ Admin privileges granted!")
            except Exception as inner_e:
                print(f"❌ Error adding admin privileges: {inner_e}")

if __name__ == "__main__":
    asyncio.run(create_admin_user())
