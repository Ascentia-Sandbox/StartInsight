// Quick script to view first 5 insights using Playwright
const { chromium } = require('playwright');

(async () => {
  console.log('🚀 Launching browser...');
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();

  console.log('📱 Navigating to http://localhost:3000...');
  await page.goto('http://localhost:3000', { waitUntil: 'networkidle' });

  // Wait for insights to load
  console.log('⏳ Waiting for insights to load...');
  await page.waitForSelector('[data-testid="insight-card"], .grid > div', { timeout: 10000 }).catch(() => {
    console.log('⚠️  No insight cards found yet, checking for content...');
  });

  // Give it a moment to render
  await page.waitForTimeout(2000);

  // Extract insight information
  console.log('📊 Extracting first 5 insights...\n');

  const insights = await page.evaluate(() => {
    const cards = document.querySelectorAll('.grid > div');
    const results = [];

    for (let i = 0; i < Math.min(5, cards.length); i++) {
      const card = cards[i];

      // Try to find problem statement
      const problemEl = card.querySelector('h3, [class*="font-semibold"]');
      const problem = problemEl?.textContent?.trim() || 'No problem statement found';

      // Try to find solution
      const paragraphs = card.querySelectorAll('p');
      let solution = 'No solution found';
      for (const p of paragraphs) {
        const text = p.textContent?.trim();
        if (text && text.length > 20 && !text.includes('View Details')) {
          solution = text;
          break;
        }
      }

      // Try to find relevance score (stars)
      const stars = card.querySelectorAll('[class*="star"]');
      const score = stars.length > 0 ? `${stars.length}/5` : 'No score';

      // Try to find market size badge
      const badges = card.querySelectorAll('[class*="badge"], [class*="px-2"]');
      let marketSize = 'Unknown';
      for (const badge of badges) {
        const text = badge.textContent?.trim();
        if (text && (text.includes('Small') || text.includes('Medium') || text.includes('Large'))) {
          marketSize = text;
          break;
        }
      }

      results.push({
        index: i + 1,
        problem,
        solution: solution.substring(0, 100) + (solution.length > 100 ? '...' : ''),
        score,
        marketSize
      });
    }

    return results;
  });

  // Display insights
  if (insights.length === 0) {
    console.log('❌ No insights found on the page.');
    console.log('   This might mean:');
    console.log('   - The backend has no insights in the database');
    console.log('   - The page is still loading');
    console.log('   - There\'s an error fetching insights from the API');
  } else {
    console.log(`✅ Found ${insights.length} insights:\n`);

    insights.forEach(insight => {
      console.log(`${'='.repeat(80)}`);
      console.log(`📌 Insight #${insight.index}`);
      console.log(`${'='.repeat(80)}`);
      console.log(`🎯 Problem: ${insight.problem}`);
      console.log(`💡 Solution: ${insight.solution}`);
      console.log(`⭐ Relevance Score: ${insight.score}`);
      console.log(`📊 Market Size: ${insight.marketSize}`);
      console.log('');
    });
  }

  // Take a screenshot
  const screenshotPath = '/home/wysetime-pcc/Nero/StartInsight/homepage-insights.png';
  await page.screenshot({ path: screenshotPath, fullPage: true });
  console.log(`📸 Screenshot saved to: ${screenshotPath}\n`);

  console.log('🎉 Browser will stay open for 10 seconds so you can view the page...');
  await page.waitForTimeout(10000);

  await browser.close();
  console.log('✅ Browser closed. Done!');
})();
