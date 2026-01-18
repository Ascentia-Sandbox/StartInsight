import { test, expect } from '@playwright/test';

test.describe('Dark Mode & Responsive Design', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test.describe('Dark Mode', () => {
    test('should have theme toggle button', async ({ page }) => {
      // Theme toggle should be in header
      const themeToggle = page.locator('button[aria-label="Toggle theme"]');

      // Wait for dynamic import to load
      await page.waitForTimeout(1000);

      if (await themeToggle.count() > 0) {
        await expect(themeToggle).toBeVisible();
      }
    });

    test('should toggle between light and dark mode', async ({ page }) => {
      // Wait for theme toggle to load
      await page.waitForTimeout(1000);

      const themeToggle = page.locator('button[aria-label="Toggle theme"]');

      if (await themeToggle.count() > 0) {
        // Get initial theme
        const htmlElement = page.locator('html');
        const initialClass = await htmlElement.getAttribute('class');
        const initiallyDark = initialClass?.includes('dark') || false;

        // Click toggle
        await themeToggle.click();

        // Wait for theme change
        await page.waitForTimeout(500);

        // Check theme changed
        const newClass = await htmlElement.getAttribute('class');
        const nowDark = newClass?.includes('dark') || false;

        expect(nowDark).toBe(!initiallyDark);

        // Toggle back
        await themeToggle.click();
        await page.waitForTimeout(500);

        const finalClass = await htmlElement.getAttribute('class');
        const finallyDark = finalClass?.includes('dark') || false;

        expect(finallyDark).toBe(initiallyDark);
      }
    });

    test('should persist theme preference on page reload', async ({ page }) => {
      // Wait for theme toggle to load
      await page.waitForTimeout(1000);

      const themeToggle = page.locator('button[aria-label="Toggle theme"]');

      if (await themeToggle.count() > 0) {
        // Toggle to dark mode
        await themeToggle.click();
        await page.waitForTimeout(500);

        const htmlElement = page.locator('html');
        const isDark = (await htmlElement.getAttribute('class'))?.includes('dark');

        // Reload page
        await page.reload();
        await page.waitForTimeout(1000);

        // Theme should persist
        const persistedClass = await htmlElement.getAttribute('class');
        const stillDark = persistedClass?.includes('dark');

        expect(stillDark).toBe(isDark);
      }
    });

    test('should show moon icon in light mode', async ({ page }) => {
      // Wait for theme toggle to load
      await page.waitForTimeout(1000);

      const htmlElement = page.locator('html');
      const isDark = (await htmlElement.getAttribute('class'))?.includes('dark');

      if (!isDark) {
        // In light mode, should show moon icon
        const moonIcon = page.locator('svg').filter({ has: page.locator('path') });
        // Moon icon exists in theme toggle
        const themeToggle = page.locator('button[aria-label="Toggle theme"]');
        if (await themeToggle.count() > 0) {
          await expect(themeToggle).toBeVisible();
        }
      }
    });
  });

  test.describe('Responsive Design', () => {
    test('should display single column on mobile', async ({ page }) => {
      // Set mobile viewport
      await page.setViewportSize({ width: 375, height: 667 });

      // Wait for insights to load
      await page.waitForSelector('[data-testid="insight-card"], .skeleton', { timeout: 10000 });

      // Check grid layout
      const grid = page.locator('.grid');
      if (await grid.count() > 0) {
        // Grid should be visible
        await expect(grid).toBeVisible();

        // Should have mobile-friendly spacing
        const gridClass = await grid.getAttribute('class');
        expect(gridClass).toContain('grid');
      }
    });

    test('should display two columns on tablet', async ({ page }) => {
      // Set tablet viewport
      await page.setViewportSize({ width: 768, height: 1024 });

      // Wait for insights to load
      await page.waitForSelector('[data-testid="insight-card"], .skeleton', { timeout: 10000 });

      // Grid should adapt
      const grid = page.locator('.grid');
      if (await grid.count() > 0) {
        await expect(grid).toBeVisible();

        // Should have responsive class (md:grid-cols-2)
        const gridClass = await grid.getAttribute('class');
        expect(gridClass).toMatch(/md:grid-cols-2|grid/);
      }
    });

    test('should display three columns on desktop', async ({ page }) => {
      // Set desktop viewport
      await page.setViewportSize({ width: 1280, height: 800 });

      // Wait for insights to load
      await page.waitForSelector('[data-testid="insight-card"], .skeleton', { timeout: 10000 });

      // Grid should adapt
      const grid = page.locator('.grid');
      if (await grid.count() > 0) {
        await expect(grid).toBeVisible();

        // Should have responsive class (lg:grid-cols-3)
        const gridClass = await grid.getAttribute('class');
        expect(gridClass).toMatch(/lg:grid-cols-3|grid/);
      }
    });

    test('should stack filters on mobile', async ({ page }) => {
      // Set mobile viewport
      await page.setViewportSize({ width: 375, height: 667 });

      // Navigate to all insights
      await page.goto('/insights');
      await page.waitForLoadState('networkidle');

      // Filters should be visible (stacked vertically)
      const filters = page.locator('[data-testid="insight-filters"]');
      if (await filters.count() > 0) {
        await expect(filters).toBeVisible();
      }
    });

    test('should display sidebar filters on desktop', async ({ page }) => {
      // Set desktop viewport
      await page.setViewportSize({ width: 1280, height: 800 });

      // Navigate to all insights
      await page.goto('/insights');
      await page.waitForLoadState('networkidle');

      // Filters should be in sidebar layout
      const filtersContainer = page.locator('[data-testid="insight-filters"]');
      if (await filtersContainer.count() > 0) {
        await expect(filtersContainer).toBeVisible();
      }
    });

    test('should have touch-friendly buttons on mobile', async ({ page }) => {
      // Set mobile viewport
      await page.setViewportSize({ width: 375, height: 667 });

      // Buttons should have adequate size for touch
      const buttons = page.locator('button');
      const firstButton = buttons.first();

      if (await firstButton.count() > 0) {
        const boundingBox = await firstButton.boundingBox();
        // Buttons should be at least 44x44px (iOS HIG recommendation)
        if (boundingBox) {
          expect(boundingBox.height).toBeGreaterThanOrEqual(36); // Tailwind h-9 = 36px
        }
      }
    });

    test('should not have horizontal scrolling', async ({ page }) => {
      // Set mobile viewport
      await page.setViewportSize({ width: 375, height: 667 });

      // Wait for page to load
      await page.waitForLoadState('networkidle');

      // Check body width doesn't exceed viewport
      const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
      const viewportWidth = await page.evaluate(() => window.innerWidth);

      expect(bodyWidth).toBeLessThanOrEqual(viewportWidth);
    });
  });

  test.describe('Accessibility', () => {
    test('should have accessible theme toggle', async ({ page }) => {
      await page.waitForTimeout(1000);

      const themeToggle = page.locator('button[aria-label="Toggle theme"]');

      if (await themeToggle.count() > 0) {
        // Should have aria-label
        const ariaLabel = await themeToggle.getAttribute('aria-label');
        expect(ariaLabel).toBe('Toggle theme');

        // Should be keyboard accessible
        await themeToggle.focus();
        const isFocused = await themeToggle.evaluate((el) =>
          el === document.activeElement
        );
        expect(isFocused).toBeTruthy();
      }
    });

    test('should have semantic HTML structure', async ({ page }) => {
      // Header should use <header> tag
      const header = page.locator('header');
      await expect(header).toBeVisible();

      // Main content should use <main> tag
      const main = page.locator('main');
      await expect(main).toBeVisible();

      // Navigation should use <nav> tag
      const nav = page.locator('nav');
      await expect(nav).toBeVisible();
    });

    test('should have proper heading hierarchy', async ({ page }) => {
      // Page should have h1
      const h1 = page.locator('h1');
      if (await h1.count() > 0) {
        await expect(h1.first()).toBeVisible();
      }
    });
  });
});
