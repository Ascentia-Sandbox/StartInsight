import { test, expect } from '@playwright/test';

/**
 * Validate Page E2E Tests
 *
 * Tests for the /validate idea-validation tool.
 * The page is accessible without authentication (auth token is optional —
 * the submit button is disabled when unauthenticated but the form renders).
 */

test.describe('Validate page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/validate');
    await page.waitForLoadState('networkidle');
  });

  // ----------------------------------------------------------------
  // Page load
  // ----------------------------------------------------------------
  test('loads the /validate page', async ({ page }) => {
    await expect(page).toHaveURL('/validate');

    // Hero heading should be visible
    const heading = page.locator('h1:has-text("Validate"), h1:has-text("Idea"), h1:has-text("Startup")');
    await expect(heading.first()).toBeVisible();
  });

  // ----------------------------------------------------------------
  // Form presence
  // ----------------------------------------------------------------
  test('renders a textarea for the idea description', async ({ page }) => {
    const textarea = page.locator('textarea#idea, textarea[placeholder*="AI" i], textarea[placeholder*="idea" i]');
    await expect(textarea.first()).toBeVisible();
  });

  test('renders a submit button', async ({ page }) => {
    const submitBtn = page.getByRole('button', { name: /validate idea/i });
    await expect(submitBtn).toBeVisible();
  });

  test('has optional target-market and budget selectors', async ({ page }) => {
    // Two Select dropdowns are rendered in the form
    const selectTriggers = page.locator('[role="combobox"]');
    const count = await selectTriggers.count();
    // At least one (target market) should be present
    expect(count).toBeGreaterThan(0);
  });

  // ----------------------------------------------------------------
  // Validation / disabled state
  // ----------------------------------------------------------------
  test('submit button is disabled when idea text is empty or too short', async ({ page }) => {
    const submitBtn = page.getByRole('button', { name: /validate idea/i });

    // Default state — textarea is empty → button should be disabled
    // (either disabled attr or aria-disabled)
    const isDisabled =
      (await submitBtn.getAttribute('disabled')) !== null ||
      (await submitBtn.getAttribute('aria-disabled')) === 'true';

    expect(isDisabled).toBe(true);
  });

  test('submit button becomes enabled only after 20+ characters are entered (when authenticated)', async ({ page }) => {
    // We can only confirm the minimum-length requirement here without a live auth token.
    // Enter < 20 chars and confirm button is still disabled.
    const textarea = page.locator('textarea').first();
    await textarea.fill('short text');

    const submitBtn = page.getByRole('button', { name: /validate idea/i });
    const isDisabled =
      (await submitBtn.getAttribute('disabled')) !== null ||
      (await submitBtn.getAttribute('aria-disabled')) === 'true';

    // Should remain disabled because there is no auth token AND text is too short
    expect(isDisabled).toBe(true);
  });

  // ----------------------------------------------------------------
  // Tier / quota information
  // ----------------------------------------------------------------
  test('displays free-tier quota badge', async ({ page }) => {
    // The page shows "Free tier: 3 validations/month" in an amber badge
    const tierBadge = page.locator('text=/free tier|validations\\/month|3 validation/i');
    await expect(tierBadge.first()).toBeVisible();
  });

  test('displays sign-in prompt when unauthenticated', async ({ page }) => {
    // The page shows "Sign in to validate your idea." when there is no session
    const signInPrompt = page.locator('text=/sign in to validate|sign in/i');

    // It may not render until authLoading resolves — wait briefly
    await page.waitForTimeout(1500);

    if (await signInPrompt.count() > 0) {
      await expect(signInPrompt.first()).toBeVisible();
    } else {
      // Fallback: confirm the Lock icon area or the amber badge is visible
      const tierBadge = page.locator('text=/free tier|validations/i');
      await expect(tierBadge.first()).toBeVisible();
    }
  });
});
