/**
 * Auth callback route handler
 *
 * This route handles the OAuth callback from Supabase.
 * It exchanges the code for a session and redirects to the dashboard.
 */

import { createClient } from '@/lib/supabase/server';
import { NextResponse } from 'next/server';

export async function GET(request: Request) {
  const { searchParams, origin } = new URL(request.url);
  const code = searchParams.get('code');
  const next = searchParams.get('next');
  const redirectTo = searchParams.get('redirectTo') || '/dashboard';

  if (code) {
    const supabase = await createClient();
    const { error } = await supabase.auth.exchangeCodeForSession(code);

    if (!error) {
      // Recovery flow: send to update-password page
      if (next === 'recovery') {
        return NextResponse.redirect(`${origin}/auth/update-password`);
      }
      return NextResponse.redirect(`${origin}${redirectTo}`);
    }
  }

  // Auth code exchange failed - redirect to login with error
  return NextResponse.redirect(`${origin}/auth/login?error=auth_failed`);
}
