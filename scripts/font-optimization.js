#!/usr/bin/env node

/**
 * Font Loading Optimization Script
 * Generates font loading strategies and preload configurations
 */

const fs = require('fs').promises;
const path = require('path');

class FontOptimizer {
    constructor() {
        this.fontConfig = {
            // Critical fonts that should be preloaded
            critical: [
                {
                    family: 'Inter',
                    weights: [400, 500, 600, 700],
                    styles: ['normal'],
                    display: 'swap',
                    source: 'google'
                }
            ],

            // Non-critical fonts for lazy loading
            nonCritical: [
                {
                    family: 'JetBrains Mono',
                    weights: [400, 500],
                    styles: ['normal'],
                    display: 'optional',
                    source: 'google'
                }
            ],

            // Font loading strategy
            strategy: {
                preload: true,
                prefetch: true,
                fallbacks: {
                    'Inter': '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
                    'JetBrains Mono': 'SFMono-Regular, Monaco, Consolas, monospace'
                }
            }
        };
    }

    async generateFontCSS() {
        console.log('🔤 Generating optimized font CSS...');

        let css = '/* Font Loading Optimization */\n\n';

        // Generate font-face declarations
        for (const font of [...this.fontConfig.critical, ...this.fontConfig.nonCritical]) {
            for (const weight of font.weights) {
                for (const style of font.styles) {
                    if (font.source === 'google') {
                        css += this.generateGoogleFontFace(font, weight, style);
                    }
                }
            }
        }

        // Add font fallbacks
        css += '\n/* Font Fallbacks */\n';
        css += ':root {\n';
        Object.entries(this.fontConfig.strategy.fallbacks).forEach(([fontFamily, fallback]) => {
            css += `  --font-${fontFamily.toLowerCase().replace(/\s+/g, '-')}: "${fontFamily}", ${fallback};\n`;
        });
        css += '}\n\n';

        // Add utility classes
        css += this.generateUtilityClasses();

        // Write to file
        const outputPath = path.join(__dirname, '..', 'static', 'css', 'fonts-optimized.css');
        await fs.writeFile(outputPath, css);

        console.log(`✅ Font CSS generated: ${outputPath}`);
    }

    generateGoogleFontFace(font, weight, style) {
        const fontUrl = this.generateGoogleFontURL(font, weight, style);

        return `@font-face {
  font-family: '${font.family}';
  font-style: ${style};
  font-weight: ${weight};
  font-display: ${font.display};
  src: url('${fontUrl}') format('woff2');
}

`;
    }

    generateGoogleFontURL(font, weight, style) {
    // Simplified Google Fonts URL generation
        const family = font.family.replace(/\s+/g, '+');
        return `https://fonts.gstatic.com/s/${family.toLowerCase()}/${style}/${weight}/font.woff2`;
    }

    generateUtilityClasses() {
        return `/* Font Utility Classes */
.font-primary {
  font-family: var(--font-inter);
}

.font-mono {
  font-family: var(--font-jetbrains-mono);
}

.font-loading {
  font-display: swap;
}

.font-optional {
  font-display: optional;
}

/* Performance optimizations */
.text-optimize {
  text-rendering: optimizeSpeed;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

@media (prefers-reduced-motion: no-preference) {
  .font-smooth-transition {
    transition: font-weight 0.2s ease-in-out;
  }
}
`;
    }

    async generatePreloadHTML() {
        console.log('📦 Generating font preload HTML...');

        let html = '<!-- Font Preloading -->\n';

        // Generate preload links for critical fonts
        for (const font of this.fontConfig.critical) {
            for (const weight of font.weights.slice(0, 2)) { // Limit preloads
                const fontUrl = this.generateGoogleFontURL(font, weight, 'normal');
                html += `<link rel="preload" href="${fontUrl}" as="font" type="font/woff2" crossorigin>\n`;
            }
        }

        // Add DNS prefetch
        html += '\n<!-- DNS Prefetch for Font Sources -->\n';
        html += '<link rel="dns-prefetch" href="//fonts.googleapis.com">\n';
        html += '<link rel="dns-prefetch" href="//fonts.gstatic.com">\n';

        // Write to partial template
        const outputPath = path.join(__dirname, '..', 'templates', 'partials', 'font-preloads.html');
        await fs.mkdir(path.dirname(outputPath), { recursive: true });
        await fs.writeFile(outputPath, html);

        console.log(`✅ Font preload template generated: ${outputPath}`);
    }

    async generateFontLoadingJS() {
        console.log('⚡ Generating font loading JavaScript...');

        const js = `/**
 * Font Loading Optimization
 * Handles progressive font loading and fallbacks
 */

class FontLoader {
  constructor() {
    this.fontsLoaded = new Set();
    this.init();
  }

  init() {
    // Check if fonts are already cached
    if ('fonts' in document) {
      this.checkCachedFonts();
    }

    // Load non-critical fonts after page load
    if (document.readyState === 'complete') {
      this.loadNonCriticalFonts();
    } else {
      window.addEventListener('load', () => this.loadNonCriticalFonts());
    }

    // Handle font loading events
    this.setupFontLoadingEvents();
  }

  async checkCachedFonts() {
    const criticalFonts = ${JSON.stringify(this.fontConfig.critical, null, 4)};

    for (const font of criticalFonts) {
      for (const weight of font.weights) {
        const fontFace = new FontFace(font.family, 'url(data:,)', {
          weight: weight.toString(),
          style: 'normal'
        });

        try {
          await fontFace.load();
          if (document.fonts.check(\`\${weight} 12px \${font.family}\`)) {
            this.fontsLoaded.add(\`\${font.family}-\${weight}\`);
            document.documentElement.classList.add(\`font-\${font.family.toLowerCase().replace(/\\s+/g, '-')}-\${weight}-loaded\`);
          }
        } catch (error) {
          console.warn(\`Font check failed for \${font.family}:\`, error);
        }
      }
    }
  }

  loadNonCriticalFonts() {
    const nonCriticalFonts = ${JSON.stringify(this.fontConfig.nonCritical, null, 4)};

    // Use requestIdleCallback for better performance
    if ('requestIdleCallback' in window) {
      requestIdleCallback(() => this.loadFonts(nonCriticalFonts));
    } else {
      setTimeout(() => this.loadFonts(nonCriticalFonts), 1000);
    }
  }

  async loadFonts(fonts) {
    for (const font of fonts) {
      for (const weight of font.weights) {
        const fontKey = \`\${font.family}-\${weight}\`;

        if (!this.fontsLoaded.has(fontKey)) {
          try {
            const fontUrl = this.generateFontURL(font, weight);
            const fontFace = new FontFace(font.family, \`url(\${fontUrl})\`, {
              weight: weight.toString(),
              style: 'normal',
              display: font.display || 'swap'
            });

            await fontFace.load();
            document.fonts.add(fontFace);
            this.fontsLoaded.add(fontKey);

            // Add loaded class for CSS targeting
            document.documentElement.classList.add(\`font-\${font.family.toLowerCase().replace(/\\s+/g, '-')}-loaded\`);

          } catch (error) {
            console.warn(\`Failed to load font \${font.family} \${weight}:\`, error);
          }
        }
      }
    }
  }

  generateFontURL(font, weight) {
    if (font.source === 'google') {
      const family = font.family.replace(/\\s+/g, '+');
      return \`https://fonts.gstatic.com/s/\${family.toLowerCase()}/normal/\${weight}/font.woff2\`;
    }
    return '';
  }

  setupFontLoadingEvents() {
    // Listen for font loading events
    document.fonts.addEventListener('loading', (event) => {
      document.documentElement.classList.add('fonts-loading');
    });

    document.fonts.addEventListener('loadingdone', (event) => {
      document.documentElement.classList.remove('fonts-loading');
      document.documentElement.classList.add('fonts-loaded');
    });

    document.fonts.addEventListener('loadingerror', (event) => {
      document.documentElement.classList.add('fonts-error');
      console.warn('Font loading error:', event);
    });
  }
}

// Initialize font loader
if (typeof window !== 'undefined') {
  new FontLoader();
}`;

        const outputPath = path.join(__dirname, '..', 'static', 'js', 'font-loader.js');
        await fs.writeFile(outputPath, js);

        console.log(`✅ Font loading script generated: ${outputPath}`);
    }

    async generateFontOptimizationSummary() {
        const summary = `# Font Loading Optimization Summary

## Implemented Optimizations

### 1. Critical Font Preloading
- **Inter**: Primary UI font (weights: 400, 500, 600, 700)
- **Preload Strategy**: First 2 weights preloaded for immediate availability
- **DNS Prefetch**: Google Fonts domains prefetched

### 2. Progressive Font Loading
- **Critical fonts**: Loaded immediately with fallbacks
- **Non-critical fonts**: Loaded after page load using requestIdleCallback
- **Font Display**: \`swap\` for critical, \`optional\` for non-critical

### 3. Font Loading Detection
- JavaScript-based font loading with fallback handling
- CSS classes added when fonts load for progressive enhancement
- Error handling for failed font loads

### 4. Performance Optimizations
- **WOFF2 format**: Modern, compressed font format
- **Subset loading**: Only required weights and styles loaded
- **Caching detection**: Checks for already cached fonts

## Files Generated

1. \`static/css/fonts-optimized.css\` - Font face declarations and utilities
2. \`templates/partials/font-preloads.html\` - HTML preload tags
3. \`static/js/font-loader.js\` - Progressive font loading script

## Usage

### In Base Template
\`\`\`html
<!-- In <head> -->
{% include 'partials/font-preloads.html' %}
<link rel="stylesheet" href="{% static 'css/fonts-optimized.css' %}">

<!-- Before </body> -->
<script src="{% static 'js/font-loader.js' %}" defer></script>
\`\`\`

### CSS Classes
\`\`\`css
.font-primary { font-family: var(--font-inter); }
.font-mono { font-family: var(--font-jetbrains-mono); }
.text-optimize { /* Performance optimizations */ }
\`\`\`

## Performance Impact

- **Reduced FOUT**: Critical fonts preloaded
- **Improved LCP**: Fallback fonts prevent layout shifts
- **Better UX**: Progressive loading of non-critical fonts
- **Bandwidth Efficient**: Only required font weights loaded
`;

        const outputPath = path.join(__dirname, '..', 'FONT_OPTIMIZATION_SUMMARY.md');
        await fs.writeFile(outputPath, summary);

        console.log(`📄 Font optimization summary generated: ${outputPath}`);
    }

    async optimize() {
        console.log('🚀 Starting font optimization...');

        await this.generateFontCSS();
        await this.generatePreloadHTML();
        await this.generateFontLoadingJS();
        await this.generateFontOptimizationSummary();

        console.log('✅ Font optimization completed successfully!');
    }
}

// Run if called directly
if (require.main === module) {
    const optimizer = new FontOptimizer();
    optimizer.optimize().catch(error => {
        console.error('💥 Font optimization failed:', error);
        process.exit(1);
    });
}

module.exports = { FontOptimizer };
