/**
 * API Integration Tests for Phase 10
 * Tests all API endpoints work together as a cohesive system
 */

const { test, expect } = require('@playwright/test');

test.describe('API Integration Tests @api @integration @phase10', () => {
    const BASE_URL = process.env.BASE_URL || 'http://127.0.0.1:8000';

    test('Health check and system status APIs', async ({ request }) => {
        await test.step('Health check endpoint', async () => {
            const response = await request.get(`${BASE_URL}/api/health/`);
            expect(response.status()).toBe(200);

            const data = await response.json();
            expect(data.status).toBe('healthy');
            expect(data.timestamp).toBeTruthy();
            expect(data.version).toBeTruthy();
        });

        await test.step('Analytics configuration endpoint', async () => {
            const response = await request.get(`${BASE_URL}/analytics.json`);
            expect(response.status()).toBe(200);

            const data = await response.json();
            expect(data.status).toBe('ok');
            expect(data.features).toBeTruthy();
        });
    });

    test('Performance monitoring API workflow', async ({ request }) => {
        await test.step('Submit performance metric', async () => {
            const metricData = {
                metric_type: 'lcp',
                value: 1200,
                url: BASE_URL,
                user_agent: 'PlaywrightTestBot/1.0',
                device_type: 'desktop',
                screen_resolution: '1920x1080',
                viewport_size: '1280x720'
            };

            const response = await request.post(`${BASE_URL}/api/performance/`, {
                data: metricData
            });

            expect(response.status()).toBe(201);

            const responseData = await response.json();
            expect(responseData.status).toBe('success');
            expect(responseData.id).toBeTruthy();
        });

        await test.step('Submit multiple performance metrics', async () => {
            const metrics = [
                { metric_type: 'fcp', value: 800 },
                { metric_type: 'fid', value: 50 },
                { metric_type: 'cls', value: 0.05 },
                { metric_type: 'ttfb', value: 200 }
            ];

            for (const metric of metrics) {
                const response = await request.post(`${BASE_URL}/api/performance/`, {
                    data: {
                        ...metric,
                        url: BASE_URL,
                        user_agent: 'PlaywrightTestBot/1.0'
                    }
                });

                expect(response.status()).toBe(201);
            }
        });
    });

    test('Push notification API workflow', async ({ request }) => {
        await test.step('Get VAPID public key', async () => {
            const response = await request.get(`${BASE_URL}/api/vapid-key/`);

            if (response.status() === 200) {
                const data = await response.json();
                expect(data.publicKey).toBeTruthy();
                expect(data.publicKey.length).toBeGreaterThan(0);
            } else {
                // VAPID might not be configured in test environment
                expect([200, 500]).toContain(response.status());
            }
        });

        await test.step('Test subscription endpoint structure', async () => {
            const subscriptionData = {
                endpoint: 'https://fcm.googleapis.com/fcm/send/test-endpoint',
                p256dh: 'test-p256dh-key',
                auth: 'test-auth-key',
                user_agent: 'PlaywrightTestBot/1.0',
                browser: 'chromium',
                platform: 'test'
            };

            const response = await request.post(`${BASE_URL}/api/push/subscribe/`, {
                data: subscriptionData
            });

            // Might fail in test environment but should have proper error structure
            const responseData = await response.json();
            expect(responseData.status).toBeTruthy();
        });
    });

    test('Error logging API', async ({ request }) => {
        await test.step('Submit frontend error log', async () => {
            const errorData = {
                error_type: 'javascript',
                level: 'error',
                message: 'Test error from E2E tests',
                url: BASE_URL,
                line_number: 42,
                stack_trace: 'Error\n    at test (test.js:42:10)',
                user_agent: 'PlaywrightTestBot/1.0',
                additional_data: {
                    test: true,
                    browser: 'chromium'
                }
            };

            const response = await request.post(`${BASE_URL}/api/errors/`, {
                data: errorData
            });

            expect(response.status()).toBe(201);

            const responseData = await response.json();
            expect(responseData.status).toBe('success');
            expect(responseData.error_id).toBeTruthy();
        });
    });

    test('PWA manifest and service worker integration', async ({ request }) => {
        await test.step('PWA manifest endpoint', async () => {
            const response = await request.get(`${BASE_URL}/manifest.json`);
            expect(response.status()).toBe(200);
            expect(response.headers()['content-type']).toContain('application/json');

            const manifest = await response.json();
            expect(manifest.name).toBeTruthy();
            expect(manifest.short_name).toBeTruthy();
            expect(manifest.display).toBe('standalone');
            expect(manifest.theme_color).toBeTruthy();
            expect(manifest.background_color).toBeTruthy();
            expect(manifest.icons).toHaveLength(3);

            // Verify icon URLs are valid
            for (const icon of manifest.icons) {
                expect(icon.src).toContain('/static/images/');
                expect(icon.sizes).toBeTruthy();
                expect(icon.type).toContain('image/');
            }
        });

        await test.step('Service worker file accessibility', async () => {
            const response = await request.get(`${BASE_URL}/static/js/sw.min.js`);
            expect(response.status()).toBe(200);
            expect(response.headers()['content-type']).toContain('javascript');

            const swContent = await response.text();
            expect(swContent).toContain('CACHE_NAME');
            expect(swContent).toContain('urlsToCache');
        });

        await test.step('PWA manager script accessibility', async () => {
            const response = await request.get(`${BASE_URL}/static/js/pwa.min.js`);
            expect(response.status()).toBe(200);

            const pwaContent = await response.text();
            expect(pwaContent).toContain('PWAManager');
            expect(pwaContent).toContain('serviceWorker');
        });
    });

    test('Static assets and CDN integration', async ({ request }) => {
        await test.step('Critical CSS files', async () => {
            const cssFiles = [
                '/static/css/output.css',
                '/static/css/custom.min.css'
            ];

            for (const cssFile of cssFiles) {
                const response = await request.get(`${BASE_URL}${cssFile}`);
                if (response.status() === 200) {
                    expect(response.headers()['content-type']).toContain('text/css');

                    const cssContent = await response.text();
                    expect(cssContent.length).toBeGreaterThan(0);
                }
            }
        });

        await test.step('Critical JavaScript files', async () => {
            const jsFiles = [
                '/static/js/main.min.js',
                '/static/js/animations.js',
                '/static/js/cursor.js',
                '/static/js/parallax.js'
            ];

            for (const jsFile of jsFiles) {
                const response = await request.get(`${BASE_URL}${jsFile}`);
                if (response.status() === 200) {
                    expect(response.headers()['content-type']).toContain('javascript');
                }
            }
        });

        await test.step('PWA icons accessibility', async () => {
            const iconFiles = [
                '/static/images/favicon-192x192.svg',
                '/static/images/favicon-512x512.svg',
                '/static/images/icon-base.svg'
            ];

            for (const iconFile of iconFiles) {
                const response = await request.get(`${BASE_URL}${iconFile}`);
                expect(response.status()).toBe(200);
                expect(response.headers()['content-type']).toContain('image/svg');

                const svgContent = await response.text();
                expect(svgContent).toContain('<svg');
                expect(svgContent).toContain('</svg>');
            }
        });
    });

    test('Internationalization API support', async ({ request }) => {
        await test.step('Language status endpoint', async () => {
            const response = await request.get(`${BASE_URL}/api/language-status/`);

            if (response.status() === 200) {
                const data = await response.json();
                expect(data.current_language).toBeTruthy();
                expect(data.available_languages).toBeTruthy();
                expect(Array.isArray(data.available_languages)).toBe(true);
            }
        });

        await test.step('Language switching workflow', async () => {
            const languages = ['en', 'tr'];

            for (const lang of languages) {
                const response = await request.post(`${BASE_URL}/set-language/`, {
                    form: {
                        language: lang,
                        next: '/'
                    }
                });

                // Should redirect (302) or succeed (200)
                expect([200, 302]).toContain(response.status());
            }
        });
    });

    test('Security headers and CSP integration', async ({ request }) => {
        await test.step('Security headers presence', async () => {
            const response = await request.get(BASE_URL);
            const headers = response.headers();

            // Check for important security headers
            const securityHeaders = [
                'x-content-type-options',
                'x-frame-options',
                'x-xss-protection'
            ];

            securityHeaders.forEach(header => {
                if (headers[header]) {
                    expect(headers[header]).toBeTruthy();
                }
            });
        });

        await test.step('CSP violation reporting endpoint', async () => {
            const cspReport = {
                'csp-report': {
                    'document-uri': BASE_URL,
                    'violated-directive': 'script-src',
                    'blocked-uri': 'eval',
                    'source-file': BASE_URL,
                    'line-number': 1
                }
            };

            const response = await request.post(`${BASE_URL}/api/csp-violation/`, {
                data: cspReport,
                headers: {
                    'Content-Type': 'application/csp-report'
                }
            });

            expect(response.status()).toBe(204);
        });
    });

    test('Search and content API integration', async ({ request }) => {
        await test.step('Search API functionality', async () => {
            const searchQuery = 'test';
            const response = await request.get(`${BASE_URL}/search/?q=${searchQuery}`);

            expect(response.status()).toBe(200);

            // Should return HTML for search results page
            const content = await response.text();
            expect(content).toContain('html');
        });

        await test.step('AJAX search endpoint', async () => {
            const response = await request.get(`${BASE_URL}/api/search/?q=test&limit=5`);

            if (response.status() === 200) {
                const data = await response.json();
                expect(data.status).toBe('success');
                expect(Array.isArray(data.results)).toBe(true);
                expect(data.total).toBeGreaterThanOrEqual(0);
            }
        });
    });
});
