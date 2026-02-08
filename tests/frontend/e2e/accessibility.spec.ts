import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

/**
 * Accessibility Audit Tests (WCAG 2.1 AA Compliance)
 *
 * These tests run automated accessibility checks using axe-core on all major pages.
 *
 * Audit Scope:
 * - WCAG 2.1 Level AA compliance
 * - Keyboard navigation
 * - Screen reader support
 * - Color contrast
 * - ARIA attributes
 *
 * Test Coverage:
 * - Homepage
 * - Insights list page
 * - Insight detail page
 * - Dashboard (if authenticated)
 * - Research page
 * - Interactive components (charts, modals, forms)
 */

test.describe('Accessibility Audit - Public Pages', () => {
  test('Homepage should have no accessibility violations', async ({ page }) => {
    await page.goto('/');

    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('Insights list page should have no accessibility violations', async ({ page }) => {
    await page.goto('/insights');

    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('Insight detail page should have no accessibility violations', async ({ page }) => {
    // Navigate to insights list first
    await page.goto('/insights');

    // Wait for insights to load
    await page.waitForSelector('[data-testid="insight-card"]', { timeout: 10000 });

    // Click on first insight
    const firstInsight = page.locator('[data-testid="insight-card"]').first();
    await firstInsight.click();

    // Wait for detail page to load
    await page.waitForLoadState('networkidle');

    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('Research page should have no accessibility violations', async ({ page }) => {
    await page.goto('/research');

    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });
});

test.describe('Accessibility - Interactive Components', () => {
  test('TrendChart should be accessible', async ({ page }) => {
    // Navigate to insight detail with Google Trends data
    await page.goto('/insights');
    await page.waitForSelector('[data-testid="insight-card"]', { timeout: 10000 });

    // Find insight with Google Trends source badge
    const trendInsight = page.locator('[data-testid="insight-card"]:has-text("google_trends")').first();

    // If no Google Trends insights, skip test
    const count = await trendInsight.count();
    if (count === 0) {
      test.skip();
      return;
    }

    await trendInsight.click();
    await page.waitForLoadState('networkidle');

    // Wait for TrendChart to render
    await page.waitForSelector('text=Search Trend Analysis', { timeout: 10000 });

    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .include('[role="region"]:has-text("Search Trend Analysis")')
      .analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('ScoreRadar should be accessible', async ({ page }) => {
    // Navigate to insight detail
    await page.goto('/insights');
    await page.waitForSelector('[data-testid="insight-card"]', { timeout: 10000 });

    const firstInsight = page.locator('[data-testid="insight-card"]').first();
    await firstInsight.click();
    await page.waitForLoadState('networkidle');

    // Wait for ScoreRadar to render
    await page.waitForSelector('text=Multi-Dimensional Quality Score', { timeout: 10000 });

    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .include('[role="region"]:has-text("Multi-Dimensional Quality Score")')
      .analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('Modal dialogs should be accessible', async ({ page }) => {
    // Navigate to insight detail
    await page.goto('/insights');
    await page.waitForSelector('[data-testid="insight-card"]', { timeout: 10000 });

    const firstInsight = page.locator('[data-testid="insight-card"]').first();
    await firstInsight.click();
    await page.waitForLoadState('networkidle');

    // Wait for ScoreRadar
    await page.waitForSelector('text=Multi-Dimensional Quality Score', { timeout: 10000 });

    // Click on a radar chart dimension to open modal
    const radarChart = page.locator('[role="region"]:has-text("Multi-Dimensional Quality Score")');
    await radarChart.click({ position: { x: 200, y: 200 } });

    // Wait for modal to appear
    await page.waitForTimeout(500);

    // Check if modal opened
    const modal = page.locator('[role="dialog"]');
    const modalCount = await modal.count();

    if (modalCount > 0) {
      const accessibilityScanResults = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
        .include('[role="dialog"]')
        .analyze();

      expect(accessibilityScanResults.violations).toEqual([]);
    }
  });
});

test.describe('Accessibility - Keyboard Navigation', () => {
  test('Homepage should be fully keyboard navigable', async ({ page }) => {
    await page.goto('/');

    // Press Tab to navigate through focusable elements
    await page.keyboard.press('Tab');

    // Check if focus indicator is visible
    const focusedElement = await page.locator(':focus').first();
    const focusedCount = await focusedElement.count();

    expect(focusedCount).toBeGreaterThan(0);
  });

  test('Insights list should be keyboard navigable', async ({ page }) => {
    await page.goto('/insights');
    await page.waitForSelector('[data-testid="insight-card"]', { timeout: 10000 });

    // Navigate to first insight card using Tab
    let tabCount = 0;
    let foundInsightCard = false;

    while (tabCount < 20 && !foundInsightCard) {
      await page.keyboard.press('Tab');
      tabCount++;

      const focusedElement = await page.locator(':focus').first();
      const testId = await focusedElement.getAttribute('data-testid');

      if (testId === 'insight-card' || await focusedElement.locator('[data-testid="insight-card"]').count() > 0) {
        foundInsightCard = true;
      }
    }

    expect(foundInsightCard).toBeTruthy();

    // Press Enter to navigate to detail page
    await page.keyboard.press('Enter');
    await page.waitForLoadState('networkidle');

    // Verify we navigated to detail page
    expect(page.url()).toContain('/insights/');
  });

  test('Chart controls should be keyboard accessible', async ({ page }) => {
    // Navigate to insight with Google Trends
    await page.goto('/insights');
    await page.waitForSelector('[data-testid="insight-card"]', { timeout: 10000 });

    const trendInsight = page.locator('[data-testid="insight-card"]:has-text("google_trends")').first();
    const count = await trendInsight.count();

    if (count === 0) {
      test.skip();
      return;
    }

    await trendInsight.click();
    await page.waitForLoadState('networkidle');

    // Wait for TrendChart
    await page.waitForSelector('text=Search Trend Analysis', { timeout: 10000 });

    // Tab to chart controls (date range selector, export button, etc.)
    let tabCount = 0;
    let foundChartControl = false;

    while (tabCount < 30 && !foundChartControl) {
      await page.keyboard.press('Tab');
      tabCount++;

      const focusedElement = await page.locator(':focus').first();
      const text = await focusedElement.textContent();

      if (text && (text.includes('Export') || text.includes('Reset') || text.includes('Last'))) {
        foundChartControl = true;
      }
    }

    expect(foundChartControl).toBeTruthy();
  });

  test('Modal dialogs should trap focus', async ({ page }) => {
    // Navigate to insight detail
    await page.goto('/insights');
    await page.waitForSelector('[data-testid="insight-card"]', { timeout: 10000 });

    const firstInsight = page.locator('[data-testid="insight-card"]').first();
    await firstInsight.click();
    await page.waitForLoadState('networkidle');

    // Wait for ScoreRadar
    await page.waitForSelector('text=Multi-Dimensional Quality Score', { timeout: 10000 });

    // Click on radar chart to open modal
    const radarChart = page.locator('[role="region"]:has-text("Multi-Dimensional Quality Score")');
    await radarChart.click({ position: { x: 200, y: 200 } });

    await page.waitForTimeout(500);

    const modal = page.locator('[role="dialog"]');
    const modalCount = await modal.count();

    if (modalCount > 0) {
      // Tab through modal elements
      let tabCount = 0;
      const focusableElements: string[] = [];

      while (tabCount < 10) {
        await page.keyboard.press('Tab');
        tabCount++;

        const focusedElement = await page.locator(':focus').first();
        const role = await focusedElement.getAttribute('role');
        const tagName = await focusedElement.evaluate((el) => el.tagName);

        focusableElements.push(`${tagName}[${role}]`);

        // Check if focus is still within modal
        const isInModal = await focusedElement.evaluate((el, modalSelector) => {
          const modalEl = document.querySelector(modalSelector);
          return modalEl?.contains(el) ?? false;
        }, '[role="dialog"]');

        expect(isInModal).toBeTruthy();
      }
    }
  });
});

test.describe('Accessibility - Screen Reader Support', () => {
  test('Charts should have ARIA labels', async ({ page }) => {
    // Navigate to insight with charts
    await page.goto('/insights');
    await page.waitForSelector('[data-testid="insight-card"]', { timeout: 10000 });

    const firstInsight = page.locator('[data-testid="insight-card"]').first();
    await firstInsight.click();
    await page.waitForLoadState('networkidle');

    // Check for aria-label or aria-labelledby on chart containers
    const chartRegions = page.locator('[role="region"]');
    const chartCount = await chartRegions.count();

    if (chartCount > 0) {
      for (let i = 0; i < chartCount; i++) {
        const chart = chartRegions.nth(i);
        const ariaLabel = await chart.getAttribute('aria-label');
        const ariaLabelledBy = await chart.getAttribute('aria-labelledby');

        // At least one should be present
        expect(ariaLabel || ariaLabelledBy).toBeTruthy();
      }
    }
  });

  test('Interactive elements should have descriptive labels', async ({ page }) => {
    await page.goto('/insights');
    await page.waitForSelector('[data-testid="insight-card"]', { timeout: 10000 });

    // Check all buttons have accessible names
    const buttons = page.locator('button');
    const buttonCount = await buttons.count();

    for (let i = 0; i < Math.min(buttonCount, 20); i++) {
      const button = buttons.nth(i);
      const ariaLabel = await button.getAttribute('aria-label');
      const textContent = await button.textContent();
      const ariaLabelledBy = await button.getAttribute('aria-labelledby');

      // Button should have text, aria-label, or aria-labelledby
      expect(ariaLabel || textContent || ariaLabelledBy).toBeTruthy();
    }
  });

  test('Live regions should announce dynamic updates', async ({ page }) => {
    // Navigate to insight with live trend data
    await page.goto('/insights');
    await page.waitForSelector('[data-testid="insight-card"]', { timeout: 10000 });

    const trendInsight = page.locator('[data-testid="insight-card"]:has-text("google_trends")').first();
    const count = await trendInsight.count();

    if (count === 0) {
      test.skip();
      return;
    }

    await trendInsight.click();
    await page.waitForLoadState('networkidle');

    // Check for aria-live regions
    const liveRegions = page.locator('[aria-live]');
    const liveRegionCount = await liveRegions.count();

    // If TrendChart has live updates, it should have aria-live
    const hasLiveBadge = await page.locator('text=Live').count();

    if (hasLiveBadge > 0) {
      expect(liveRegionCount).toBeGreaterThan(0);
    }
  });
});

test.describe('Accessibility - Color Contrast', () => {
  test('Text should meet WCAG AA contrast requirements', async ({ page }) => {
    await page.goto('/');

    // axe-core will check contrast as part of WCAG 2.1 AA tests
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2aa'])
      .analyze();

    // Filter for contrast violations
    const contrastViolations = accessibilityScanResults.violations.filter(
      (v) => v.id === 'color-contrast'
    );

    expect(contrastViolations).toEqual([]);
  });

  test('Dark mode should maintain contrast', async ({ page }) => {
    await page.goto('/');

    // Toggle dark mode
    const darkModeToggle = page.locator('[aria-label*="dark" i], [aria-label*="theme" i]').first();
    const toggleCount = await darkModeToggle.count();

    if (toggleCount > 0) {
      await darkModeToggle.click();
      await page.waitForTimeout(500);

      const accessibilityScanResults = await new AxeBuilder({ page })
        .withTags(['wcag2aa'])
        .analyze();

      const contrastViolations = accessibilityScanResults.violations.filter(
        (v) => v.id === 'color-contrast'
      );

      expect(contrastViolations).toEqual([]);
    }
  });
});
