/**
 * Global Teardown for E2E Tests
 * Cleanup after all tests are complete
 */

async function globalTeardown(config) {
    console.log('🧹 Cleaning up E2E test environment...');

    try {
        // Cleanup any test data or temporary files
        console.log('✅ E2E test environment cleanup complete!');
    } catch (error) {
        console.error('❌ Global teardown failed:', error);
        throw error;
    }
}

module.exports = globalTeardown;
