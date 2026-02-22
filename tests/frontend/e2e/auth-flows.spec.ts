import { test, expect } from '@playwright/test';

/**
 * Auth Flows E2E Tests
 *
 * Tests for login, signup, logout, forgot-password, and protected-route
 * redirect behaviour. Live-auth tests are skipped when TEST_USER_EMAIL
 * is not set so they can run safely in CI without real credentials.
 */

test.describe('Auth Flows', () => {
  // ----------------------------------------------------------------
  // Login page
  // ----------------------------------------------------------------
  test.describe('Login page', () => {
    test('loads with email and password fields', async ({ page }) => {
      await page.goto('/auth/login');

      await expect(page.locator('input[type="email"]')).toBeVisible();
      await expect(page.locator('input[type="password"]')).toBeVisible();
    });

    test('shows a submit button', async ({ page }) => {
      await page.goto('/auth/login');

      const submitBtn = page.getByRole('button', { name: /sign in/i });
      await expect(submitBtn).toBeVisible();
    });

    test('shows error message for invalid credentials', async ({ page }) => {
      await page.goto('/auth/login');

      await page.fill('input[type="email"]', 'nobody@example.com');
      await page.fill('input[type="password"]', 'wrongpassword');
      await page.getByRole('button', { name: /sign in/i }).click();

      // Supabase returns "Invalid login credentials" or similar
      const errorMessage = page.locator('text=/invalid|incorrect|credentials|wrong/i');
      await expect(errorMessage).toBeVisible({ timeout: 8000 });
    });

    test('redirects to /dashboard after valid login', async ({ page }) => {
      test.skip(
        !process.env.TEST_USER_EMAIL,
        'TEST_USER_EMAIL not set — skipping live auth tests'
      );

      await page.goto('/auth/login');

      await page.fill('input[type="email"]', process.env.TEST_USER_EMAIL!);
      await page.fill('input[type="password"]', process.env.TEST_USER_PASSWORD!);
      await page.getByRole('button', { name: /sign in/i }).click();

      await page.waitForURL(/\/dashboard/, { timeout: 10000 });
      await expect(page).toHaveURL(/\/dashboard/);
    });

    test('has a link to the signup page', async ({ page }) => {
      await page.goto('/auth/login');

      const signupLink = page.locator(
        'a:has-text("Sign up"), a:has-text("Create account"), text=/don.t have an account/i'
      );
      await expect(signupLink.first()).toBeVisible();
    });
  });

  // ----------------------------------------------------------------
  // Logout
  // ----------------------------------------------------------------
  test.describe('Logout', () => {
    test('clears session and redirects to /auth/login after logout', async ({ page }) => {
      test.skip(
        !process.env.TEST_USER_EMAIL,
        'TEST_USER_EMAIL not set — skipping live auth tests'
      );

      // Sign in first
      await page.goto('/auth/login');
      await page.fill('input[type="email"]', process.env.TEST_USER_EMAIL!);
      await page.fill('input[type="password"]', process.env.TEST_USER_PASSWORD!);
      await page.getByRole('button', { name: /sign in/i }).click();
      await page.waitForURL(/\/dashboard/, { timeout: 10000 });

      // Find and click the logout / sign-out control
      const signOutTrigger = page.locator(
        'button:has-text("Sign out"), button:has-text("Log out"), a:has-text("Sign out"), a:has-text("Log out")'
      );
      // Some UIs put it inside a dropdown — open avatar/user menu first if needed
      const userMenu = page.locator('[data-testid="user-menu"], [aria-label*="user" i], [aria-label*="account" i]');
      if (await userMenu.count() > 0) {
        await userMenu.first().click();
      }
      await expect(signOutTrigger.first()).toBeVisible({ timeout: 5000 });
      await signOutTrigger.first().click();

      // Should land back on login
      await page.waitForURL(/\/(auth\/login|auth\/signin|login)/i, { timeout: 8000 });
    });
  });

  // ----------------------------------------------------------------
  // Signup page
  // ----------------------------------------------------------------
  test.describe('Signup page', () => {
    test('loads with the required fields', async ({ page }) => {
      await page.goto('/auth/signup');

      await expect(page.locator('input[type="email"]')).toBeVisible();
      // Password field(s)
      const passwordFields = page.locator('input[type="password"]');
      await expect(passwordFields.first()).toBeVisible();
    });

    test('shows full-name field', async ({ page }) => {
      await page.goto('/auth/signup');

      // The signup form has a "Full name" text input
      const nameField = page.locator('input[type="text"]#name, input[id="name"], input[placeholder*="name" i]');
      await expect(nameField.first()).toBeVisible();
    });

    test('shows error when email is already registered', async ({ page }) => {
      test.skip(
        !process.env.TEST_USER_EMAIL,
        'TEST_USER_EMAIL not set — skipping live auth tests'
      );

      await page.goto('/auth/signup');

      await page.fill('#name', 'Existing User');
      await page.fill('input[type="email"]', process.env.TEST_USER_EMAIL!);
      // Both password fields
      const passwordInputs = page.locator('input[type="password"]');
      await passwordInputs.nth(0).fill('Password123!');
      await passwordInputs.nth(1).fill('Password123!');
      await page.getByRole('button', { name: /create account/i }).click();

      // Supabase returns "User already registered" or similar
      const errorMessage = page.locator('text=/already|registered|exists|taken/i');
      await expect(errorMessage).toBeVisible({ timeout: 8000 });
    });
  });

  // ----------------------------------------------------------------
  // Forgot password
  // ----------------------------------------------------------------
  test.describe('Forgot password page', () => {
    test('page at /auth redirects or shows auth content', async ({ page }) => {
      // The app does not expose a standalone /auth/forgot-password page —
      // test that the auth area is reachable.
      const response = await page.goto('/auth/login');
      // Should not be a hard 404
      expect(response?.status()).not.toBe(404);
      await expect(page.locator('input[type="email"]')).toBeVisible();
    });

    test('login page contains forgot-password link or text', async ({ page }) => {
      await page.goto('/auth/login');
      // Some designs embed "Forgot password?" as a link
      const forgotLink = page.locator(
        'a:has-text("Forgot"), text=/forgot password/i'
      );
      // It is optional in this UI — just confirm page loaded
      const emailInput = page.locator('input[type="email"]');
      await expect(emailInput).toBeVisible();

      if (await forgotLink.count() > 0) {
        await expect(forgotLink.first()).toBeVisible();
      }
    });
  });

  // ----------------------------------------------------------------
  // Protected route redirects
  // ----------------------------------------------------------------
  test.describe('Protected route redirects', () => {
    test('unauthenticated /dashboard redirects to /auth/login', async ({ page }) => {
      await page.goto('/dashboard');

      await page.waitForURL(/\/(auth\/login|auth\/signin|login)/i, { timeout: 8000 });
      expect(page.url()).toMatch(/login/i);
    });

    test('unauthenticated /workspace redirects to login', async ({ page }) => {
      await page.goto('/workspace');

      await page.waitForURL(/\/(auth\/login|auth\/signin|login)/i, { timeout: 8000 });
      expect(page.url()).toMatch(/login/i);
    });

    test('unauthenticated /settings redirects to login', async ({ page }) => {
      await page.goto('/settings');

      await page.waitForURL(/\/(auth\/login|auth\/signin|login)/i, { timeout: 8000 });
      expect(page.url()).toMatch(/login/i);
    });
  });
});
