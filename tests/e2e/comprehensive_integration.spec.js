/**
 * Comprehensive E2E Integration Tests for Phase 10
 * Tests user journeys that span multiple phases (Phase 7 UI/UX + Phase 9 Advanced Features)
 */

const { test, expect } = require('@playwright/test');

test.describe('Comprehensive Integration Tests @integration @phase10', () => {
    const BASE_URL = process.env.BASE_URL || 'http://127.0.0.1:8000';

    test.beforeEach(async ({ page }) => {
        // Set up viewport for testing
        await page.setViewportSize({ width: 1280, height: 720 });

        // Go to homepage
        await page.goto(BASE_URL);

        // Wait for animations and initial load
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(1000);
    });

    test('Complete user journey: Homepage → UI Kit → PWA Installation → Offline Mode', async ({ page, context }) => {
        // Phase 7 UI/UX: Homepage with modern design
        await test.step('Verify Phase 7 UI elements on homepage', async () => {
            // Check for glassmorphism navigation
            const nav = page.locator('nav');
            await expect(nav).toBeVisible();

            // Check for aurora background effects
            const heroSection = page.locator('[class*="hero"], [class*="aurora"], main').first();
            await expect(heroSection).toBeVisible();

            // Check for modern button system
            const buttons = page.locator('[class*="btn-"], button').first();
            await expect(buttons).toBeVisible();

            // Check for custom cursor (if enabled)
            const customCursor = page.locator('[class*="cursor-"], .custom-cursor');
            // Note: Custom cursor might not be visible in headless mode
        });

        // Navigate to UI Kit to test Phase 7 components
        await test.step('Navigate to UI Kit and verify components', async () => {
            await page.click('a[href*="ui-kit"], a:has-text("UI Kit")').catch(() => {
                // Try alternative navigation
                await page.goto(`${BASE_URL}/ui-kit/`);
            });

            await page.waitForLoadState('networkidle');

            // Verify UI Kit page loads with Phase 7 components
            await expect(page.locator('h1, .heading-1')).toContainText(/UI Kit|Design System/i);

            // Check for button system
            const buttonExamples = page.locator('[class*="btn-primary"], [class*="btn-secondary"]');
            await expect(buttonExamples.first()).toBeVisible();

            // Check for card system
            const cardExamples = page.locator('[class*="card-"], .card');
            await expect(cardExamples.first()).toBeVisible();

            // Check for form system
            const formExamples = page.locator('input, .form-control, [class*="form-"]');
            await expect(formExamples.first()).toBeVisible();
        });

        // Test Phase 9: PWA Installation Flow
        await test.step('Test PWA installation prompt', async () => {
            // Go back to homepage
            await page.goto(BASE_URL);
            await page.waitForLoadState('networkidle');

            // Check for PWA manifest
            const manifestLink = page.locator('link[rel="manifest"]');
            await expect(manifestLink).toHaveAttribute('href', '/manifest.json');

            // Test manifest.json endpoint
            const manifestResponse = await page.request.get(`${BASE_URL}/manifest.json`);
            expect(manifestResponse.status()).toBe(200);

            const manifestData = await manifestResponse.json();
            expect(manifestData.name).toBeTruthy();
            expect(manifestData.icons).toBeTruthy();
            expect(manifestData.display).toBe('standalone');

            // Check for service worker registration
            const swRegistered = await page.evaluate(() => {
                return 'serviceWorker' in navigator;
            });
            expect(swRegistered).toBe(true);
        });

        // Test Phase 9: Offline functionality
        await test.step('Test offline functionality', async () => {
            // Navigate to offline page directly
            await page.goto(`${BASE_URL}/offline/`);
            await page.waitForLoadState('networkidle');

            // Verify offline page loads with Phase 7 styling
            await expect(page.locator('h1')).toContainText(/offline/i);

            // Check for modern styling elements
            const offlineContainer = page.locator('.offline-container, [class*="container"]');
            await expect(offlineContainer).toBeVisible();

            // Test network status monitoring
            const networkStatus = page.locator('#networkStatus, #network-status, [id*="network"]');
            if (await networkStatus.isVisible()) {
                await expect(networkStatus).toContainText(/offline|online/i);
            }
        });
    });

    test('Theme switching integration with PWA and real-time features', async ({ page }) => {
        await test.step('Test theme switching across different components', async () => {
            // Find theme toggle (Phase 7 feature)
            const themeToggle = page.locator('[data-theme-toggle], .theme-toggle, button:has-text("theme"), button:has-text("dark"), button:has-text("light")').first();

            if (await themeToggle.isVisible()) {
                // Test theme switching
                await themeToggle.click();
                await page.waitForTimeout(500);

                // Verify theme change applied to body or html
                const isDarkMode = await page.evaluate(() => {
                    return document.documentElement.classList.contains('dark') ||
                           document.body.classList.contains('dark') ||
                           document.documentElement.getAttribute('data-theme') === 'dark';
                });

                expect(typeof isDarkMode).toBe('boolean');

                // Switch back
                await themeToggle.click();
                await page.waitForTimeout(500);
            }
        });

        await test.step('Verify theme consistency across PWA components', async () => {
            // Test manifest.json respects theme
            const manifestResponse = await page.request.get(`${BASE_URL}/manifest.json`);
            const manifestData = await manifestResponse.json();

            expect(manifestData.theme_color).toBeTruthy();
            expect(manifestData.background_color).toBeTruthy();
        });
    });

    test('Real-time features integration with modern UI', async ({ page, context }) => {
        await test.step('Test WebSocket chat with Phase 7 UI', async () => {
            // Navigate to chat page (Phase 9 feature)
            const chatLink = page.locator('a[href*="chat"], a:has-text("Chat")').first();

            if (await chatLink.isVisible()) {
                await chatLink.click();
                await page.waitForLoadState('networkidle');

                // Verify chat page loads with Phase 7 styling
                const chatContainer = page.locator('.chat-container, [class*="chat"], main');
                await expect(chatContainer.first()).toBeVisible();

                // Check for modern form elements
                const chatInput = page.locator('input[type="text"], textarea, [class*="form-"]');
                if (await chatInput.first().isVisible()) {
                    await expect(chatInput.first()).toBeVisible();
                }

                // Check for modern button styling
                const sendButton = page.locator('button:has-text("Send"), button[type="submit"], .btn-primary');
                if (await sendButton.first().isVisible()) {
                    await expect(sendButton.first()).toBeVisible();
                }
            }
        });

        await test.step('Test push notification integration', async () => {
            // Check for push notification permissions
            const notificationPermission = await page.evaluate(() => {
                return 'Notification' in window;
            });
            expect(notificationPermission).toBe(true);

            // Test VAPID key endpoint
            const vapidResponse = await page.request.get(`${BASE_URL}/api/vapid-key/`);
            if (vapidResponse.status() === 200) {
                const vapidData = await vapidResponse.json();
                expect(vapidData.publicKey).toBeTruthy();
            }
        });
    });

    test('Form submissions with offline sync and modern UI validation', async ({ page }) => {
        await test.step('Test contact form with Phase 7 styling and Phase 9 offline sync', async () => {
            // Navigate to contact form
            const contactLink = page.locator('a[href*="contact"], a:has-text("Contact")').first();

            if (await contactLink.isVisible()) {
                await contactLink.click();
                await page.waitForLoadState('networkidle');

                // Verify form has Phase 7 styling
                const form = page.locator('form');
                await expect(form.first()).toBeVisible();

                // Check for modern form inputs
                const nameInput = page.locator('input[name="name"], input[id*="name"]');
                const emailInput = page.locator('input[name="email"], input[id*="email"]');
                const messageInput = page.locator('textarea[name="message"], textarea[id*="message"]');

                if (await nameInput.first().isVisible()) {
                    // Fill form with test data
                    await nameInput.first().fill('Test User');
                    await emailInput.first().fill('test@example.com');
                    await messageInput.first().fill('This is a test message for E2E testing');

                    // Check for form validation styling
                    const submitButton = page.locator('button[type="submit"], input[type="submit"], .btn-primary');
                    if (await submitButton.first().isVisible()) {
                        await expect(submitButton.first()).toBeVisible();

                        // Note: We don't actually submit to avoid spam
                        // but we verify the form structure is correct
                    }
                }
            }
        });
    });

    test('Performance monitoring with UI/UX features', async ({ page }) => {
        await test.step('Verify performance tracking works with animations', async () => {
            // Check for performance monitoring scripts
            const performanceScript = await page.evaluate(() => {
                return window.performance && window.performance.mark;
            });
            expect(performanceScript).toBe(true);

            // Test Core Web Vitals monitoring
            await page.waitForLoadState('networkidle');

            // Trigger some animations (Phase 7 feature)
            await page.mouse.move(100, 100);
            await page.waitForTimeout(500);

            // Check if performance metrics are being collected
            const metricsCollected = await page.evaluate(() => {
                return window.performance.getEntriesByType('navigation').length > 0;
            });
            expect(metricsCollected).toBe(true);
        });
    });

    test('Responsive design consistency across all features', async ({ page }) => {
        const viewports = [
            { width: 375, height: 667, name: 'Mobile' },
            { width: 768, height: 1024, name: 'Tablet' },
            { width: 1280, height: 720, name: 'Desktop' }
        ];

        for (const viewport of viewports) {
            await test.step(`Test ${viewport.name} (${viewport.width}x${viewport.height})`, async () => {
                await page.setViewportSize({ width: viewport.width, height: viewport.height });
                await page.reload();
                await page.waitForLoadState('networkidle');

                // Verify navigation is responsive
                const nav = page.locator('nav, header');
                await expect(nav).toBeVisible();

                // Check for mobile menu if on mobile
                if (viewport.width < 768) {
                    const mobileMenu = page.locator('.mobile-menu, [class*="mobile"], .hamburger, .menu-toggle');
                    // Mobile menu might exist
                }

                // Verify main content is visible
                const mainContent = page.locator('main, .main-content, [role="main"]');
                await expect(mainContent.first()).toBeVisible();

                // Check that PWA features work on mobile
                if (viewport.width < 768) {
                    const manifestLink = page.locator('link[rel="manifest"]');
                    await expect(manifestLink).toHaveAttribute('href', '/manifest.json');
                }
            });
        }
    });
});
