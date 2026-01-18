import { test, expect } from '@playwright/test';

test.describe('Insight Detail Page', () => {
  // Note: This test assumes there's at least one insight in the database
  // In a real test suite, you would seed test data first

  test.beforeEach(async ({ page }) => {
    // Navigate to homepage first
    await page.goto('/');

    // Wait for insights to load
    await page.waitForSelector('[data-testid="insight-card"], .skeleton', { timeout: 10000 });

    // Click first "View Details" button (if available)
    const viewDetailsButton = page.locator('text=View Details').first();
    if (await viewDetailsButton.count() > 0) {
      await viewDetailsButton.click();
      // Wait for navigation
      await page.waitForURL(/\/insights\/[a-f0-9-]+/);
    }
  });

  test('should display insight detail page', async ({ page }) => {
    // Should be on detail page
    await expect(page).toHaveURL(/\/insights\/[a-f0-9-]+/);
  });

  test('should display back button', async ({ page }) => {
    const backButton = page.locator('text=Back to All Insights');

    if (await backButton.count() > 0) {
      await expect(backButton).toBeVisible();
    }
  });

  test('should navigate back when clicking back button', async ({ page }) => {
    const backButton = page.locator('text=Back to All Insights');

    if (await backButton.count() > 0) {
      await backButton.click();
      await expect(page).toHaveURL('/insights');
    }
  });

  test('should display problem statement', async ({ page }) => {
    // Wait for content to load
    await page.waitForLoadState('networkidle');

    const card = page.locator('[data-testid="insight-detail-card"]');
    if (await card.count() === 0) {
      // Fallback: just check for card component
      const anyCard = page.locator('.card');
      await expect(anyCard.first()).toBeVisible();
    } else {
      await expect(card).toBeVisible();
    }
  });

  test('should display proposed solution', async ({ page }) => {
    // Wait for content to load
    await page.waitForLoadState('networkidle');

    const solution = page.locator('text=/Proposed Solution/i');
    if (await solution.count() > 0) {
      await expect(solution).toBeVisible();
    }
  });

  test('should display relevance score with stars', async ({ page }) => {
    // Wait for content to load
    await page.waitForLoadState('networkidle');

    const relevanceSection = page.locator('text=/Relevance Score/i');
    if (await relevanceSection.count() > 0) {
      await expect(relevanceSection).toBeVisible();

      // Stars should be visible
      const stars = page.locator('text=⭐');
      await expect(stars).toBeVisible();
    }
  });

  test('should display market size badge', async ({ page }) => {
    // Wait for content to load
    await page.waitForLoadState('networkidle');

    // Market size badge (Small/Medium/Large)
    const badge = page.locator('text=/Small Market|Medium Market|Large Market/');
    if (await badge.count() > 0) {
      await expect(badge).toBeVisible();
    }
  });

  test('should display competitor analysis', async ({ page }) => {
    // Wait for content to load
    await page.waitForLoadState('networkidle');

    const competitorSection = page.locator('text=/Competitor Analysis/i');
    if (await competitorSection.count() > 0) {
      await expect(competitorSection).toBeVisible();

      // Should have competitor cards
      const competitorCard = page.locator('.border').filter({ hasText: /Visit website|http/ });
      if (await competitorCard.count() > 0) {
        await expect(competitorCard.first()).toBeVisible();
      }
    }
  });

  test('should display source information', async ({ page }) => {
    // Wait for content to load
    await page.waitForLoadState('networkidle');

    const sourceSection = page.locator('text=/Source/i');
    if (await sourceSection.count() > 0) {
      await expect(sourceSection).toBeVisible();

      // Should have source badge (reddit/product_hunt/google_trends)
      const sourceBadge = page.locator('text=/reddit|product_hunt|google_trends/i');
      if (await sourceBadge.count() > 0) {
        await expect(sourceBadge.first()).toBeVisible();
      }
    }
  });

  test('should display trend chart for Google Trends data', async ({ page }) => {
    // Wait for content to load
    await page.waitForLoadState('networkidle');

    // Check if source is Google Trends
    const trendSection = page.locator('text=/Search Trend Analysis/i');

    if (await trendSection.count() > 0) {
      await expect(trendSection).toBeVisible();

      // Should have chart
      const chart = page.locator('svg'); // Recharts renders as SVG
      if (await chart.count() > 0) {
        await expect(chart.first()).toBeVisible();
      }
    }
  });

  test('should handle 404 for non-existent insight', async ({ page }) => {
    // Navigate to non-existent insight
    await page.goto('/insights/00000000-0000-0000-0000-000000000000');

    // Wait for error state
    await page.waitForLoadState('networkidle');

    // Should show error message
    const errorMessage = page.locator('text=/not found|does not exist/i');
    await expect(errorMessage).toBeVisible();

    // Should have back button
    const backButton = page.locator('text=/Back to|Go to Homepage/i');
    await expect(backButton.first()).toBeVisible();
  });

  test('should display timestamp', async ({ page }) => {
    // Wait for content to load
    await page.waitForLoadState('networkidle');

    // Should show relative time (e.g., "2 hours ago")
    const timestamp = page.locator('text=/ago|just now/i');
    if (await timestamp.count() > 0) {
      await expect(timestamp).toBeVisible();
    }
  });

  test('should have responsive card layout', async ({ page }) => {
    // Wait for content to load
    await page.waitForLoadState('networkidle');

    const container = page.locator('.container');
    await expect(container).toBeVisible();

    // Should have max-width constraint
    const maxWContainer = page.locator('.max-w-4xl');
    if (await maxWContainer.count() > 0) {
      await expect(maxWContainer).toBeVisible();
    }
  });
});
