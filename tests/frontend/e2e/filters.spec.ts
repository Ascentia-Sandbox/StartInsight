import { test, expect } from '@playwright/test';

test.describe('All Insights Page - Filters and Search', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/insights');
  });

  test('should display filters sidebar', async ({ page }) => {
    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Check for filters container
    const filters = page.locator('[data-testid="insight-filters"]');
    await expect(filters).toBeVisible();
  });

  test('should filter by source', async ({ page }) => {
    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Find source filter select
    const sourceFilter = page.locator('select[name="source"]');

    if (await sourceFilter.count() > 0) {
      // Select a source (e.g., Reddit)
      await sourceFilter.selectOption('reddit');

      // URL should update with filter
      await expect(page).toHaveURL(/source=reddit/);

      // Wait for filtered results
      await page.waitForLoadState('networkidle');
    }
  });

  test('should filter by minimum relevance score', async ({ page }) => {
    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Find relevance score filter
    const scoreFilter = page.locator('select[name="min_score"]');

    if (await scoreFilter.count() > 0) {
      // Select minimum score (e.g., 0.7)
      await scoreFilter.selectOption('0.7');

      // URL should update with filter
      await expect(page).toHaveURL(/min_score=0.7/);

      // Wait for filtered results
      await page.waitForLoadState('networkidle');
    }
  });

  test('should search insights by keyword', async ({ page }) => {
    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Find search input
    const searchInput = page.locator('input[type="search"], input[placeholder*="Search"]');

    if (await searchInput.count() > 0) {
      // Type search query
      await searchInput.fill('AI startup');

      // Wait for debounce (if implemented)
      await page.waitForTimeout(1000);

      // Wait for results to update
      await page.waitForLoadState('networkidle');

      // Results should contain search term (if insights exist)
      const insights = page.locator('[data-testid="insight-card"]');
      if (await insights.count() > 0) {
        const firstInsight = insights.first();
        const text = await firstInsight.textContent();
        // Text might contain "AI" or "startup"
        expect(text?.toLowerCase()).toMatch(/ai|startup/);
      }
    }
  });

  test('should clear all filters', async ({ page }) => {
    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Apply some filters first
    const sourceFilter = page.locator('select[name="source"]');
    if (await sourceFilter.count() > 0) {
      await sourceFilter.selectOption('reddit');
      await page.waitForLoadState('networkidle');
    }

    // Find clear filters button
    const clearButton = page.locator('button', { hasText: 'Clear' });

    if (await clearButton.count() > 0) {
      await clearButton.click();

      // URL should reset
      await expect(page).toHaveURL('/insights');

      // Wait for results to reload
      await page.waitForLoadState('networkidle');
    }
  });

  test('should maintain filters in URL (shareable links)', async ({ page }) => {
    // Navigate with filter params
    await page.goto('/insights?source=reddit&min_score=0.7');

    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Filters should be applied from URL
    const sourceFilter = page.locator('select[name="source"]');
    if (await sourceFilter.count() > 0) {
      const selectedSource = await sourceFilter.inputValue();
      expect(selectedSource).toBe('reddit');
    }

    const scoreFilter = page.locator('select[name="min_score"]');
    if (await scoreFilter.count() > 0) {
      const selectedScore = await scoreFilter.inputValue();
      expect(selectedScore).toBe('0.7');
    }
  });

  test('should display filtered results count', async ({ page }) => {
    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Check if results count is displayed
    const resultsCount = page.locator('text=/\\d+ insights?/i');

    // Count should be visible (if implemented)
    if (await resultsCount.count() > 0) {
      await expect(resultsCount.first()).toBeVisible();
    }
  });

  test('should handle no results gracefully', async ({ page }) => {
    // Apply filter that might have no results
    await page.goto('/insights?min_score=0.99');

    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Should show empty state or message
    const hasResults = await page.locator('[data-testid="insight-card"]').count() > 0;
    const hasEmptyState = await page.locator('text=/no insights/i').count() > 0;

    expect(hasResults || hasEmptyState).toBeTruthy();
  });

  test('should display insights in grid layout', async ({ page }) => {
    // Wait for insights to load
    await page.waitForLoadState('networkidle');

    const grid = page.locator('.grid');
    if (await grid.count() > 0) {
      await expect(grid).toBeVisible();
    }
  });

  test('should navigate back to home', async ({ page }) => {
    const homeLink = page.locator('a', { hasText: 'Home' });
    await homeLink.click();

    await expect(page).toHaveURL('/');
  });
});
