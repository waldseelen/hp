#!/usr/bin/env node

/**
 * Critical CSS Extraction Script
 * Extracts above-the-fold CSS for different pages to improve loading performance
 */

const critical = require('critical');
const fs = require('fs');
const path = require('path');

// Ensure critical CSS directory exists
const criticalDir = path.join(__dirname, '..', 'static', 'css', 'critical');
if (!fs.existsSync(criticalDir)) {
    fs.mkdirSync(criticalDir, { recursive: true });
}

// Configuration for different page types
const pages = [
    {
        url: 'http://localhost:8000/',
        output: 'home.min.css',
        width: 1300,
        height: 900
    },
    {
        url: 'http://localhost:8000/blog/',
        output: 'blog.min.css',
        width: 1300,
        height: 900
    },
    {
        url: 'http://localhost:8000/tools/',
        output: 'tools.min.css',
        width: 1300,
        height: 900
    },
    {
        url: 'http://localhost:8000/contact/',
        output: 'contact.min.css',
        width: 1300,
        height: 900
    },
    {
        url: 'http://localhost:8000/playground/',
        output: 'playground.min.css',
        width: 1300,
        height: 900
    }
];

async function extractCriticalCSS() {
    console.log('🚀 Starting Critical CSS extraction...');

    for (const page of pages) {
        try {
            console.log(`📄 Extracting critical CSS for ${page.url}...`);

            const result = await critical.generate({
                // Page URL to analyze
                src: page.url,

                // CSS files to analyze
                css: [
                    'static/css/output.css',
                    'static/css/custom.css'
                ],

                // Viewport dimensions
                width: page.width,
                height: page.height,

                // Output settings
                dest: path.join(criticalDir, page.output),
                minify: true,
                extract: false, // Don't remove critical CSS from main files

                // Advanced settings
                timeout: 30000,
                penthouse: {
                    timeout: 60000,
                    maxEmbeddedBase64Length: 1000,
                    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                },

                // Ignore CSS rules for certain selectors
                ignore: {
                    atrule: ['@font-face'],
                    rule: [/\.sr-only/, /\.skip-nav/],
                    decl: (node, value) =>
                    // Ignore large background images in critical CSS
                        /url\(.+\.(jpg|jpeg|png|webp|svg).+\)/.test(value)

                }
            });

            console.log(`✅ Critical CSS extracted for ${page.output} (${Math.round(result.css.length / 1024)}KB)`);

        } catch (error) {
            console.error(`❌ Failed to extract critical CSS for ${page.url}:`, error.message);

            // Create empty critical CSS file as fallback
            fs.writeFileSync(path.join(criticalDir, page.output), '/* Critical CSS extraction failed */');
        }
    }

    console.log('🎉 Critical CSS extraction completed!');
}

// Run extraction if called directly
if (require.main === module) {
    extractCriticalCSS().catch(error => {
        console.error('Fatal error:', error);
        process.exit(1);
    });
}

module.exports = { extractCriticalCSS };
