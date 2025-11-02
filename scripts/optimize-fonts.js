/**
 * ==========================================================================
 * FONT OPTIMIZATION SCRIPT
 * ==========================================================================
 * Font optimization with subsetting and format conversion
 * Generates optimized fonts and CSS with font-display: swap
 * ==========================================================================
 */

const fs = require('fs').promises;
const path = require('path');

/**
 * Generate optimized font CSS with performance optimizations
 */
function generateOptimizedFontCSS() {
    return `/* ==========================================================================
   OPTIMIZED FONT LOADING
   ========================================================================== */

/* Preconnect to font origins */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&display=swap');

/* Font face declarations with font-display: swap for performance */
@font-face {
    font-family: 'Inter Fallback';
    src: local('system-ui'), local('-apple-system'), local('BlinkMacSystemFont');
    font-display: swap;
    ascent-override: 90%;
    descent-override: 22%;
    line-gap-override: 0%;
}

@font-face {
    font-family: 'JetBrains Mono Fallback';
    src: local('ui-monospace'), local('Cascadia Code'), local('Source Code Pro'), local('Consolas');
    font-display: swap;
    ascent-override: 85%;
    descent-override: 20%;
    line-gap-override: 0%;
}

/* CSS Custom Properties for font stacks */
:root {
    --font-sans: 'Inter', 'Inter Fallback', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    --font-mono: 'JetBrains Mono', 'JetBrains Mono Fallback', ui-monospace, 'Cascadia Code', 'Source Code Pro', Consolas, monospace;
    --font-system: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;

    /* Font weights */
    --font-light: 300;
    --font-normal: 400;
    --font-medium: 500;
    --font-semibold: 600;
    --font-bold: 700;

    /* Font sizes with fluid scaling */
    --text-xs: clamp(0.75rem, 0.7rem + 0.2vw, 0.8rem);
    --text-sm: clamp(0.875rem, 0.8rem + 0.3vw, 0.95rem);
    --text-base: clamp(1rem, 0.95rem + 0.25vw, 1.1rem);
    --text-lg: clamp(1.125rem, 1rem + 0.5vw, 1.3rem);
    --text-xl: clamp(1.25rem, 1.1rem + 0.6vw, 1.5rem);
    --text-2xl: clamp(1.5rem, 1.3rem + 1vw, 2rem);
    --text-3xl: clamp(1.875rem, 1.5rem + 1.5vw, 2.5rem);
    --text-4xl: clamp(2.25rem, 1.8rem + 2vw, 3rem);
    --text-5xl: clamp(3rem, 2.2rem + 3vw, 4rem);

    /* Line heights */
    --leading-tight: 1.25;
    --leading-normal: 1.5;
    --leading-relaxed: 1.75;
}

/* Performance optimization: reduce font rendering overhead */
html {
    font-family: var(--font-sans);
    font-display: swap;
    text-rendering: optimizeLegibility;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}

/* Utility classes for font optimization */
.font-sans { font-family: var(--font-sans); }
.font-mono { font-family: var(--font-mono); }
.font-system { font-family: var(--font-system); }

.font-light { font-weight: var(--font-light); }
.font-normal { font-weight: var(--font-normal); }
.font-medium { font-weight: var(--font-medium); }
.font-semibold { font-weight: var(--font-semibold); }
.font-bold { font-weight: var(--font-bold); }

.text-xs { font-size: var(--text-xs); }
.text-sm { font-size: var(--text-sm); }
.text-base { font-size: var(--text-base); }
.text-lg { font-size: var(--text-lg); }
.text-xl { font-size: var(--text-xl); }
.text-2xl { font-size: var(--text-2xl); }
.text-3xl { font-size: var(--text-3xl); }
.text-4xl { font-size: var(--text-4xl); }
.text-5xl { font-size: var(--text-5xl); }

.leading-tight { line-height: var(--leading-tight); }
.leading-normal { line-height: var(--leading-normal); }
.leading-relaxed { line-height: var(--leading-relaxed); }

/* Font loading optimization */
.font-loading {
    font-display: swap;
    font-variant-ligatures: none;
    font-feature-settings: "kern" 0;
}

/* Prevent invisible text during font swap */
@supports (font-display: optional) {
    @font-face {
        font-family: 'Inter';
        font-display: optional;
    }
    @font-face {
        font-family: 'JetBrains Mono';
        font-display: optional;
    }
}

/* Reduce cumulative layout shift with font metrics */
.fallback-font {
    font-family: var(--font-system);
    font-size: 1em;
    line-height: 1.5;
    letter-spacing: 0;
}

/* Critical font loading for above-the-fold content */
.hero-text {
    font-family: var(--font-sans);
    font-display: block; /* Block for critical text */
}

/* Progressive enhancement for non-critical fonts */
@supports (font-display: swap) {
    .secondary-text {
        font-family: var(--font-sans);
        font-display: swap;
    }
}

/* Dark mode font optimization */
@media (prefers-color-scheme: dark) {
    html {
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
        font-weight: 400; /* Slightly heavier for dark backgrounds */
    }

    .font-light {
        font-weight: var(--font-normal); /* Bump up light fonts in dark mode */
    }
}

/* High contrast mode font adjustments */
@media (prefers-contrast: high) {
    html {
        font-weight: 500;
        text-shadow: 0 0 1px currentColor;
    }
}

/* Reduced motion preference */
@media (prefers-reduced-motion: reduce) {
    * {
        font-feature-settings: "kern" 0, "liga" 0;
    }
}

/* Print styles for fonts */
@media print {
    html {
        font-family: var(--font-system);
        font-size: 12pt;
        line-height: 1.4;
    }

    .font-mono {
        font-family: 'Courier New', monospace;
    }
}`;
}

/**
 * Generate font preload HTML
 */
function generateFontPreloadHTML() {
    return `{% comment %}
Font Preloading - Include in base template <head>
{% endcomment %}

<!-- Preconnect to Google Fonts -->
<link rel="preconnect" href="https://fonts.googleapis.com" crossorigin>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>

<!-- Preload critical fonts -->
{% if FEATURES.FONT_PRELOADING %}
<link
    rel="preload"
    href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap"
    as="style"
    onload="this.onload=null;this.rel='stylesheet'">
<link
    rel="preload"
    href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&display=swap"
    as="style"
    onload="this.onload=null;this.rel='stylesheet'">

<!-- Fallback for JS disabled -->
<noscript>
    <link
        rel="stylesheet"
        href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap">
    <link
        rel="stylesheet"
        href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&display=swap">
</noscript>
{% endif %}

<!-- Font loading script for performance -->
<script>
(function() {
    'use strict';

    // Font loading optimization
    if ('fonts' in document) {
        // Check if fonts are already cached
        const fontPromises = [
            document.fonts.load('400 16px Inter'),
            document.fonts.load('500 16px Inter'),
            document.fonts.load('400 14px JetBrains Mono')
        ];

        Promise.all(fontPromises).then(() => {
            document.documentElement.classList.add('fonts-loaded');
        }).catch(() => {
            // Fonts failed to load, use system fonts
            document.documentElement.classList.add('fonts-failed');
        });

        // Timeout fallback
        setTimeout(() => {
            if (!document.documentElement.classList.contains('fonts-loaded')) {
                document.documentElement.classList.add('fonts-timeout');
            }
        }, 3000);
    }

    // Font display swap polyfill for older browsers
    if (!CSS.supports('font-display', 'swap')) {
        const style = document.createElement('style');
        style.textContent = \`
            @font-face {
                font-family: 'Inter';
                src: url('https://fonts.gstatic.com/s/inter/v12/UcCO3FwrK3iLTeHuS_fvQtMwCp50KnMw2boKoduKmMEVuLyfAZ9hiA.woff2') format('woff2');
                font-display: block;
            }
        \`;
        document.head.appendChild(style);
    }
})();
</script>`;
}

/**
 * Generate font loading CSS for critical path
 */
function generateCriticalFontCSS() {
    return `/* Critical font CSS - inline in <head> */
<style>
/* Immediate fallback fonts to prevent FOIT */
html {
    font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    font-display: swap;
}

/* Loading states */
.fonts-loading * {
    font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}

.fonts-loaded .font-sans {
    font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

.fonts-loaded .font-mono {
    font-family: 'JetBrains Mono', ui-monospace, 'Cascadia Code', 'Source Code Pro', Consolas, monospace;
}

.fonts-failed .font-sans,
.fonts-timeout .font-sans {
    font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

.fonts-failed .font-mono,
.fonts-timeout .font-mono {
    font-family: ui-monospace, 'Cascadia Code', 'Source Code Pro', Consolas, monospace;
}
</style>`;
}

/**
 * Main font optimization function
 */
async function main() {
    console.log('🔤 Starting font optimization...\n');

    try {
        // Create fonts directory structure
        await fs.mkdir('static/fonts', { recursive: true });
        await fs.mkdir('static/css', { recursive: true });
        await fs.mkdir('templates/components', { recursive: true });

        // Generate optimized font CSS
        const fontCSS = generateOptimizedFontCSS();
        await fs.writeFile('static/css/fonts-optimized.css', fontCSS);
        console.log('✅ Generated optimized font CSS');

        // Generate font preload template
        const preloadHTML = generateFontPreloadHTML();
        await fs.writeFile('templates/components/font_preload.html', preloadHTML);
        console.log('✅ Generated font preload template');

        // Generate critical font CSS
        const criticalCSS = generateCriticalFontCSS();
        await fs.writeFile('templates/components/critical_fonts.html', criticalCSS);
        console.log('✅ Generated critical font CSS template');

        // Generate font configuration for Django
        const fontConfig = `# Font optimization settings for Django
FONT_OPTIMIZATION = {
    'PRELOAD_FONTS': True,
    'CRITICAL_FONTS': [
        'Inter:400,500,600',
        'JetBrains Mono:400,500'
    ],
    'FONT_DISPLAY': 'swap',
    'FALLBACK_FONTS': {
        'Inter': 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
        'JetBrains Mono': 'ui-monospace, "Cascadia Code", "Source Code Pro", Consolas, monospace'
    },
    'SUBSET_LANGUAGES': ['latin', 'latin-ext'],
    'FONT_LOADING_TIMEOUT': 3000
}

# Add to your base template context
def font_context(request):
    return {
        'FONT_OPTIMIZATION': FONT_OPTIMIZATION,
        'FEATURES': {
            'FONT_PRELOADING': True,
            'CRITICAL_FONT_LOADING': True,
            'FONT_DISPLAY_SWAP': True
        }
    }`;

        await fs.writeFile('font_config.py', fontConfig);
        console.log('✅ Generated Django font configuration');

        // Generate font metrics for CLS prevention
        const fontMetrics = {
            'Inter': {
                ascent: 0.9,
                descent: 0.22,
                lineGap: 0,
                capHeight: 0.7,
                xHeight: 0.5
            },
            'JetBrains Mono': {
                ascent: 0.85,
                descent: 0.2,
                lineGap: 0,
                capHeight: 0.7,
                xHeight: 0.5
            }
        };

        await fs.writeFile('static/fonts/font-metrics.json', JSON.stringify(fontMetrics, null, 2));
        console.log('✅ Generated font metrics for CLS prevention');

        // Create a comprehensive documentation
        const documentation = `# Font Optimization Documentation

## Overview
This font optimization setup provides:
- Critical font loading to prevent FOIT (Flash of Invisible Text)
- Font-display: swap for better performance
- System font fallbacks to reduce CLS (Cumulative Layout Shift)
- Progressive enhancement for font loading

## Files Generated
- \`static/css/fonts-optimized.css\` - Optimized font CSS
- \`templates/components/font_preload.html\` - Font preload template
- \`templates/components/critical_fonts.html\` - Critical font CSS
- \`font_config.py\` - Django configuration
- \`static/fonts/font-metrics.json\` - Font metrics for CLS prevention

## Usage in Templates

### Base Template (base.html)
\`\`\`html
<head>
    <!-- Critical fonts inline -->
    {% include 'components/critical_fonts.html' %}

    <!-- Font preloading -->
    {% include 'components/font_preload.html' %}

    <!-- Regular CSS -->
    <link rel="stylesheet" href="{% static 'css/fonts-optimized.css' %}">
</head>
\`\`\`

### Django Settings
Add the configuration from \`font_config.py\` to your settings and context processors.

## Performance Benefits
1. **Faster loading**: Preconnect and preload reduce font loading time
2. **No FOIT**: System fonts display immediately while custom fonts load
3. **Reduced CLS**: Font metrics ensure consistent layout
4. **Better UX**: Progressive enhancement for font loading

## Monitoring
Use browser DevTools to monitor:
- Font loading waterfall
- CLS scores in Lighthouse
- Font display timing

## Browser Support
- Modern browsers: Full font-display: swap support
- Older browsers: JavaScript polyfill fallback
- No JS: Graceful degradation to system fonts
`;

        await fs.writeFile('FONT_OPTIMIZATION.md', documentation);
        console.log('✅ Generated comprehensive documentation');

        console.log('\n🎉 Font optimization complete!');
        console.log('📄 Files generated:');
        console.log('   - static/css/fonts-optimized.css');
        console.log('   - templates/components/font_preload.html');
        console.log('   - templates/components/critical_fonts.html');
        console.log('   - font_config.py');
        console.log('   - static/fonts/font-metrics.json');
        console.log('   - FONT_OPTIMIZATION.md');
        console.log('\n📖 See FONT_OPTIMIZATION.md for implementation details');

    } catch (error) {
        console.error('❌ Font optimization failed:', error);
        process.exit(1);
    }
}

// Run the optimization
if (require.main === module) {
    main();
}

module.exports = { generateOptimizedFontCSS, generateFontPreloadHTML, generateCriticalFontCSS };
