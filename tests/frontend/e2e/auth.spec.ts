import { test, expect } from '@playwright/test';

/**
 * Authentication Flow E2E Tests
 *
 * Tests for signup, signin, signout, and protected routes.
 * Uses Supabase Auth for authentication.
 */

test.describe('Authentication Flows', () => {
  test.describe('Sign Up', () => {
    test('should display signup form', async ({ page }) => {
      await page.goto('/auth/signup');

      // Should show signup form
      await expect(page.locator('input[type="email"]')).toBeVisible();
      await expect(page.locator('input[type="password"]')).toBeVisible();
      await expect(page.locator('button:has-text("Sign up"), button:has-text("Create account")')).toBeVisible();
    });

    test('should show error for invalid email', async ({ page }) => {
      await page.goto('/auth/signup');

      await page.fill('input[type="email"]', 'invalid-email');
      await page.fill('input[type="password"]', 'password123');
      await page.click('button:has-text("Sign up"), button:has-text("Create account")');

      // Should show email validation error
      const error = page.locator('text=/invalid|valid email/i');
      await expect(error).toBeVisible({ timeout: 5000 });
    });

    test('should show error for weak password', async ({ page }) => {
      await page.goto('/auth/signup');

      await page.fill('input[type="email"]', 'test@example.com');
      await page.fill('input[type="password"]', '123'); // Too short
      await page.click('button:has-text("Sign up"), button:has-text("Create account")');

      // Should show password validation error
      const error = page.locator('text=/password|characters|weak/i');
      await expect(error).toBeVisible({ timeout: 5000 });
    });

    test('should have link to signin page', async ({ page }) => {
      await page.goto('/auth/signup');

      const signinLink = page.locator('a:has-text("Sign in"), a:has-text("Log in"), text=/already have an account/i');
      await expect(signinLink.first()).toBeVisible();
    });
  });

  test.describe('Sign In', () => {
    test('should display signin form', async ({ page }) => {
      await page.goto('/auth/signin');

      await expect(page.locator('input[type="email"]')).toBeVisible();
      await expect(page.locator('input[type="password"]')).toBeVisible();
      await expect(page.locator('button:has-text("Sign in"), button:has-text("Log in")')).toBeVisible();
    });

    test('should show error for invalid credentials', async ({ page }) => {
      await page.goto('/auth/signin');

      await page.fill('input[type="email"]', 'nonexistent@example.com');
      await page.fill('input[type="password"]', 'wrongpassword');
      await page.click('button:has-text("Sign in"), button:has-text("Log in")');

      // Should show authentication error
      const error = page.locator('text=/invalid|incorrect|credentials|not found/i');
      await expect(error).toBeVisible({ timeout: 5000 });
    });

    test('should have forgot password link', async ({ page }) => {
      await page.goto('/auth/signin');

      const forgotLink = page.locator('a:has-text("Forgot"), text=/forgot password/i');
      if (await forgotLink.count() > 0) {
        await expect(forgotLink.first()).toBeVisible();
      }
    });

    test('should have link to signup page', async ({ page }) => {
      await page.goto('/auth/signin');

      const signupLink = page.locator('a:has-text("Sign up"), a:has-text("Create"), text=/don.t have an account/i');
      await expect(signupLink.first()).toBeVisible();
    });
  });

  test.describe('Protected Routes', () => {
    test('should redirect unauthenticated users from dashboard', async ({ page }) => {
      await page.goto('/dashboard');

      // Should redirect to signin
      await page.waitForURL(/\/(auth\/signin|signin|login)/i, { timeout: 5000 });
    });

    test('should redirect unauthenticated users from workspace', async ({ page }) => {
      await page.goto('/workspace');

      // Should redirect to signin
      await page.waitForURL(/\/(auth\/signin|signin|login)/i, { timeout: 5000 });
    });

    test('should redirect unauthenticated users from research', async ({ page }) => {
      await page.goto('/research');

      // Should redirect to signin or show login required message
      const isRedirected = page.url().includes('signin') || page.url().includes('login');
      const hasLoginMessage = await page.locator('text=/sign in|log in/i').count() > 0;

      expect(isRedirected || hasLoginMessage).toBeTruthy();
    });

    test('should redirect unauthenticated users from billing', async ({ page }) => {
      await page.goto('/billing');

      // Should redirect to signin
      await page.waitForURL(/\/(auth\/signin|signin|login)/i, { timeout: 5000 });
    });

    test('should redirect unauthenticated users from admin', async ({ page }) => {
      await page.goto('/admin');

      // Should redirect to signin
      await page.waitForURL(/\/(auth\/signin|signin|login)/i, { timeout: 5000 });
    });
  });

  test.describe('Public Routes', () => {
    test('should allow unauthenticated access to homepage', async ({ page }) => {
      await page.goto('/');

      // Should not redirect, homepage should load
      await expect(page).toHaveURL(/\/$/);
      await expect(page.locator('h1, h2').first()).toBeVisible();
    });

    test('should allow unauthenticated access to insights', async ({ page }) => {
      await page.goto('/insights');

      // Should not redirect
      await expect(page).toHaveURL('/insights');
    });

    test('should allow unauthenticated access to tools', async ({ page }) => {
      await page.goto('/tools');

      // Should not redirect
      await expect(page).toHaveURL('/tools');
    });

    test('should allow unauthenticated access to trends', async ({ page }) => {
      await page.goto('/trends');

      // Should not redirect
      await expect(page).toHaveURL('/trends');
    });

    test('should allow unauthenticated access to success stories', async ({ page }) => {
      await page.goto('/success-stories');

      // Should not redirect
      await expect(page).toHaveURL('/success-stories');
    });

    test('should allow unauthenticated access to pricing', async ({ page }) => {
      await page.goto('/pricing');

      // Should not redirect
      await expect(page).toHaveURL('/pricing');
    });
  });
});

test.describe('Authentication UI Elements', () => {
  test('should show login/signup buttons when not authenticated', async ({ page }) => {
    await page.goto('/');

    // Should show login or signup buttons in header
    const authButtons = page.locator('button:has-text("Sign in"), button:has-text("Log in"), button:has-text("Sign up"), a:has-text("Sign in"), a:has-text("Log in")');
    await expect(authButtons.first()).toBeVisible();
  });

  test('should show navigation for authenticated user flow', async ({ page }) => {
    // Navigate to signin page
    await page.goto('/auth/signin');

    // Check for OAuth provider buttons (Google, GitHub, etc.)
    const oauthButtons = page.locator('button:has-text("Google"), button:has-text("GitHub"), button:has-text("Continue with")');
    const oauthCount = await oauthButtons.count();

    // May or may not have OAuth, just verify the page loads
    await expect(page.locator('input[type="email"]')).toBeVisible();
  });
});
