/**
 * Next.js Middleware - Composed Authentication + i18n
 *
 * Handles:
 * 1. Supabase authentication and session refresh
 * 2. Route protection for authenticated pages
 * 3. Locale routing (English-only)
 */

import { createServerClient, type CookieOptions } from '@supabase/ssr';
import { NextResponse, type NextRequest } from 'next/server';
import createIntlMiddleware from 'next-intl/middleware';
import { locales } from './i18n';

// Routes that require authentication
const protectedRoutes = ['/dashboard', '/workspace', '/settings', '/research', '/build', '/teams', '/billing'];

// Routes that require admin role
const adminRoutes = ['/admin'];

// Create i18n middleware instance
const intlMiddleware = createIntlMiddleware({
  locales,
  defaultLocale: 'en',
  localePrefix: 'as-needed'
});

export async function middleware(request: NextRequest) {
  const pathname = request.nextUrl.pathname;

  // Skip i18n middleware for admin routes (they live outside [locale])
  const isAdminPath = pathname.startsWith('/admin');

  // Step 1: Handle i18n routing (skip for admin pages)
  // The intl middleware returns a response with rewrites (e.g. /founder-fits -> /en/founder-fits)
  // or redirects that we MUST preserve — not discard.
  const intlResponse = isAdminPath ? null : intlMiddleware(request);

  // Step 2: Use the intl response as the base (preserves rewrites/redirects),
  // or fall back to NextResponse.next() for admin routes.
  let response = intlResponse ?? NextResponse.next({ request });

  // Step 3: Create Supabase client for auth (writes cookies onto the response)
  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll();
        },
        setAll(cookiesToSet: { name: string; value: string; options: CookieOptions }[]) {
          cookiesToSet.forEach(({ name, value }) => request.cookies.set(name, value));
          // When Supabase needs to update cookies, rebuild the response while
          // preserving the intl middleware's rewrite/redirect behaviour.
          if (intlResponse) {
            // Re-run intl middleware to get a fresh response with the same rewrite
            const freshIntl = intlMiddleware(request);
            response = freshIntl;
          } else {
            response = NextResponse.next({ request });
          }
          cookiesToSet.forEach(({ name, value, options }) =>
            response.cookies.set(name, value, options)
          );
        },
      },
    }
  );

  // Refresh session if expired
  const {
    data: { user },
  } = await supabase.auth.getUser();

  // Extract pathname without locale prefix (if present)
  const locale = pathname.split('/')[1];
  const pathWithoutLocale = locales.includes(locale as any)
    ? pathname.slice(locale.length + 1) || '/'
    : pathname;

  // Check if route requires authentication (check path without locale)
  const isProtectedRoute = protectedRoutes.some((route) => pathWithoutLocale.startsWith(route));
  const isAdminRoute = adminRoutes.some((route) => pathWithoutLocale.startsWith(route));

  // Redirect to login if accessing protected route without auth
  if ((isProtectedRoute || isAdminRoute) && !user) {
    const url = request.nextUrl.clone();
    url.pathname = '/auth/login';
    url.searchParams.set('redirectTo', pathname);
    return NextResponse.redirect(url);
  }

  // Redirect non-admin users away from admin routes
  const adminRoles = ['admin', 'superadmin'];
  if (isAdminRoute && user && !adminRoles.includes(user.app_metadata?.role)) {
    const url = request.nextUrl.clone();
    url.pathname = '/dashboard';
    return NextResponse.redirect(url);
  }

  // Redirect logged-in users away from auth pages (except update-password which requires a session)
  const isUpdatePassword = pathWithoutLocale === '/auth/update-password' || pathname === '/auth/update-password';
  if (user && !isUpdatePassword && (pathWithoutLocale.startsWith('/auth/') || pathname.startsWith('/auth/'))) {
    const url = request.nextUrl.clone();
    url.pathname = '/dashboard';
    return NextResponse.redirect(url);
  }

  return response;
}

export const config = {
  matcher: [
    // Match all routes except static files and API routes
    '/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp|txt|xml|ico)$).*)',
  ],
};
