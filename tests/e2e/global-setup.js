/**
 * Playwright Global Setup
 * Runs before all test files
 */

const { spawn } = require('child_process');
const { chromium } = require('@playwright/test');

let djangoServer;

async function globalSetup(config) {
    console.log('🚀 Starting Django test server...');
    
    // Start Django development server for testing
    djangoServer = spawn('python', ['manage.py', 'runserver', '127.0.0.1:8001', '--settings=portfolio_site.settings'], {
        stdio: 'pipe',
        env: {
            ...process.env,
            DEBUG: 'True',
            DJANGO_SETTINGS_MODULE: 'portfolio_site.settings'
        }
    });

    // Wait for server to start
    await new Promise((resolve) => {
        djangoServer.stdout.on('data', (data) => {
            const output = data.toString();
            console.log(`Django: ${output.trim()}`);
            if (output.includes('Starting development server') || output.includes('Watching for file changes')) {
                setTimeout(resolve, 2000); // Give it 2 more seconds to fully start
            }
        });
        
        djangoServer.stderr.on('data', (data) => {
            console.error(`Django Error: ${data.toString().trim()}`);
        });
        
        // Fallback timeout
        setTimeout(resolve, 10000);
    });

    // Store server process globally so it can be killed in teardown
    global.__DJANGO_SERVER__ = djangoServer;
    
    console.log('✅ Django test server started');
}

module.exports = globalSetup;