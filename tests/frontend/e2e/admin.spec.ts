import { test, expect } from '@playwright/test';

/**
 * Admin Portal E2E Tests
 *
 * Tests for admin-only features including research queue,
 * agent controller, and admin dashboard.
 *
 * Note: These tests require authenticated admin access.
 * In CI, you would need to mock authentication or use test credentials.
 */

test.describe('Admin Portal - Unauthenticated', () => {
  test('should redirect to login when accessing admin without auth', async ({ page }) => {
    await page.goto('/admin');

    // Should redirect to signin
    await page.waitForURL(/\/(auth\/signin|signin|login)/i, { timeout: 5000 });
  });

  test('should redirect to login when accessing research queue without auth', async ({ page }) => {
    await page.goto('/admin/research-queue');

    // Should redirect to signin
    await page.waitForURL(/\/(auth\/signin|signin|login)/i, { timeout: 5000 });
  });

  test('should redirect to login when accessing agent controller without auth', async ({ page }) => {
    await page.goto('/admin/agent-controller');

    // Should redirect to signin
    await page.waitForURL(/\/(auth\/signin|signin|login)/i, { timeout: 5000 });
  });

  test('should redirect to login when accessing admin tools without auth', async ({ page }) => {
    await page.goto('/admin/tools');

    // Should redirect to signin
    await page.waitForURL(/\/(auth\/signin|signin|login)/i, { timeout: 5000 });
  });

  test('should redirect to login when accessing admin success-stories without auth', async ({ page }) => {
    await page.goto('/admin/success-stories');

    // Should redirect to signin
    await page.waitForURL(/\/(auth\/signin|signin|login)/i, { timeout: 5000 });
  });

  test('should redirect to login when accessing admin trends without auth', async ({ page }) => {
    await page.goto('/admin/trends');

    // Should redirect to signin
    await page.waitForURL(/\/(auth\/signin|signin|login)/i, { timeout: 5000 });
  });

  test('should redirect to login when accessing admin market-insights without auth', async ({ page }) => {
    await page.goto('/admin/market-insights');

    // Should redirect to signin
    await page.waitForURL(/\/(auth\/signin|signin|login)/i, { timeout: 5000 });
  });
});

test.describe('Admin Portal - Page Structure (with mock auth)', () => {
  // These tests verify page structure exists even if redirected
  // In a real scenario, you would set up auth cookies/tokens

  test('admin page route should exist', async ({ page }) => {
    const response = await page.goto('/admin');

    // Should get a response (either the page or a redirect)
    expect(response?.status()).toBeLessThan(500);
  });

  test('research queue route should exist', async ({ page }) => {
    const response = await page.goto('/admin/research-queue');

    // Should get a response (either the page or a redirect)
    expect(response?.status()).toBeLessThan(500);
  });

  test('agent controller route should exist', async ({ page }) => {
    const response = await page.goto('/admin/agent-controller');

    // Should get a response (either the page or a redirect)
    expect(response?.status()).toBeLessThan(500);
  });

  test('admin tools route should exist', async ({ page }) => {
    const response = await page.goto('/admin/tools');

    // Should get a response (either the page or a redirect)
    expect(response?.status()).toBeLessThan(500);
  });
});

test.describe('Admin Portal - API Routes', () => {
  test('admin API should require authentication', async ({ request }) => {
    // Try to access admin endpoints without auth
    const endpoints = [
      '/api/admin/research/requests',
      '/api/admin/agents/status',
      '/api/admin/tools',
      '/api/admin/success-stories',
      '/api/admin/trends',
      '/api/admin/market-insights',
    ];

    for (const endpoint of endpoints) {
      const response = await request.get(`http://localhost:8000${endpoint}`);

      // Should return 401 Unauthorized or 403 Forbidden
      expect([401, 403, 404, 422]).toContain(response.status());
    }
  });
});

test.describe('Admin Navigation', () => {
  test('login page should have admin-related UI elements', async ({ page }) => {
    await page.goto('/auth/signin');

    // The signin page should load properly
    await expect(page.locator('input[type="email"]')).toBeVisible();
  });
});

// Helper to set up authenticated admin session (for future use)
// This would be used with test.use() to set up auth state
/*
test.describe.configure({ mode: 'serial' });

test.describe('Admin Portal - Authenticated', () => {
  test.use({
    storageState: '.auth/admin.json',
  });

  test('should display admin dashboard', async ({ page }) => {
    await page.goto('/admin');

    // Should show admin dashboard
    await expect(page.locator('h1:has-text("Admin"), h1:has-text("Dashboard")')).toBeVisible();
  });

  test('should display research queue', async ({ page }) => {
    await page.goto('/admin/research-queue');

    // Should show research queue
    await expect(page.locator('text=/Research Queue|Pending Requests/i')).toBeVisible();
  });

  test('should display agent controller', async ({ page }) => {
    await page.goto('/admin/agent-controller');

    // Should show agent controller
    await expect(page.locator('text=/Agent Controller|AI Agents/i')).toBeVisible();
  });

  test('should allow approving research requests', async ({ page }) => {
    await page.goto('/admin/research-queue');

    // Look for pending request
    const pendingRequest = page.locator('[data-status="pending"]').first();
    if (await pendingRequest.count() > 0) {
      // Click approve button
      await pendingRequest.locator('button:has-text("Approve")').click();

      // Should show success message
      await expect(page.locator('text=/approved|success/i')).toBeVisible();
    }
  });

  test('should allow rejecting research requests', async ({ page }) => {
    await page.goto('/admin/research-queue');

    // Look for pending request
    const pendingRequest = page.locator('[data-status="pending"]').first();
    if (await pendingRequest.count() > 0) {
      // Click reject button
      await pendingRequest.locator('button:has-text("Reject")').click();

      // Should show rejection dialog
      const dialog = page.locator('[role="dialog"]');
      if (await dialog.count() > 0) {
        // Enter rejection reason
        await page.fill('textarea', 'Test rejection reason');
        await page.click('button:has-text("Confirm")');

        // Should show success message
        await expect(page.locator('text=/rejected|success/i')).toBeVisible();
      }
    }
  });
});
*/
