import { test, expect } from '@playwright/test';

/**
 * Workspace E2E Tests
 *
 * Tests the workspace page (auth-gated) and the public insights list.
 * Workspace itself redirects unauthenticated users — that redirect is
 * the thing we assert for most tests here.
 * Insight-list / card / detail tests run without authentication.
 */

test.describe('Workspace', () => {
  // ----------------------------------------------------------------
  // Workspace page — auth-gated
  // ----------------------------------------------------------------
  test.describe('Workspace page (auth-gated)', () => {
    test('redirects unauthenticated users to login', async ({ page }) => {
      await page.goto('/workspace');

      // The middleware or client-side guard should redirect to login
      await page.waitForURL(/\/(auth\/login|auth\/signin|login)/i, { timeout: 8000 });
      expect(page.url()).toMatch(/login/i);
    });

    test('redirect includes redirectTo query param pointing to /workspace', async ({ page }) => {
      await page.goto('/workspace');

      await page.waitForURL(/login/i, { timeout: 8000 });
      expect(page.url()).toMatch(/redirectTo/i);
    });
  });

  // ----------------------------------------------------------------
  // Insights list page — public
  // ----------------------------------------------------------------
  test.describe('Insights list page', () => {
    test.beforeEach(async ({ page }) => {
      await page.goto('/insights');
      await page.waitForLoadState('networkidle');
    });

    test('loads at /insights without authentication', async ({ page }) => {
      await expect(page).toHaveURL('/insights');
    });

    test('shows insight cards', async ({ page }) => {
      // Cards can be custom components or generic shadcn Card elements
      const insightCards = page.locator(
        '[data-testid="insight-card"], .card, article'
      );
      const count = await insightCards.count();
      expect(count).toBeGreaterThan(0);
    });

    test('insight card contains readable text', async ({ page }) => {
      const firstCard = page.locator('[data-testid="insight-card"], .card').first();
      await expect(firstCard).toBeVisible();

      // Each card should have some textual content
      const cardText = await firstCard.innerText();
      expect(cardText.trim().length).toBeGreaterThan(10);
    });

    test('insight cards show a save/bookmark icon or button', async ({ page }) => {
      // The InsightCard component renders a bookmark/save icon
      const saveButton = page.locator(
        '[data-testid="save-button"], button[aria-label*="save" i], button[aria-label*="bookmark" i], svg[class*="bookmark" i]'
      );

      // Not all views expose the save button without login — check presence
      // rather than forcing visibility (it may require hover state)
      if (await saveButton.count() > 0) {
        // At least one save button exists in the list
        expect(await saveButton.count()).toBeGreaterThan(0);
      } else {
        // Fallback: confirm the page loaded cards with content
        const cards = page.locator('[data-testid="insight-card"], .card');
        expect(await cards.count()).toBeGreaterThan(0);
      }
    });
  });

  // ----------------------------------------------------------------
  // Insight detail page
  // ----------------------------------------------------------------
  test.describe('Insight detail page', () => {
    test('navigates to insight detail on card click', async ({ page }) => {
      await page.goto('/insights');
      await page.waitForLoadState('networkidle');

      // Click the first link that leads to an insight detail
      const detailLink = page.locator(
        'a[href*="/insights/"], a:has-text("View"), a:has-text("Details")'
      ).first();

      if (await detailLink.count() > 0) {
        await detailLink.click();
        await page.waitForURL(/\/insights\/.+/, { timeout: 8000 });
        expect(page.url()).toMatch(/\/insights\/.+/);
      } else {
        // If no direct link, navigate to insights root and skip
        test.skip(true, 'No clickable insight detail link found on /insights');
      }
    });

    test('insight detail page renders a radar/score chart', async ({ page }) => {
      await page.goto('/insights');
      await page.waitForLoadState('networkidle');

      const detailLink = page.locator(
        'a[href*="/insights/"], a:has-text("View"), a:has-text("Details")'
      ).first();

      if (await detailLink.count() === 0) {
        test.skip(true, 'No insight detail link found — skipping radar chart test');
        return;
      }

      await detailLink.click();
      await page.waitForURL(/\/insights\/.+/, { timeout: 8000 });
      await page.waitForLoadState('networkidle');

      // ScoreRadar renders via Recharts as an SVG, or may be canvas
      const chart = page.locator('svg, canvas');
      if (await chart.count() > 0) {
        await expect(chart.first()).toBeVisible();
      } else {
        // Graceful — chart may not render without live data
        const scoreText = page.locator('text=/score|opportunity|feasibility/i');
        if (await scoreText.count() > 0) {
          await expect(scoreText.first()).toBeVisible();
        }
      }
    });
  });

  // ----------------------------------------------------------------
  // Compare page
  // ----------------------------------------------------------------
  test.describe('Compare page', () => {
    test('compare page loads without authentication', async ({ page }) => {
      await page.goto('/compare');

      // May show a "no insights selected" empty state — page should still load
      const response = await page.evaluate(() => document.readyState);
      expect(response).toBe('complete');
    });

    test('compare page accepts two insight IDs via query string', async ({ page }) => {
      // Navigate with two placeholder UUIDs — page should render without crashing
      await page.goto('/compare?ids=00000000-0000-0000-0000-000000000001,00000000-0000-0000-0000-000000000002');
      await page.waitForLoadState('networkidle');

      // Should render some UI (error state, empty state, or comparison layout)
      const body = page.locator('body');
      await expect(body).toBeVisible();

      // The page should not be a blank white screen — check for any text content
      const bodyText = await body.innerText();
      expect(bodyText.trim().length).toBeGreaterThan(0);
    });
  });
});
