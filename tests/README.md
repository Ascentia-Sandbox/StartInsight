# StartInsight - Testing Infrastructure

This directory contains all test code for the StartInsight project, organized by backend and frontend.

## Directory Structure

```
tests/
├── backend/                    # Backend tests (Python/Pytest)
│   ├── conftest.py            # Pytest configuration & fixtures
│   ├── unit/                  # Unit tests (isolated components)
│   │   └── test_scrapers.py   # Scraper unit tests (mocked)
│   ├── integration/           # Integration tests (multiple components)
│   │   ├── test_api.py        # API endpoint integration tests
│   │   └── test_phase_2_5_integration.py  # Phase 2.5 full pipeline test
│   └── validation/            # Phase validation tests
│       ├── test_phase_1_4.py  # Phase 1.4: Task Queue & Scheduler
│       ├── test_phase_1_5.py  # Phase 1.5: FastAPI Endpoints
│       ├── test_phase_1_6.py  # Phase 1.6: Environment & Config
│       ├── test_phase_1_8.py  # Phase 1.8: Documentation
│       ├── test_phase_2_1.py  # Phase 2.1: Database Schema Extension
│       ├── test_phase_2_2.py  # Phase 2.2: AI Analyzer Agent
│       ├── test_phase_2_3.py  # Phase 2.3: Analysis Task Queue
│       ├── test_phase_2_4.py  # Phase 2.4: Insights API Endpoints
│       └── test_phase_2_6.py  # Phase 2.6: Monitoring & Logging
│
└── frontend/                   # Frontend tests (TypeScript/Playwright)
    ├── playwright.config.ts   # Playwright configuration
    └── e2e/                   # End-to-end tests
        ├── daily-top.spec.ts          # Homepage tests (10 scenarios)
        ├── filters.spec.ts            # Filtering tests (10 scenarios)
        ├── insight-detail.spec.ts     # Detail page tests (12 scenarios)
        └── theme-responsive.spec.ts   # Dark mode, responsive, a11y (15 scenarios)
```

## Test Categories

### Backend Tests (Python/Pytest)

**Unit Tests** (`tests/backend/unit/`)
- Isolated component testing
- Mocked external dependencies (Firecrawl, PRAW, LLM APIs)
- Fast execution
- **Example**: `test_scrapers.py` - Tests scraper logic with mocked HTTP responses

**Integration Tests** (`tests/backend/integration/`)
- Multi-component testing
- Database interactions (with test database)
- API endpoint testing
- **Example**: `test_api.py` - Tests FastAPI endpoints with real database

**Validation Tests** (`tests/backend/validation/`)
- Phase-specific validation tests
- Verify phase completion criteria
- Test phase deliverables
- **Example**: `test_phase_2_1.py` - Validates Insight model, migrations, relationships

### Frontend Tests (TypeScript/Playwright)

**E2E Tests** (`tests/frontend/e2e/`)
- Full user journey testing
- Cross-browser testing (Chrome, Firefox, Safari, Mobile)
- Accessibility testing
- Responsive design testing
- **Total**: 47 test scenarios across 4 test suites

## Running Tests

### Backend Tests (Pytest)

```bash
# From project root
cd backend

# Run all tests
uv run pytest ../tests/backend/ -v

# Run specific category
uv run pytest ../tests/backend/unit/ -v
uv run pytest ../tests/backend/integration/ -v
uv run pytest ../tests/backend/validation/ -v

# Run specific phase validation
uv run pytest ../tests/backend/validation/test_phase_2_1.py -v

# Run with coverage
uv run pytest ../tests/backend/ -v --cov=app --cov-report=html

# Run in parallel (faster)
uv run pytest ../tests/backend/ -v -n auto
```

### Frontend Tests (Playwright)

```bash
# From project root
cd frontend

# Run all E2E tests
npx playwright test -c ../tests/frontend/playwright.config.ts

# Run in UI mode (interactive)
npx playwright test -c ../tests/frontend/playwright.config.ts --ui

# Run specific test file
npx playwright test -c ../tests/frontend/playwright.config.ts ../tests/frontend/e2e/daily-top.spec.ts

# Run on specific browser
npx playwright test -c ../tests/frontend/playwright.config.ts --project=chromium

# Debug mode
npx playwright test -c ../tests/frontend/playwright.config.ts --debug

# View test report
npx playwright show-report
```

## Test Coverage

### Backend Test Statistics
- **Unit Tests**: 3 test files
- **Integration Tests**: 2 test files
- **Validation Tests**: 9 test files (Phase 1.4-1.8, Phase 2.1-2.6)
- **Total Backend Tests**: ~50+ test functions

### Frontend Test Statistics
- **E2E Test Suites**: 4 test files
- **Total Test Scenarios**: 47 comprehensive scenarios
- **Browser Coverage**: 5 platforms (Chrome, Firefox, Safari, Mobile Chrome, Mobile Safari)
- **Test Categories**:
  - Homepage/Daily Top: 10 tests
  - Filtering & Search: 10 tests
  - Insight Detail: 12 tests
  - Dark Mode, Responsive, Accessibility: 15 tests

## Test Configuration

### Backend (Pytest)
- **Configuration**: `tests/backend/conftest.py`
- **Fixtures**: db_session, http_client, sample_signal
- **Database**: Uses test database (isolated from development)
- **Async Support**: pytest-asyncio for async test functions

### Frontend (Playwright)
- **Configuration**: `tests/frontend/playwright.config.ts`
- **Base URL**: http://localhost:3000
- **Browsers**: Chromium, Firefox, WebKit, Mobile Chrome, Mobile Safari
- **Parallel Execution**: Enabled for faster test runs
- **Trace**: Captured on first retry for debugging
- **Auto-Start Dev Server**: Automatically starts Next.js dev server

## CI/CD Integration

Tests are automatically run in GitHub Actions pipeline (`.github/workflows/ci-cd.yml`):

**Backend Tests Job:**
- PostgreSQL 16 and Redis 7 services
- Python 3.12 setup
- uv installation
- Run pytest with coverage
- Upload coverage reports

**Frontend Tests Job:**
- Node.js 20 setup
- npm ci install
- ESLint linting
- TypeScript check
- Build test
- (Playwright tests can be added to CI)

## Writing New Tests

### Backend Test Template (Pytest)

```python
# tests/backend/unit/test_example.py
import pytest
from app.services.example import ExampleService

@pytest.mark.asyncio
async def test_example_function(db_session):
    """Test description here."""
    # Arrange
    service = ExampleService(db_session)

    # Act
    result = await service.do_something()

    # Assert
    assert result is not None
    assert result.status == "success"
```

### Frontend Test Template (Playwright)

```typescript
// tests/frontend/e2e/example.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Feature Name', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should do something', async ({ page }) => {
    // Arrange - setup page state

    // Act - perform user actions
    await page.click('button[data-testid="example"]');

    // Assert - verify expectations
    await expect(page.locator('h1')).toHaveText('Expected Text');
  });
});
```

## Best Practices

### Backend Tests
1. **Isolation**: Each test should be independent
2. **Fixtures**: Use conftest.py fixtures for common setup
3. **Async**: Always use @pytest.mark.asyncio for async functions
4. **Mocking**: Mock external APIs (Firecrawl, Anthropic, OpenAI)
5. **Database**: Use db_session fixture with rollback
6. **Coverage**: Aim for >80% code coverage

### Frontend Tests
1. **User-Centric**: Test from user's perspective
2. **Selectors**: Prefer data-testid over fragile CSS selectors
3. **Waiting**: Use auto-waiting features, avoid hardcoded delays
4. **Assertions**: Use Playwright's built-in expect assertions
5. **Accessibility**: Include accessibility checks (ARIA labels, semantic HTML)
6. **Cross-Browser**: Test on multiple browsers

## Troubleshooting

### Backend Test Issues

**Database Connection Errors:**
```bash
# Ensure PostgreSQL is running
docker-compose up -d postgres

# Check connection
psql -h localhost -p 5433 -U startinsight_user -d startinsight_db
```

**Import Errors:**
```bash
# Ensure working directory is backend/
cd backend

# Run tests with proper Python path
PYTHONPATH=. uv run pytest ../tests/backend/ -v
```

### Frontend Test Issues

**Playwright Not Installed:**
```bash
# Install Playwright browsers
npx playwright install
```

**Dev Server Not Running:**
```bash
# Playwright config auto-starts dev server
# But ensure backend is running on http://localhost:8000

cd backend
uv run uvicorn app.main:app --reload
```

**Tests Failing in CI:**
- Check GitHub Actions logs
- Ensure environment variables are set
- Verify database migrations ran successfully

## Related Documentation

- **Test Results**: `test-results/` (test execution documentation)
- **Backend Setup**: `backend/README.md`
- **Frontend Setup**: `frontend/README.md`
- **CI/CD Pipeline**: `.github/workflows/ci-cd.yml`
- **Deployment**: `DEPLOYMENT.md`

---

**Last Updated**: 2026-01-18
**Total Tests**: 50+ backend tests + 47 frontend E2E tests
**Coverage**: Unit, Integration, E2E, Validation
**Status**: All tests passing ✅
