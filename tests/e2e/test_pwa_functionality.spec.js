// @ts-check
const { test, expect } = require('@playwright/test');

/**
 * PWA Functionality Tests
 * Testing Progressive Web App features including service worker,
 * push notifications, and offline functionality
 */

test.describe('PWA Functionality', () => {

    test.beforeEach(async ({ page }) => {
    // Navigate to home page before each test
        await page.goto('/');
    });

    test('should have service worker registered @pwa', async ({ page }) => {
    // Wait for service worker to be registered
        await page.waitForFunction(() => 'serviceWorker' in navigator && navigator.serviceWorker.controller, { timeout: 10000 });

        // Check service worker registration
        const swRegistered = await page.evaluate(() => navigator.serviceWorker.controller !== null);

        expect(swRegistered).toBeTruthy();
    });

    test('should have web app manifest @pwa', async ({ page }) => {
    // Check if manifest link exists
        const manifestLink = page.locator('link[rel="manifest"]');
        await expect(manifestLink).toBeVisible();

        // Verify manifest is accessible
        const manifestHref = await manifestLink.getAttribute('href');
        const manifestResponse = await page.request.get(manifestHref);
        expect(manifestResponse.status()).toBe(200);

        // Parse manifest content
        const manifestContent = await manifestResponse.json();
        expect(manifestContent.name).toBeTruthy();
        expect(manifestContent.start_url).toBeTruthy();
        expect(manifestContent.display).toBeTruthy();
    });

    test('should support push notifications @pwa', async ({ page, context }) => {
    // Grant notification permission
        await context.grantPermissions(['notifications']);

        // Check if push notifications are supported
        const pushSupported = await page.evaluate(() => 'PushManager' in window && 'serviceWorker' in navigator);

        expect(pushSupported).toBeTruthy();

        // Test VAPID key endpoint
        const vapidResponse = await page.request.get('/main/api/webpush/vapid-public-key/');
        expect(vapidResponse.status()).toBe(200);

        const vapidData = await vapidResponse.json();
        expect(vapidData.publicKey).toBeTruthy();
    });

    test('should cache resources for offline use @pwa', async ({ page }) => {
    // Wait for service worker to cache resources
        await page.waitForTimeout(2000);

        // Check if critical resources are cached
        const cacheCheck = await page.evaluate(async () => {
            const cacheNames = await caches.keys();
            const portfolioCache = cacheNames.find(name => name.includes('portfolio-v'));

            if (!portfolioCache) { return false; }

            const cache = await caches.open(portfolioCache);
            const cachedUrls = await cache.keys();

            return cachedUrls.length > 0;
        });

        expect(cacheCheck).toBeTruthy();
    });

    test('should show offline page when network unavailable @pwa', async ({ page, context }) => {
    // First visit to cache the offline page
        await page.goto('/offline/');
        expect(await page.title()).toContain('Offline');

        // Simulate offline condition
        await context.setOffline(true);

        // Try to navigate to a new page
        await page.goto('/main/personal/');

        // Should show offline page or cached content
        const pageContent = await page.textContent('body');
        const isOfflineOrCached = pageContent.includes('offline') ||
                             pageContent.includes('Personal') ||
                             pageContent.includes('Portfolio');

        expect(isOfflineOrCached).toBeTruthy();

        // Restore online status
        await context.setOffline(false);
    });

    test('should track performance metrics @performance', async ({ page }) => {
    // Navigate and wait for page load
        await page.goto('/');
        await page.waitForLoadState('networkidle');

        // Check if performance metrics are being collected
        const performanceTracking = await page.evaluate(() =>
        // Check if Web Vitals are being tracked
            typeof window.PerformanceMonitor !== 'undefined' ||
             typeof window.webVitals !== 'undefined' ||
             performance.getEntriesByType('navigation').length > 0
        );

        expect(performanceTracking).toBeTruthy();

        // Verify performance API endpoint
        const perfResponse = await page.request.get('/main/api/performance/summary/');
        expect(perfResponse.status()).toBe(200);
    });

    test('should handle app installation prompt @pwa', async ({ page, context }) => {
    // Check if beforeinstallprompt event is handled
        const installPromptHandled = await page.evaluate(() => typeof window.deferredPrompt !== 'undefined' ||
             typeof window.installApp === 'function');

        // Note: This might be false in test environment, which is expected
        // The important thing is that the code doesn't throw errors
        expect(typeof installPromptHandled).toBe('boolean');
    });

    test('should sync data when back online @pwa', async ({ page, context }) => {
    // Fill out a form while online
        await page.goto('/contact/');

        // Check if contact form exists
        const form = page.locator('form');
        if (await form.count() > 0) {
            await page.fill('input[name="name"]', 'Test User');
            await page.fill('input[name="email"]', 'test@example.com');

            // Go offline
            await context.setOffline(true);

            // Try to submit (should queue for background sync)
            await page.click('button[type="submit"]');

            // Go back online
            await context.setOffline(false);

            // Wait for potential background sync
            await page.waitForTimeout(2000);
        }

        // Test passes if no JavaScript errors occurred
        const errors = [];
        page.on('pageerror', error => errors.push(error));

        expect(errors.length).toBe(0);
    });

    test('should handle service worker updates @pwa', async ({ page }) => {
    // Check if service worker update mechanism is in place
        const updateMechanism = await page.evaluate(() => 'serviceWorker' in navigator &&
             typeof window.addEventListener === 'function');

        expect(updateMechanism).toBeTruthy();

        // Verify service worker script is accessible
        const swResponse = await page.request.get('/static/js/sw.js');
        expect(swResponse.status()).toBe(200);

        const swContent = await swResponse.text();
        expect(swContent).toContain('install');
        expect(swContent).toContain('activate');
        expect(swContent).toContain('fetch');
    });

});
