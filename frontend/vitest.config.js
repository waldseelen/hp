/**
 * ==========================================================================
 * VITEST.CONFIG.JS - JavaScript Unit Testing Configuration
 * ==========================================================================
 * Comprehensive Vitest configuration for Django portfolio project
 * Tests JavaScript modules including PWA, performance monitoring, and UI
 * ==========================================================================
 */

import { defineConfig } from 'vitest/config';
import path from 'path';

export default defineConfig({
    test: {
    // Test Environment
        environment: 'jsdom',

        // Test File Patterns
        include: [
            'tests/unit/**/*.test.js',
            'tests/unit/**/*.spec.js',
            'static/js/**/*.test.js'
        ],
        exclude: [
            'node_modules/**',
            'tests/e2e/**',
            'staticfiles/**'
        ],

        // Global Test Configuration
        globals: true,

        // Setup Files
        setupFiles: [
            'tests/unit/setup.js'
        ],

        // Coverage Configuration
        coverage: {
            provider: 'v8',
            reporter: ['text', 'json', 'html', 'lcov'],
            reportsDirectory: 'coverage',
            include: [
                'static/js/**/*.js'
            ],
            exclude: [
                'static/js/**/*.test.js',
                'static/js/**/*.spec.js',
                'static/js/sw.js', // Service Worker tested separately
                'node_modules/**',
                'staticfiles/**'
            ],
            thresholds: {
                global: {
                    branches: 80,
                    functions: 80,
                    lines: 80,
                    statements: 80
                }
            }
        },

        // Test Timeout
        testTimeout: 10000,

        // Mock Configuration
        clearMocks: true,
        restoreMocks: true,

        // Parallel Execution
        pool: 'threads',
        poolOptions: {
            threads: {
                minThreads: 1,
                maxThreads: 4
            }
        }
    },

    // Path Resolution
    resolve: {
        alias: {
            '@': path.resolve(__dirname, 'static/js'),
            '@css': path.resolve(__dirname, 'static/css'),
            '@tests': path.resolve(__dirname, 'tests')
        }
    },

    // Define Global Variables
    define: {
        'process.env.NODE_ENV': JSON.stringify('test'),
        'process.env.DJANGO_SETTINGS_MODULE': JSON.stringify('portfolio_site.settings'),
        '__VITEST__': true
    },

    // Server Configuration for Testing
    server: {
        deps: {
            inline: ['vitest-canvas-mock']
        }
    },

    // Optimization for Testing
    esbuild: {
        target: 'node14'
    }
});
