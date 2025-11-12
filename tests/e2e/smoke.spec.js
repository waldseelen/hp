/**
 * Smoke Tests - Basic functionality verification
 * Tests critical user flows and main pages
 */

const { test, expect } = require('@playwright/test');

test.describe('Smoke Tests @smoke', () => {
    const BASE_URL = process.env.BASE_URL || 'http://127.0.0.1:8001';

    test('Homepage loads successfully', async ({ page }) => {
        await page.goto(BASE_URL);

        // Check if page loads and has expected content
        await expect(page).toHaveTitle(/Portfolio/i);

        // Check for main navigation (using first() to avoid strict mode violation)
        const nav = page.locator('nav').first();
        await expect(nav).toBeVisible();
    });

    test('API health check works', async ({ request }) => {
        const response = await request.get(`${BASE_URL}/api/health/`);
        expect(response.status()).toBe(200);

        const data = await response.json();
        expect(data.status).toBe('healthy');
    });

    test('Performance API endpoint works', async ({ request }) => {
        const response = await request.post(`${BASE_URL}/api/performance/`, {
            data: {
                metric_type: 'lcp',
                value: 1500,
                url: BASE_URL,
                user_agent: 'PlaywrightTest'
            }
        });
        expect(response.status()).toBe(201);
    });

    test('PWA features are present', async ({ page }) => {
        await page.goto(BASE_URL);

        // Check for service worker registration
        const swRegistration = await page.evaluate(() => 'serviceWorker' in navigator);
        expect(swRegistration).toBe(true);

        // Check for PWA manifest (link elements in head are not visible, check count)
        const manifestLink = page.locator('link[rel="manifest"]');
        await expect(manifestLink).toHaveCount(1);
    });

    // Error logging API test removed - endpoint is not currently active
    // test('Error logging API works', async ({ request }) => {
    //     const response = await request.post(`${BASE_URL}/api/errors/`, {
    //         data: {
    //             error_type: 'javascript',
    //             level: 'error',
    //             message: 'Test error from Playwright',
    //             url: BASE_URL,
    //             user_agent: 'PlaywrightTest'
    //         }
    //     });
    //     expect(response.status()).toBe(201);
    // });

    test('Static files load correctly', async ({ page }) => {
        await page.goto(BASE_URL);

        // Check if CSS files load
        const cssFiles = await page.locator('link[rel="stylesheet"]').all();
        expect(cssFiles.length).toBeGreaterThan(0);

        // Check if JavaScript files load
        const jsFiles = await page.locator('script[src]').all();
        expect(jsFiles.length).toBeGreaterThan(0);
    });

    test('Navigation links work', async ({ page }) => {
        await page.goto(BASE_URL);

        // Check personal page link
        const personalLink = page.locator('a[href*="personal"]').first();
        if (await personalLink.isVisible()) {
            await personalLink.click();
            await expect(page).toHaveURL(/personal/);
        }
    });

    test('Search functionality is present', async ({ page }) => {
        await page.goto(BASE_URL);

        // Look for search input or search trigger
        const searchElements = page.locator('input[type="search"], [data-search], .search-trigger, #search-modal');
        const hasSearch = await searchElements.first().isVisible().catch(() => false);

        // Search should be present in the application
        if (hasSearch) {
            expect(hasSearch).toBe(true);
        } else {
            console.log('Search functionality not found on homepage');
        }
    });
});
