/**
 * Global Setup for E2E Tests
 * Prepares test environment before running tests
 */

const { chromium } = require('@playwright/test');

async function globalSetup(config) {
    console.log('🚀 Setting up E2E test environment...');

    const browser = await chromium.launch();
    const page = await browser.newPage();

    try {
        // Wait for server to be ready
        const baseURL = config.use?.baseURL || 'http://127.0.0.1:8000';
        console.log(`📡 Checking server availability at ${baseURL}...`);

        let retries = 0;
        const maxRetries = 30; // 30 seconds

        while (retries < maxRetries) {
            try {
                const response = await page.goto(baseURL, { timeout: 5000 });
                if (response && response.status() === 200) {
                    console.log('✅ Server is ready for testing');
                    break;
                }
            } catch (error) {
                retries++;
                if (retries === maxRetries) {
                    throw new Error(`❌ Server not ready after ${maxRetries} seconds`);
                }
                console.log(`⏳ Waiting for server... (${retries}/${maxRetries})`);
                await page.waitForTimeout(1000);
            }
        }

        // Verify critical pages are accessible
        const criticalPages = ['/', '/ui-kit/', '/offline/'];

        for (const pagePath of criticalPages) {
            try {
                const response = await page.goto(`${baseURL}${pagePath}`, { timeout: 10000 });
                if (response && response.status() === 200) {
                    console.log(`✅ ${pagePath} is accessible`);
                }
            } catch (error) {
                console.log(`⚠️  ${pagePath} is not accessible: ${error.message}`);
            }
        }

        console.log('🎯 E2E test environment setup complete!');

    } catch (error) {
        console.error('❌ Global setup failed:', error);
        throw error;
    } finally {
        await browser.close();
    }
}

module.exports = globalSetup;
