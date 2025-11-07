/**
 * ==========================================================================
 * PLAYWRIGHT.CONFIG.JS - End-to-End Testing Configuration
 * ==========================================================================
 * Comprehensive E2E testing configuration for Django portfolio project
 * Tests PWA functionality, performance, and user workflows across browsers
 * ==========================================================================
 */

import { defineConfig, devices } from '@playwright/test';

/**
 * @see https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
    // Test Directory
    testDir: './tests/e2e',

    // Run tests in files in parallel
    fullyParallel: true,

    // Fail the build on CI if you accidentally left test.only in the source code
    forbidOnly: !!process.env.CI,

    // Retry on CI only
    retries: process.env.CI ? 2 : 0,

    // Opt out of parallel tests on CI
    workers: process.env.CI ? 1 : undefined,

    // Reporter to use
    reporter: [
        ['html', { outputFolder: 'playwright-report' }],
        ['json', { outputFile: 'playwright-report/results.json' }],
        ['junit', { outputFile: 'playwright-report/results.xml' }],
        process.env.CI ? ['github'] : ['list']
    ],

    // Global test timeout
    timeout: 30 * 1000,

    // Global setup timeout
    globalTimeout: 60 * 1000 * 5,

    // Expect timeout
    expect: {
        timeout: 5000
    },

    // Shared settings for all the projects below
    use: {
    // Base URL to use in actions like `await page.goto('/')`
        baseURL: process.env.BASE_URL || 'http://127.0.0.1:8001',

        // Collect trace when retrying the failed test
        trace: 'on-first-retry',

        // Record video on failure
        video: 'retain-on-failure',

        // Take screenshot on failure
        screenshot: 'only-on-failure',

        // Browser context options
        viewport: { width: 1280, height: 720 },
        ignoreHTTPSErrors: true,

        // Permissions for PWA testing
        permissions: ['notifications'],

        // Service Worker support
        serviceWorkers: 'allow',

        // Local storage and session storage
        storageState: undefined
    },

    // Configure projects for major browsers
    projects: [
    // Desktop Browsers
        {
            name: 'chromium',
            use: { ...devices['Desktop Chrome'] },
        },
        {
            name: 'firefox',
            use: { ...devices['Desktop Firefox'] },
        },
        {
            name: 'webkit',
            use: { ...devices['Desktop Safari'] },
        },

        // Mobile Testing
        {
            name: 'Mobile Chrome',
            use: { ...devices['Pixel 5'] },
        },
        {
            name: 'Mobile Safari',
            use: { ...devices['iPhone 12'] },
        },

        // PWA Testing
        {
            name: 'PWA Chrome',
            use: {
                ...devices['Desktop Chrome'],
                channel: 'chrome',
                launchOptions: {
                    args: [
                        '--enable-features=VaapiVideoDecoder',
                        '--use-gl=egl',
                        '--enable-web-app-manifests',
                        '--enable-experimental-web-platform-features'
                    ]
                }
            },
        },

        // Performance Testing
        {
            name: 'Performance',
            use: {
                ...devices['Desktop Chrome'],
                channel: 'chrome',
                launchOptions: {
                    args: ['--enable-precise-memory-info']
                }
            },
            grep: /@performance/
        },

        // Accessibility Testing
        {
            name: 'Accessibility',
            use: { ...devices['Desktop Chrome'] },
            grep: /@accessibility/
        }
    ],

    // Global Setup
    globalSetup: require.resolve('./tests/e2e/global-setup.js'),

    // Global Teardown
    globalTeardown: require.resolve('./tests/e2e/global-teardown.js'),

    // Web Server Configuration
    webServer: process.env.CI ? undefined : {
        command: 'python portfolio_site/manage.py runserver 127.0.0.1:8001',
        url: 'http://127.0.0.1:8001',
        reuseExistingServer: !process.env.CI,
        timeout: 120 * 1000,
        stdout: 'ignore',
        stderr: 'pipe'
    },

    // Test metadata
    metadata: {
        'test-type': 'e2e',
        'test-framework': 'playwright',
        'project': 'django-portfolio',
        'environment': process.env.NODE_ENV || 'development'
    }
});
