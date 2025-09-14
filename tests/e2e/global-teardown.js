/**
 * Playwright Global Teardown
 * Runs after all test files
 */

async function globalTeardown(config) {
    console.log('🛑 Shutting down Django test server...');
    
    // Kill Django server if it exists
    const djangoServer = global.__DJANGO_SERVER__;
    if (djangoServer && !djangoServer.killed) {
        djangoServer.kill('SIGTERM');
        
        // Wait for graceful shutdown
        await new Promise((resolve) => {
            djangoServer.on('close', () => {
                console.log('✅ Django test server stopped');
                resolve();
            });
            
            // Force kill after 5 seconds if not stopped
            setTimeout(() => {
                if (!djangoServer.killed) {
                    djangoServer.kill('SIGKILL');
                }
                resolve();
            }, 5000);
        });
    }
}

module.exports = globalTeardown;