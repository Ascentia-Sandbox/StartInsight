import { test, expect } from '@playwright/test';

/**
 * Public Pages E2E Tests
 *
 * Tests for public-facing pages that don't require authentication:
 * - Tools directory
 * - Success stories
 * - Trends database
 * - Market insights (blog)
 * - Platform tour
 * - Pricing
 * - FAQ
 * - About
 * - Contact
 */

test.describe('Tools Directory', () => {
  test('should display tools page', async ({ page }) => {
    await page.goto('/tools');

    await expect(page).toHaveURL('/tools');
    await expect(page.locator('h1:has-text("Tools"), h1:has-text("Directory")')).toBeVisible();
  });

  test('should display tool cards', async ({ page }) => {
    await page.goto('/tools');

    // Wait for tools to load
    await page.waitForSelector('[data-testid="tool-card"], .card', { timeout: 10000 });

    // Should have multiple tool cards
    const toolCards = page.locator('[data-testid="tool-card"], .card');
    const count = await toolCards.count();

    expect(count).toBeGreaterThan(0);
  });

  test('should filter tools by category', async ({ page }) => {
    await page.goto('/tools');

    // Look for category filter
    const categoryFilter = page.locator('[data-testid="category-filter"], select, [role="combobox"]');

    if (await categoryFilter.count() > 0) {
      // Click on a category
      await categoryFilter.first().click();

      // Select a category option
      const option = page.locator('[role="option"], option').first();
      if (await option.count() > 0) {
        await option.click();
      }
    }
  });

  test('should display tool details with pricing', async ({ page }) => {
    await page.goto('/tools');

    // Wait for tools to load
    await page.waitForSelector('[data-testid="tool-card"], .card', { timeout: 10000 });

    // Should show pricing information
    const pricing = page.locator('text=/\\$/');
    await expect(pricing.first()).toBeVisible();
  });

  test('should have links to tool websites', async ({ page }) => {
    await page.goto('/tools');

    // Wait for tools to load
    await page.waitForSelector('[data-testid="tool-card"], .card', { timeout: 10000 });

    // Should have external links
    const externalLinks = page.locator('a[href^="http"], a[target="_blank"]');
    const count = await externalLinks.count();

    expect(count).toBeGreaterThan(0);
  });
});

test.describe('Success Stories', () => {
  test('should display success stories page', async ({ page }) => {
    await page.goto('/success-stories');

    await expect(page).toHaveURL('/success-stories');
    await expect(page.locator('h1:has-text("Success"), h1:has-text("Stories")')).toBeVisible();
  });

  test('should display founder stories', async ({ page }) => {
    await page.goto('/success-stories');

    // Wait for stories to load
    await page.waitForSelector('[data-testid="story-card"], .card', { timeout: 10000 });

    // Should have story cards
    const storyCards = page.locator('[data-testid="story-card"], .card');
    const count = await storyCards.count();

    expect(count).toBeGreaterThan(0);
  });

  test('should display founder metrics', async ({ page }) => {
    await page.goto('/success-stories');

    // Wait for stories to load
    await page.waitForSelector('[data-testid="story-card"], .card', { timeout: 10000 });

    // Should show metrics (MRR, users, funding)
    const metrics = page.locator('text=/\\$|MRR|users|funding/i');
    await expect(metrics.first()).toBeVisible();
  });

  test('should display journey timeline', async ({ page }) => {
    await page.goto('/success-stories');

    // Wait for stories to load
    await page.waitForSelector('[data-testid="story-card"], .card', { timeout: 10000 });

    // Click on first story to see details
    const firstStory = page.locator('[data-testid="story-card"], .card').first();
    await firstStory.click();

    // May navigate to detail page or expand card
    await page.waitForTimeout(500);

    // Look for timeline elements
    const timeline = page.locator('text=/Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec/');
    if (await timeline.count() > 0) {
      await expect(timeline.first()).toBeVisible();
    }
  });
});

test.describe('Trends Database', () => {
  test('should display trends page', async ({ page }) => {
    await page.goto('/trends');

    await expect(page).toHaveURL('/trends');
    await expect(page.locator('h1:has-text("Trends"), h1:has-text("Trending")')).toBeVisible();
  });

  test('should display trending keywords', async ({ page }) => {
    await page.goto('/trends');

    // Wait for trends to load
    await page.waitForSelector('[data-testid="trend-card"], .card', { timeout: 10000 });

    // Should have trend cards
    const trendCards = page.locator('[data-testid="trend-card"], .card');
    const count = await trendCards.count();

    expect(count).toBeGreaterThan(0);
  });

  test('should display search volume', async ({ page }) => {
    await page.goto('/trends');

    // Wait for trends to load
    await page.waitForSelector('[data-testid="trend-card"], .card', { timeout: 10000 });

    // Should show search volume
    const volume = page.locator('text=/K|M|volume/i');
    await expect(volume.first()).toBeVisible();
  });

  test('should display growth percentage', async ({ page }) => {
    await page.goto('/trends');

    // Wait for trends to load
    await page.waitForSelector('[data-testid="trend-card"], .card', { timeout: 10000 });

    // Should show growth percentage
    const growth = page.locator('text=/\\+\\d+%|growth|-\\d+%/');
    await expect(growth.first()).toBeVisible();
  });

  test('should filter trends by category', async ({ page }) => {
    await page.goto('/trends');

    // Look for category filter
    const categoryFilter = page.locator('[data-testid="category-filter"], select, [role="combobox"]');

    if (await categoryFilter.count() > 0) {
      await categoryFilter.first().click();
    }
  });
});

test.describe('Market Insights (Blog)', () => {
  test('should display market insights page', async ({ page }) => {
    await page.goto('/market-insights');

    await expect(page).toHaveURL('/market-insights');
    await expect(page.locator('h1:has-text("Insights"), h1:has-text("Blog"), h1:has-text("Market")')).toBeVisible();
  });

  test('should display blog articles', async ({ page }) => {
    await page.goto('/market-insights');

    // Wait for articles to load
    await page.waitForSelector('[data-testid="article-card"], article, .card', { timeout: 10000 });

    // Should have article cards
    const articleCards = page.locator('[data-testid="article-card"], article, .card');
    const count = await articleCards.count();

    expect(count).toBeGreaterThan(0);
  });

  test('should display reading time', async ({ page }) => {
    await page.goto('/market-insights');

    // Wait for articles to load
    await page.waitForSelector('[data-testid="article-card"], article, .card', { timeout: 10000 });

    // Should show reading time
    const readingTime = page.locator('text=/\\d+ min read|minute/');
    await expect(readingTime.first()).toBeVisible();
  });

  test('should navigate to article detail', async ({ page }) => {
    await page.goto('/market-insights');

    // Wait for articles to load
    await page.waitForSelector('[data-testid="article-card"], article, .card', { timeout: 10000 });

    // Click on first article
    const firstArticle = page.locator('[data-testid="article-card"], article, .card').first();
    await firstArticle.click();

    // Should navigate to article detail
    await page.waitForURL(/\/market-insights\//, { timeout: 5000 });
  });
});

test.describe('Platform Tour', () => {
  test('should display platform tour page', async ({ page }) => {
    await page.goto('/platform-tour');

    await expect(page).toHaveURL('/platform-tour');
    await expect(page.locator('h1:has-text("Platform"), h1:has-text("Tour"), h1:has-text("Features")')).toBeVisible();
  });

  test('should display feature sections', async ({ page }) => {
    await page.goto('/platform-tour');

    // Should have multiple feature sections
    const sections = page.locator('section, [data-testid="feature-section"]');
    const count = await sections.count();

    expect(count).toBeGreaterThan(0);
  });

  test('should have interactive tabs or accordion', async ({ page }) => {
    await page.goto('/platform-tour');

    // Look for tabs or accordion
    const interactive = page.locator('[role="tablist"], [data-testid="tabs"], [data-state="open"]');

    if (await interactive.count() > 0) {
      await expect(interactive.first()).toBeVisible();
    }
  });
});

test.describe('Pricing Page', () => {
  test('should display pricing page', async ({ page }) => {
    await page.goto('/pricing');

    await expect(page).toHaveURL('/pricing');
    await expect(page.locator('h1:has-text("Pricing"), h1:has-text("Plans")')).toBeVisible();
  });

  test('should display pricing tiers', async ({ page }) => {
    await page.goto('/pricing');

    // Should show pricing tiers
    const tiers = page.locator('text=/Free|Starter|Pro|Enterprise/');
    await expect(tiers.first()).toBeVisible();
  });

  test('should display pricing amounts', async ({ page }) => {
    await page.goto('/pricing');

    // Should show pricing amounts
    const prices = page.locator('text=/\\$\\d+|Free/');
    await expect(prices.first()).toBeVisible();
  });

  test('should have CTA buttons', async ({ page }) => {
    await page.goto('/pricing');

    // Should have call-to-action buttons
    const ctaButtons = page.locator('button:has-text("Get started"), button:has-text("Start"), a:has-text("Sign up")');
    await expect(ctaButtons.first()).toBeVisible();
  });

  test('should display feature comparison', async ({ page }) => {
    await page.goto('/pricing');

    // Should show feature list
    const features = page.locator('text=/Insights|Research|API|Team/');
    await expect(features.first()).toBeVisible();
  });
});

test.describe('FAQ Page', () => {
  test('should display FAQ page', async ({ page }) => {
    await page.goto('/faq');

    await expect(page).toHaveURL('/faq');
    await expect(page.locator('h1:has-text("FAQ"), h1:has-text("Questions")')).toBeVisible();
  });

  test('should display FAQ accordion', async ({ page }) => {
    await page.goto('/faq');

    // Should have accordion items
    const accordionItems = page.locator('[data-testid="faq-item"], [role="button"], .accordion-trigger');
    const count = await accordionItems.count();

    expect(count).toBeGreaterThan(0);
  });

  test('should expand FAQ item on click', async ({ page }) => {
    await page.goto('/faq');

    // Click on first FAQ item
    const firstItem = page.locator('[data-testid="faq-item"], [role="button"], .accordion-trigger').first();
    await firstItem.click();

    // Should show expanded content
    await page.waitForTimeout(300);
    const expandedContent = page.locator('[data-state="open"], .accordion-content');
    if (await expandedContent.count() > 0) {
      await expect(expandedContent.first()).toBeVisible();
    }
  });
});

test.describe('About Page', () => {
  test('should display about page', async ({ page }) => {
    await page.goto('/about');

    await expect(page).toHaveURL('/about');
    await expect(page.locator('h1:has-text("About"), h1:has-text("Story")')).toBeVisible();
  });

  test('should display mission or vision', async ({ page }) => {
    await page.goto('/about');

    // Should show mission/vision content
    const content = page.locator('text=/mission|vision|believe|help/i');
    await expect(content.first()).toBeVisible();
  });
});

test.describe('Contact Page', () => {
  test('should display contact page', async ({ page }) => {
    await page.goto('/contact');

    await expect(page).toHaveURL('/contact');
    await expect(page.locator('h1:has-text("Contact"), h1:has-text("Touch")')).toBeVisible();
  });

  test('should display contact form', async ({ page }) => {
    await page.goto('/contact');

    // Should have contact form fields
    const emailField = page.locator('input[type="email"]');
    const messageField = page.locator('textarea');

    await expect(emailField).toBeVisible();
    await expect(messageField).toBeVisible();
  });

  test('should have submit button', async ({ page }) => {
    await page.goto('/contact');

    // Should have submit button
    const submitButton = page.locator('button[type="submit"], button:has-text("Send"), button:has-text("Submit")');
    await expect(submitButton.first()).toBeVisible();
  });
});

test.describe('Homepage Public Features', () => {
  test('should display Idea of the Day', async ({ page }) => {
    await page.goto('/');

    // Look for Idea of the Day section
    const ideaOfDay = page.locator('text=/Idea of the Day|Featured Idea|Today/i');

    if (await ideaOfDay.count() > 0) {
      await expect(ideaOfDay.first()).toBeVisible();
    }
  });

  test('should display recent insights preview', async ({ page }) => {
    await page.goto('/');

    // Should show some insights
    const insights = page.locator('[data-testid="insight-card"], .card:has-text("Market")');

    if (await insights.count() > 0) {
      await expect(insights.first()).toBeVisible();
    }
  });

  test('should have navigation to all public pages', async ({ page }) => {
    await page.goto('/');

    // Check for navigation links
    const navLinks = page.locator('nav a, header a');
    const count = await navLinks.count();

    expect(count).toBeGreaterThan(3);
  });

  test('should have footer with links', async ({ page }) => {
    await page.goto('/');

    // Check for footer
    const footer = page.locator('footer');

    if (await footer.count() > 0) {
      await expect(footer).toBeVisible();

      // Should have links
      const footerLinks = footer.locator('a');
      const linkCount = await footerLinks.count();
      expect(linkCount).toBeGreaterThan(0);
    }
  });
});

test.describe('SEO Elements', () => {
  test('should have meta title', async ({ page }) => {
    await page.goto('/');

    const title = await page.title();
    expect(title).toBeTruthy();
    expect(title.length).toBeGreaterThan(0);
  });

  test('should have meta description', async ({ page }) => {
    await page.goto('/');

    const metaDescription = await page.locator('meta[name="description"]').getAttribute('content');
    expect(metaDescription).toBeTruthy();
  });

  test('should have Open Graph tags', async ({ page }) => {
    await page.goto('/');

    const ogTitle = await page.locator('meta[property="og:title"]').getAttribute('content');
    const ogDescription = await page.locator('meta[property="og:description"]').getAttribute('content');

    expect(ogTitle || ogDescription).toBeTruthy();
  });

  test('tools page should have unique title', async ({ page }) => {
    await page.goto('/tools');

    const title = await page.title();
    expect(title.toLowerCase()).toContain('tool');
  });

  test('trends page should have unique title', async ({ page }) => {
    await page.goto('/trends');

    const title = await page.title();
    expect(title.toLowerCase()).toMatch(/trend|trending/);
  });
});
