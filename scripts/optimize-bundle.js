/**
 * Bundle Optimization Script
 * Combines, minifies, and optimizes CSS/JS bundles for production
 */

const fs = require('fs');
const path = require('path');

// CSS optimization functions
function minifyCSS(css) {
    return css
    // Remove comments
        .replace(/\/\*[\s\S]*?\*\//g, '')
    // Remove extra whitespace
        .replace(/\s+/g, ' ')
    // Remove whitespace around symbols
        .replace(/\s*([{}:;,>+~])\s*/g, '$1')
    // Remove trailing semicolons
        .replace(/;}/g, '}')
    // Remove empty rules
        .replace(/[^{}]+\{\s*\}/g, '')
        .trim();
}

function combineCSS(files) {
    const combinedCSS = files
        .filter(file => fs.existsSync(file))
        .map(file => {
            const css = fs.readFileSync(file, 'utf8');
            return `/* ${path.basename(file)} */\n${css}\n`;
        })
        .join('\n');

    return combinedCSS;
}

// Main optimization function
async function optimizeBundle() {
    try {
        console.log('🚀 Starting bundle optimization...');

        const staticDir = path.join(__dirname, '..', 'static');
        const cssDir = path.join(staticDir, 'css');
        const optimizedDir = path.join(cssDir, 'optimized');

        // Create optimized directory
        if (!fs.existsSync(optimizedDir)) {
            fs.mkdirSync(optimizedDir, { recursive: true });
        }

        // Define CSS bundles
        const cssBundles = {
            // Critical bundle for above-the-fold content
            'critical.min.css': [
                path.join(cssDir, 'critical', 'base.css'),
            ],

            // Main bundle for core styles
            'main.min.css': [
                path.join(cssDir, 'custom.css'),
                path.join(cssDir, 'components.css'),
                path.join(cssDir, 'accessibility.css'),
            ],

            // Enhanced bundle for additional features
            'enhanced.min.css': [
                path.join(cssDir, 'animations.css'),
                path.join(cssDir, 'component-library.css'),
            ],

            // Tailwind bundle (compiled)
            'tailwind.min.css': [
                path.join(cssDir, 'output.css'),
                path.join(cssDir, 'components-compiled.css'),
            ]
        };

        // Process each bundle
        Object.entries(cssBundles).forEach(([bundleName, files]) => {
            console.log(`📦 Processing bundle: ${bundleName}`);

            // Combine CSS files
            const combinedCSS = combineCSS(files);

            if (combinedCSS.trim()) {
                // Minify combined CSS
                const minifiedCSS = minifyCSS(combinedCSS);

                // Calculate compression ratio
                const originalSize = Buffer.byteLength(combinedCSS, 'utf8');
                const minifiedSize = Buffer.byteLength(minifiedCSS, 'utf8');
                const compressionRatio = ((originalSize - minifiedSize) / originalSize * 100).toFixed(1);

                // Write optimized bundle
                const outputPath = path.join(optimizedDir, bundleName);
                fs.writeFileSync(outputPath, minifiedCSS);

                console.log(`   ✅ ${bundleName}: ${originalSize} → ${minifiedSize} bytes (${compressionRatio}% reduction)`);
            } else {
                console.log(`   ⚠️  ${bundleName}: No content found`);
            }
        });

        // Generate bundle manifest
        const manifest = {
            generated: new Date().toISOString(),
            bundles: Object.keys(cssBundles).reduce((acc, bundleName) => {
                const bundlePath = path.join(optimizedDir, bundleName);
                if (fs.existsSync(bundlePath)) {
                    const stats = fs.statSync(bundlePath);
                    acc[bundleName] = {
                        size: stats.size,
                        path: `static/css/optimized/${bundleName}`,
                        integrity: require('crypto')
                            .createHash('sha384')
                            .update(fs.readFileSync(bundlePath))
                            .digest('base64')
                    };
                }
                return acc;
            }, {}),
            loadingStrategy: {
                critical: ['critical.min.css'],
                deferred: ['main.min.css', 'enhanced.min.css'],
                async: ['tailwind.min.css']
            }
        };

        fs.writeFileSync(
            path.join(optimizedDir, 'manifest.json'),
            JSON.stringify(manifest, null, 2)
        );

        // Generate Django template helper
        const djangoHelper = `
{# Optimized CSS Loading Helper #}
{# Usage: {% include 'partials/optimized-css.html' %} #}

{% load static %}

<!-- Critical CSS - Inline for immediate rendering -->
<style>
/* Critical styles loaded inline for performance */
{{ critical_css|safe }}
</style>

<!-- Main CSS bundle - High priority -->
<link rel="preload"
      href="{% static 'css/optimized/main.min.css' %}"
      as="style"
      onload="this.onload=null;this.rel='stylesheet'">
<noscript>
  <link rel="stylesheet" href="{% static 'css/optimized/main.min.css' %}">
</noscript>

<!-- Enhanced CSS bundle - Load after main content -->
<link rel="preload"
      href="{% static 'css/optimized/enhanced.min.css' %}"
      as="style"
      onload="this.onload=null;this.rel='stylesheet'"
      media="print"
      onload="this.media='all'">

<!-- Tailwind CSS bundle - Lowest priority -->
<script>
  // Load Tailwind CSS asynchronously after page load
  window.addEventListener('load', function() {
    setTimeout(function() {
      var link = document.createElement('link');
      link.rel = 'stylesheet';
      link.href = '{% static "css/optimized/tailwind.min.css" %}';
      document.head.appendChild(link);
    }, 100);
  });
</script>

<!-- Fallback for no-JS users -->
<noscript>
  <link rel="stylesheet" href="{% static 'css/optimized/tailwind.min.css' %}">
</noscript>
`;

        // Create templates directory if it doesn't exist
        const templatesDir = path.join(__dirname, '..', 'templates', 'partials');
        if (!fs.existsSync(templatesDir)) {
            fs.mkdirSync(templatesDir, { recursive: true });
        }

        fs.writeFileSync(
            path.join(templatesDir, 'optimized-css.html'),
            djangoHelper.trim()
        );

        // Generate performance optimization guide
        const performanceGuide = `
# CSS Bundle Optimization Guide

## Bundle Strategy

### 1. Critical CSS (Inline)
- Above-the-fold styles
- Navigation and layout
- Base typography
- **Load:** Inline in <head>

### 2. Main CSS Bundle
- Core component styles
- Accessibility features
- Form styles
- **Load:** High priority with preload

### 3. Enhanced CSS Bundle
- Animations and transitions
- Advanced components
- **Load:** After main content

### 4. Tailwind CSS Bundle
- Utility classes
- Framework styles
- **Load:** Asynchronously after page load

## Implementation

### Django Settings

Add to your base template:
\`\`\`html
{% include 'partials/optimized-css.html' %}
\`\`\`

### Performance Metrics

Monitor these metrics:
- First Contentful Paint (FCP)
- Largest Contentful Paint (LCP)
- Cumulative Layout Shift (CLS)
- Time to Interactive (TTI)

### Build Commands

Development:
\`\`\`bash
npm run dev
\`\`\`

Production:
\`\`\`bash
npm run build:production
\`\`\`

## Best Practices

1. **Critical CSS**: Keep under 14KB for optimal performance
2. **Bundle splitting**: Separate critical from non-critical styles
3. **Loading strategy**: Use preload for important resources
4. **Caching**: Set appropriate cache headers for bundles
5. **Monitoring**: Track bundle sizes and loading times

## Bundle Sizes

Check current bundle sizes in manifest.json
`;

        fs.writeFileSync(
            path.join(optimizedDir, 'PERFORMANCE.md'),
            performanceGuide.trim()
        );

        console.log('\n🎉 Bundle optimization completed!');
        console.log('📊 Optimization summary:');
        console.log(`   📁 Bundles: ${Object.keys(cssBundles).length}`);
        console.log(`   📄 Manifest: static/css/optimized/manifest.json`);
        console.log(`   🎨 Template: templates/partials/optimized-css.html`);
        console.log(`   📋 Guide: static/css/optimized/PERFORMANCE.md`);

        // Calculate total savings
        const totalOriginal = Object.keys(cssBundles).reduce((total, bundleName) => {
            const files = cssBundles[bundleName];
            return total + files.reduce((size, file) => {
                if (fs.existsSync(file)) {
                    return size + fs.statSync(file).size;
                }
                return size;
            }, 0);
        }, 0);

        const totalOptimized = Object.keys(manifest.bundles).reduce((total, bundleName) => total + manifest.bundles[bundleName].size, 0);

        const totalSavings = ((totalOriginal - totalOptimized) / totalOriginal * 100).toFixed(1);
        console.log(`   💾 Total savings: ${totalSavings}% (${totalOriginal} → ${totalOptimized} bytes)`);

    } catch (error) {
        console.error('❌ Bundle optimization failed:', error);
        process.exit(1);
    }
}

// Run if called directly
if (require.main === module) {
    optimizeBundle();
}

module.exports = { optimizeBundle };
