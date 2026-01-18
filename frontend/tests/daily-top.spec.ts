import { test, expect } from '@playwright/test';

test.describe('Homepage - Daily Top Insights', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should display page title', async ({ page }) => {
    await expect(page).toHaveTitle(/StartInsight/);
  });

  test('should display header with navigation', async ({ page }) => {
    // Check header exists
    const header = page.locator('header');
    await expect(header).toBeVisible();

    // Check logo/brand name
    const logo = page.locator('a', { hasText: 'StartInsight' });
    await expect(logo).toBeVisible();

    // Check navigation links
    const homeLink = page.locator('a', { hasText: 'Home' });
    await expect(homeLink).toBeVisible();

    const insightsLink = page.locator('a', { hasText: 'All Insights' });
    await expect(insightsLink).toBeVisible();
  });

  test('should display daily top insights', async ({ page }) => {
    // Wait for insights to load (or loading state)
    await page.waitForSelector('[data-testid="insight-card"], .skeleton', { timeout: 10000 });

    // Check for either insights or loading state
    const hasInsights = await page.locator('[data-testid="insight-card"]').count() > 0;
    const hasLoading = await page.locator('.skeleton').count() > 0;

    expect(hasInsights || hasLoading).toBeTruthy();
  });

  test('should display heading', async ({ page }) => {
    const heading = page.locator('h1', { hasText: 'Top Startup Insights' });
    await expect(heading).toBeVisible();
  });

  test('should navigate to All Insights page', async ({ page }) => {
    const allInsightsLink = page.locator('a', { hasText: 'All Insights' });
    await allInsightsLink.click();

    await expect(page).toHaveURL('/insights');
  });

  test('should display insight cards with key information', async ({ page }) => {
    // Wait for data to load
    await page.waitForSelector('[data-testid="insight-card"]', { timeout: 10000 });

    const firstCard = page.locator('[data-testid="insight-card"]').first();

    // Check card has problem statement
    await expect(firstCard.locator('.problem-statement')).toBeVisible();

    // Check card has proposed solution
    await expect(firstCard.locator('.proposed-solution')).toBeVisible();

    // Check card has relevance score (stars)
    await expect(firstCard.locator('.relevance-stars')).toBeVisible();

    // Check card has "View Details" button
    await expect(firstCard.locator('text=View Details')).toBeVisible();
  });

  test('should navigate to detail page when clicking View Details', async ({ page }) => {
    // Wait for insight cards to load
    await page.waitForSelector('[data-testid="insight-card"]', { timeout: 10000 });

    // Click first "View Details" button
    const viewDetailsButton = page.locator('text=View Details').first();
    await viewDetailsButton.click();

    // Should navigate to detail page
    await expect(page).toHaveURL(/\/insights\/[a-f0-9-]+/);
  });

  test('should display responsive grid layout', async ({ page }) => {
    // Wait for insights to load
    await page.waitForSelector('[data-testid="insight-card"], .skeleton', { timeout: 10000 });

    const grid = page.locator('.grid');
    await expect(grid).toBeVisible();

    // Grid should have responsive classes (check className includes grid)
    const gridClass = await grid.getAttribute('class');
    expect(gridClass).toContain('grid');
  });

  test('should handle empty state gracefully', async ({ page }) => {
    // If no insights, should show helpful message
    const hasCards = await page.locator('[data-testid="insight-card"]').count() > 0;
    const hasEmptyState = await page.locator('text=No insights available').count() > 0;

    expect(hasCards || hasEmptyState).toBeTruthy();
  });
});
