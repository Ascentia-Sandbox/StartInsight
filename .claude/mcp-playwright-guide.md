# Playwright MCP Server - Configuration Guide

## Overview

The Playwright MCP (Model Context Protocol) server enables Claude Code to perform browser automation tasks directly. This is configured and ready to use in the StartInsight project.

## Configuration Status

✅ **Installed**: `@playwright/mcp@0.0.56` (globally via npm)
✅ **Configured**: Active in project MCP servers
✅ **Connected**: Server health check passed

## MCP Server Details

**Server Name**: `playwright`
**Command**: `npx -y @playwright/mcp`
**Type**: stdio (Standard Input/Output)
**Status**: ✓ Connected

## Configuration Location

The Playwright MCP server is configured in:
- **Global Config**: `/home/wysetime-pcc/.claude.json`
- **Project**: `/home/wysetime-pcc/Nero/StartInsight`

```json
{
  "playwright": {
    "type": "stdio",
    "command": "npx",
    "args": ["-y", "@playwright/mcp"],
    "env": {}
  }
}
```

## Available Capabilities

The Playwright MCP server provides Claude Code with the following browser automation tools:

### 1. Browser Control
- **Launch browsers**: Chromium, Firefox, WebKit
- **Navigate to URLs**: Open web pages
- **Browser contexts**: Isolated browser sessions
- **Page management**: Multiple tabs/pages

### 2. Page Interaction
- **Click elements**: Buttons, links, interactive elements
- **Type text**: Form inputs, text areas
- **Select options**: Dropdowns, checkboxes, radio buttons
- **Hover/Focus**: Mouse and keyboard interactions

### 3. Content Extraction
- **Take screenshots**: Full page or element screenshots
- **Get page content**: HTML, text, or structured data
- **Extract elements**: Find elements by selector, text, or attributes
- **Evaluate JavaScript**: Run custom scripts in browser context

### 4. Navigation & Waiting
- **Page navigation**: Back, forward, reload
- **Wait for elements**: Network idle, DOM ready, custom conditions
- **Handle popups**: Dialogs, alerts, new windows

## Usage Examples with Claude Code

### Example 1: Test a Website

**User prompt:**
```
Using the Playwright MCP server, navigate to http://localhost:3000
and take a screenshot of the homepage
```

**What Claude Code will do:**
1. Launch a browser using Playwright MCP
2. Navigate to the URL
3. Wait for page load
4. Capture screenshot
5. Save screenshot file

### Example 2: Automated Testing

**User prompt:**
```
Use Playwright MCP to test the login flow:
1. Go to http://localhost:3000
2. Click "All Insights" link
3. Verify the page has a filter sidebar
4. Take a screenshot
```

**What Claude Code will do:**
1. Launch browser with Playwright MCP
2. Navigate to homepage
3. Click the link
4. Check for filter sidebar element
5. Capture verification screenshot

### Example 3: Scrape Data

**User prompt:**
```
Use Playwright MCP to scrape the top 3 insights from
http://localhost:3000 and extract their problem statements
```

**What Claude Code will do:**
1. Open browser via MCP
2. Navigate to page
3. Find insight card elements
4. Extract text from problem statement elements
5. Return structured data

### Example 4: Interactive Debugging

**User prompt:**
```
Use Playwright MCP to debug the filter functionality:
1. Navigate to /insights page
2. Click the "Reddit" source filter
3. Verify URL changes to include ?source=reddit
4. Check if results are filtered
```

**What Claude Code will do:**
1. Launch browser with Playwright MCP
2. Execute each step
3. Verify URL parameters
4. Check DOM for filtered results
5. Report findings

## Integration with StartInsight Tests

The Playwright MCP server complements the existing test infrastructure:

### Existing Playwright Tests
Location: `tests/frontend/e2e/`
- `daily-top.spec.ts` (10 scenarios)
- `filters.spec.ts` (10 scenarios)
- `insight-detail.spec.ts` (12 scenarios)
- `theme-responsive.spec.ts` (15 scenarios)

**Run existing tests:**
```bash
cd frontend
npm run test        # Run all E2E tests
npm run test:ui     # Interactive mode
```

### MCP-Assisted Testing Workflows

**Use Case 1: Ad-hoc Testing**
- Ask Claude Code to test specific user flows without writing test code
- Quick verification during development
- Screenshot-based visual regression checks

**Use Case 2: Test Development**
- Ask Claude Code to help write new Playwright test scenarios
- Generate test code using MCP to explore the application
- Prototype test interactions before formalizing them

**Use Case 3: Debug Failing Tests**
- Use MCP to reproduce failing test scenarios interactively
- Investigate element selectors and page state
- Validate fixes before re-running full test suite

**Use Case 4: Cross-Browser Testing**
- Test on different browsers (Chromium, Firefox, WebKit)
- Verify responsive design at various viewport sizes
- Check browser-specific issues

## Common Commands

### Check MCP Server Status
```bash
claude mcp list
```

### Restart MCP Server (if needed)
```bash
claude mcp restart playwright
```

### Remove MCP Server (if needed)
```bash
claude mcp remove playwright
```

### Re-add MCP Server
```bash
claude mcp add playwright -- npx -y @playwright/mcp
```

## Best Practices

### 1. Use for Ad-hoc Testing
- Quick verification of UI changes
- Manual testing automation
- Screenshot comparisons

### 2. Complement Formal Tests
- Use MCP for exploration and prototyping
- Write formal Playwright tests for CI/CD
- Keep MCP tests as temporary/debugging tools

### 3. Browser Lifecycle
- MCP will automatically manage browser lifecycle
- Each session launches fresh browser instances
- No need to manually close browsers

### 4. Selector Strategies
- Prefer `data-testid` attributes for reliability
- Use text content for user-facing elements
- Avoid brittle CSS selectors

### 5. Wait Strategies
- Let Playwright auto-wait for elements
- Avoid hardcoded timeouts
- Use network idle for dynamic content

## Limitations

1. **Session Scope**: Each MCP request is isolated (no persistent browser sessions between prompts)
2. **Performance**: Slower than direct Playwright tests (involves LLM reasoning)
3. **Complexity**: Best for simple tasks; complex flows better suited for formal tests
4. **Visibility**: MCP runs headless by default (no browser UI visible)

## Troubleshooting

### MCP Server Not Connected

**Problem**: `playwright: npx -y @playwright/mcp - ✗ Failed to connect`

**Solutions**:
```bash
# 1. Reinstall globally
npm install -g @playwright/mcp

# 2. Restart MCP server
claude mcp restart playwright

# 3. Check npm global path
npm list -g @playwright/mcp

# 4. Clear npm cache
npm cache clean --force
```

### Browser Launch Fails

**Problem**: Playwright can't launch browser

**Solutions**:
```bash
# Install browser binaries
npx playwright install

# Install with dependencies (Linux)
npx playwright install --with-deps

# Check Playwright installation
npx playwright --version
```

### Permission Issues

**Problem**: MCP can't access files or network

**Solutions**:
- Check Claude Code permissions in `.claude/settings.local.json`
- Ensure backend is running (http://localhost:8000)
- Verify file system access permissions

## Example Workflows

### Workflow 1: Visual Regression Testing

**Scenario**: Verify UI changes didn't break existing pages

**Steps**:
1. Ask Claude Code to screenshot current homepage
2. Make UI changes
3. Ask Claude Code to screenshot again
4. Compare screenshots manually or ask Claude to describe differences

**Example prompt**:
```
Use Playwright MCP to take a full-page screenshot of http://localhost:3000
and save it as homepage-before.png
```

### Workflow 2: Form Testing

**Scenario**: Test insight filtering workflow

**Example prompt**:
```
Use Playwright MCP to:
1. Navigate to http://localhost:3000/insights
2. Click the "Source" dropdown
3. Select "Reddit"
4. Verify the URL contains ?source=reddit
5. Count how many insight cards are displayed
```

### Workflow 3: Accessibility Audit

**Scenario**: Check for accessibility issues

**Example prompt**:
```
Use Playwright MCP to audit accessibility on http://localhost:3000:
1. Navigate to homepage
2. Check if all buttons have aria-labels
3. Verify heading hierarchy (h1, h2, h3)
4. List any images without alt text
```

## Related Documentation

- **Playwright MCP Source**: https://github.com/microsoft/playwright-mcp
- **Playwright Docs**: https://playwright.dev
- **MCP Protocol**: https://modelcontextprotocol.io
- **StartInsight Tests**: `tests/frontend/e2e/`
- **Frontend Setup**: `frontend/README.md`

## Advanced Configuration (Optional)

### Custom Browser Options

If you need to configure browser options, you can modify the MCP server configuration:

```json
{
  "playwright": {
    "type": "stdio",
    "command": "npx",
    "args": [
      "-y",
      "@playwright/mcp"
    ],
    "env": {
      "PLAYWRIGHT_BROWSER": "chromium",
      "PLAYWRIGHT_HEADLESS": "false"
    }
  }
}
```

**Note**: Modifying configuration requires editing `/home/wysetime-pcc/.claude.json` manually.

### Browser Launch Arguments

For advanced scenarios (e.g., testing with specific browser flags):

```typescript
// This is handled automatically by MCP
// but understanding the underlying Playwright API helps:
const browser = await playwright.chromium.launch({
  headless: true,
  args: ['--disable-gpu', '--no-sandbox']
});
```

## Summary

✅ Playwright MCP server is configured and ready to use
✅ Enables Claude Code to automate browser tasks
✅ Complements existing Playwright E2E test suite
✅ Use for ad-hoc testing, debugging, and exploration
✅ Keep formal tests in `tests/frontend/e2e/` for CI/CD

**Quick Start**: Simply ask Claude Code to use Playwright MCP for browser automation tasks!

---

**Last Updated**: 2026-01-18
**MCP Server Version**: @playwright/mcp@0.0.56
**Status**: ✅ Active and Connected
