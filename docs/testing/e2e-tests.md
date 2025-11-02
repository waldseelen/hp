# End-to-End Testing Guide

**Document Version:** 1.0
**Last Updated:** January 2025
**Testing Framework:** Playwright

---

## Table of Contents

1. [Overview](#overview)
2. [Setup](#setup)
3. [Test Structure](#test-structure)
4. [Running Tests](#running-tests)
5. [Writing Tests](#writing-tests)
6. [Debugging](#debugging)
7. [Best Practices](#best-practices)
8. [CI/CD Integration](#cicd-integration)
9. [Troubleshooting](#troubleshooting)

---

## Overview

End-to-End (E2E) tests verify complete user journeys through the application, testing the system from the user's perspective.

### What We Test

- ✅ **Authentication flows** (registration, login, logout)
- ✅ **Blog functionality** (list, detail, search, filtering)
- ✅ **Contact form** (submission, validation)
- ✅ **Admin dashboard** (navigation, CRUD operations)
- ✅ **Accessibility** (WCAG 2.1 AA compliance)

### Test Coverage

| Test File | Tests | Purpose |
|-----------|-------|---------|
| `test_auth.spec.js` | 40+ | Authentication & session management |
| `test_blog.spec.js` | 50+ | Blog browsing & interactions |
| `test_contact.spec.js` | 40+ | Contact form functionality |
| `test_admin.spec.js` | 40+ | Admin dashboard operations |
| `test_accessibility.spec.js` | 80+ | Accessibility compliance |

**Total:** 250+ E2E tests

---

## Setup

### Prerequisites

```bash
# Install Node.js dependencies
npm install

# Install Playwright browsers
npx playwright install
```

### Configuration

E2E tests are configured in `playwright.config.js`:

```javascript
{
  testDir: './tests/e2e',
  timeout: 60000,              // 60 seconds per test
  retries: 2,                  // Retry failed tests on CI
  workers: 1,                  // Run tests in parallel
  baseURL: 'http://127.0.0.1:8001',
}
```

### Environment Setup

Tests automatically start Django development server on port 8001:

```javascript
webServer: {
  command: 'python manage.py runserver 127.0.0.1:8001',
  url: 'http://127.0.0.1:8001',
  reuseExistingServer: !process.env.CI,
  timeout: 120000,
}
```

---

## Test Structure

### Directory Structure

```
tests/e2e/
├── test_auth.spec.js          # Authentication tests
├── test_blog.spec.js          # Blog functionality tests
├── test_contact.spec.js       # Contact form tests
├── test_admin.spec.js         # Admin dashboard tests
├── test_accessibility.spec.js # Accessibility tests
├── global-setup.js            # Pre-test setup
└── global-teardown.js         # Post-test cleanup
```

### Test File Structure

```javascript
const { test, expect } = require('@playwright/test');

test.describe('Feature Name', () => {
    test.beforeEach(async ({ page }) => {
        // Setup before each test
        await page.goto('/');
    });

    test('should do something', async ({ page }) => {
        // Test implementation
        await page.click('button');
        await expect(page.locator('h1')).toBeVisible();
    });
});
```

---

## Running Tests

### All Tests

```bash
# Run all E2E tests
npm run test:e2e

# With UI mode (headed)
npm run test:e2e:headed

# Playwright command
npx playwright test
```

### Specific Tests

```bash
# Run specific test file
npx playwright test tests/e2e/test_auth.spec.js

# Run specific test by name
npx playwright test -g "should login successfully"

# Run tests matching pattern
npx playwright test tests/e2e/test_auth
```

### Browser-Specific Tests

```bash
# Run in Chromium only
npx playwright test --project=chromium

# Run in Firefox only
npx playwright test --project=firefox

# Run in WebKit (Safari) only
npx playwright test --project=webkit

# Run in mobile browsers
npx playwright test --project="Mobile Chrome"
npx playwright test --project="Mobile Safari"
```

### Test Reports

```bash
# Generate HTML report
npx playwright test --reporter=html

# Open report
npx playwright show-report

# JSON report
npx playwright test --reporter=json --reporter-options=outputFile=results.json

# Multiple reporters
npx playwright test --reporter=html --reporter=list
```

---

## Writing Tests

### Basic Test Example

```javascript
const { test, expect } = require('@playwright/test');

test('homepage loads successfully', async ({ page }) => {
    // Navigate to page
    await page.goto('/');

    // Check page title
    await expect(page).toHaveTitle(/Portfolio/);

    // Check element is visible
    const heading = page.locator('h1');
    await expect(heading).toBeVisible();
});
```

### Form Interaction

```javascript
test('user can submit contact form', async ({ page }) => {
    await page.goto('/contact/');

    // Fill form fields
    await page.fill('input[name="name"]', 'John Doe');
    await page.fill('input[name="email"]', 'john@example.com');
    await page.fill('textarea[name="message"]', 'Test message');

    // Submit form
    await page.click('button[type="submit"]');

    // Verify success message
    const successMessage = page.locator('text=/success|thank you/i');
    await expect(successMessage).toBeVisible({ timeout: 5000 });
});
```

### Navigation & Clicks

```javascript
test('user can browse blog posts', async ({ page }) => {
    await page.goto('/blog/');

    // Click first blog post
    const firstPost = page.locator('article').first();
    await firstPost.locator('a').click();

    // Wait for navigation
    await page.waitForURL(/\/blog\/.+/);

    // Verify detail page loaded
    const content = page.locator('article');
    await expect(content).toBeVisible();
});
```

### Authentication

```javascript
test.describe('Protected pages', () => {
    test.beforeEach(async ({ page }) => {
        // Login before each test
        await page.goto('/admin/login/');
        await page.fill('input[name="username"]', 'admin');
        await page.fill('input[name="password"]', 'password');
        await page.click('input[type="submit"]');
        await page.waitForURL('/admin/');
    });

    test('admin dashboard is accessible', async ({ page }) => {
        await page.goto('/admin/');
        await expect(page.locator('#header')).toBeVisible();
    });
});
```

### Accessibility Testing

```javascript
const AxeBuilder = require('@axe-core/playwright').default;

test('homepage has no accessibility violations', async ({ page }) => {
    await page.goto('/');

    const accessibilityScanResults = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa'])
        .analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
});
```

### Mobile Testing

```javascript
test.describe('Mobile experience', () => {
    test.use({ viewport: { width: 375, height: 667 } });

    test('mobile menu works', async ({ page }) => {
        await page.goto('/');

        // Click mobile menu toggle
        const menuButton = page.locator('button[aria-label*="menu"]');
        await menuButton.click();

        // Verify menu is visible
        const menu = page.locator('nav');
        await expect(menu).toBeVisible();
    });
});
```

---

## Debugging

### Debug Mode

```bash
# Run in debug mode (opens inspector)
npx playwright test --debug

# Debug specific test
npx playwright test test_auth.spec.js --debug

# Headed mode (see browser)
npx playwright test --headed

# Slow motion (500ms between actions)
npx playwright test --headed --slow-mo=500
```

### Screenshots & Videos

```bash
# Take screenshot on failure (default)
npx playwright test --screenshot=only-on-failure

# Take screenshot always
npx playwright test --screenshot=on

# Record video on failure
npx playwright test --video=retain-on-failure

# Record video always
npx playwright test --video=on
```

### Traces

```bash
# Record trace on first retry
npx playwright test --trace=on-first-retry

# Record trace always
npx playwright test --trace=on

# View trace
npx playwright show-trace trace.zip
```

### Console Logs

```javascript
test('debug with console', async ({ page }) => {
    // Listen to console messages
    page.on('console', msg => console.log('PAGE LOG:', msg.text()));

    await page.goto('/');
});
```

### Pause Execution

```javascript
test('pause for inspection', async ({ page }) => {
    await page.goto('/');

    // Pause here - opens Playwright Inspector
    await page.pause();

    await page.click('button');
});
```

---

## Best Practices

### 1. Use Data Attributes for Selectors

**Good:**
```javascript
await page.click('[data-testid="submit-button"]');
```

**Bad:**
```javascript
await page.click('button.btn-primary.mt-4'); // Fragile
```

### 2. Use Explicit Waits

```javascript
// Wait for element
await page.waitForSelector('h1', { state: 'visible' });

// Wait for network
await page.waitForLoadState('networkidle');

// Wait for URL
await page.waitForURL('/success');
```

### 3. Use Page Object Model

```javascript
class LoginPage {
    constructor(page) {
        this.page = page;
        this.usernameInput = page.locator('input[name="username"]');
        this.passwordInput = page.locator('input[name="password"]');
        this.submitButton = page.locator('button[type="submit"]');
    }

    async login(username, password) {
        await this.usernameInput.fill(username);
        await this.passwordInput.fill(password);
        await this.submitButton.click();
    }
}

test('login with POM', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await page.goto('/login/');
    await loginPage.login('user', 'password');
});
```

### 4. Avoid Hard-Coded Waits

**Good:**
```javascript
await page.waitForSelector('.message', { state: 'visible' });
```

**Bad:**
```javascript
await page.waitForTimeout(3000); // Flaky
```

### 5. Clean Test Data

```javascript
test.afterEach(async ({ page }) => {
    // Clean up test data
    await page.evaluate(() => localStorage.clear());
});
```

---

## CI/CD Integration

### GitHub Actions

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install dependencies
        run: npm ci

      - name: Install Playwright browsers
        run: npx playwright install --with-deps

      - name: Run E2E tests
        run: npx playwright test

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: test-results/
```

### Environment Variables

```bash
# Set base URL
export BASE_URL=https://staging.example.com

# Run tests
npx playwright test
```

---

## Troubleshooting

### Common Issues

#### "webServer process exited"

**Cause:** Django server failed to start

**Solution:**
```bash
# Check Django runs manually
python manage.py runserver 8001

# Check dependencies
pip install -r requirements.txt

# Check database
python manage.py migrate
```

#### "Timeout waiting for selector"

**Cause:** Element not found or slow to load

**Solution:**
```javascript
// Increase timeout
await page.waitForSelector('h1', { timeout: 10000 });

// Use better selector
await page.waitForSelector('[data-testid="heading"]');

// Check element exists
const exists = await page.locator('h1').count() > 0;
```

#### "Navigation timeout"

**Cause:** Page takes too long to load

**Solution:**
```javascript
// Increase navigation timeout
await page.goto('/', { timeout: 60000 });

// Wait for specific state
await page.goto('/', { waitUntil: 'domcontentloaded' });
```

#### Flaky Tests

**Cause:** Race conditions, timing issues

**Solution:**
- Use explicit waits instead of `waitForTimeout`
- Wait for specific conditions
- Increase retries in config
- Use `page.waitForLoadState('networkidle')`

### Debug Commands

```bash
# Verbose output
npx playwright test --reporter=list --reporter-options="printSteps=true"

# Show browser
npx playwright test --headed --slow-mo=500

# Single worker (no parallel)
npx playwright test --workers=1

# Update snapshots
npx playwright test --update-snapshots
```

---

## Performance Tips

### 1. Run Tests in Parallel

```javascript
// playwright.config.js
module.exports = {
  fullyParallel: true,
  workers: process.env.CI ? 1 : 4,
};
```

### 2. Reuse Browser Context

```javascript
test.describe.serial('Related tests', () => {
    // These run in sequence and share context
    test('test 1', async ({ page }) => {});
    test('test 2', async ({ page }) => {});
});
```

### 3. Skip Slow Tests Locally

```javascript
test.skip(process.env.CI !== 'true', 'slow test', async ({ page }) => {
    // Only runs in CI
});
```

---

## Resources

- [Playwright Documentation](https://playwright.dev)
- [Best Practices](https://playwright.dev/docs/best-practices)
- [API Reference](https://playwright.dev/docs/api/class-playwright)
- [Debugging Guide](https://playwright.dev/docs/debug)

---

**Document Changelog:**

| Date | Version | Changes |
|------|---------|---------|
| Jan 2025 | 1.0 | Initial version - 250+ E2E tests implemented |
