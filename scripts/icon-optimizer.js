#!/usr/bin/env node

/**
 * Icon Optimization Script
 * Creates optimized icon sprites and font-based icon systems
 */

const fs = require('fs').promises;
const path = require('path');

class IconOptimizer {
    constructor() {
        this.config = {
            inputDir: 'static/images/icons',
            outputDir: 'static/icons',
            formats: ['svg', 'sprite', 'font'],
            sizes: [16, 24, 32, 48, 64, 128, 256],
            optimization: {
                removeUselessDefs: true,
                removeEditorsNSData: true,
                removeEmptyAttrs: true,
                removeHiddenElems: true,
                removeEmptyText: true,
                removeEmptyContainers: true,
                cleanupNumericValues: true,
                convertColors: true,
                minifyStyles: true
            }
        };

        this.icons = new Map();
    }

    async init() {
        console.log('🎨 Starting icon optimization...');

        // Ensure directories exist
        await this.ensureDirectories();

        // Scan for icon files
        await this.scanIcons();

        // Generate optimized outputs
        await this.generateSVGSprite();
        await this.generateIconFont();
        await this.generateIconCSS();
        await this.generateIconComponents();

        console.log('✅ Icon optimization completed!');
    }

    async ensureDirectories() {
        const dirs = [
            this.config.outputDir,
            path.join(this.config.outputDir, 'sprites'),
            path.join(this.config.outputDir, 'fonts'),
            path.join(this.config.outputDir, 'optimized')
        ];

        for (const dir of dirs) {
            await fs.mkdir(dir, { recursive: true });
        }
    }

    async scanIcons() {
        console.log('🔍 Scanning for icon files...');

        try {
            await fs.access(this.config.inputDir);
            const files = await fs.readdir(this.config.inputDir);

            for (const file of files) {
                if (path.extname(file).toLowerCase() === '.svg') {
                    const iconName = path.basename(file, '.svg');
                    const iconPath = path.join(this.config.inputDir, file);
                    const content = await fs.readFile(iconPath, 'utf8');

                    this.icons.set(iconName, {
                        name: iconName,
                        path: iconPath,
                        content: content,
                        optimized: this.optimizeSVG(content)
                    });
                }
            }

            console.log(`📦 Found ${this.icons.size} icons to process`);
        } catch (error) {
            console.log('ℹ️  No icons directory found, creating default icons...');
            await this.createDefaultIcons();
        }
    }

    optimizeSVG(content) {
    // Basic SVG optimization
        const optimized = content
        // Remove comments
            .replace(/<!--[\s\S]*?-->/g, '')
        // Remove unnecessary attributes
            .replace(/\s*(xmlns:.*?=".*?")/g, '')
            .replace(/\s*id=".*?"/g, '')
            .replace(/\s*class=".*?"/g, '')
        // Normalize whitespace
            .replace(/\s+/g, ' ')
            .trim();

        return optimized;
    }

    async createDefaultIcons() {
        const defaultIcons = {
            'home': '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/></svg>',
            'search': '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0 0 16 9.5 6.5 6.5 0 1 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/></svg>',
            'menu': '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M3 18h18v-2H3v2zm0-5h18v-2H3v2zm0-7v2h18V6H3z"/></svg>',
            'close': '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>',
            'arrow-up': '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M7.41 15.41L12 10.83l4.59 4.58L18 14l-6-6-6 6z"/></svg>',
            'check': '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>'
        };

        // Ensure icons directory exists
        await fs.mkdir(this.config.inputDir, { recursive: true });

        for (const [name, svg] of Object.entries(defaultIcons)) {
            const iconPath = path.join(this.config.inputDir, `${name}.svg`);
            await fs.writeFile(iconPath, svg);

            this.icons.set(name, {
                name: name,
                path: iconPath,
                content: svg,
                optimized: this.optimizeSVG(svg)
            });
        }

        console.log('✅ Created default icon set');
    }

    async generateSVGSprite() {
        console.log('🎯 Generating SVG sprite...');

        let sprite = '<svg xmlns="http://www.w3.org/2000/svg" style="display: none;">\n';

        for (const [name, icon] of this.icons) {
            // Extract viewBox and paths from optimized SVG
            const viewBoxMatch = icon.optimized.match(/viewBox="([^"]*)"/);
            const contentMatch = icon.optimized.match(/<svg[^>]*>(.*)<\/svg>/s);

            if (viewBoxMatch && contentMatch) {
                sprite += `  <symbol id="icon-${name}" viewBox="${viewBoxMatch[1]}">\n`;
                sprite += `    ${contentMatch[1].trim()}\n`;
                sprite += `  </symbol>\n`;
            }
        }

        sprite += '</svg>';

        const spritePath = path.join(this.config.outputDir, 'sprites', 'icons.svg');
        await fs.writeFile(spritePath, sprite);

        console.log(`✅ SVG sprite generated: ${spritePath}`);
    }

    async generateIconFont() {
        console.log('🔤 Generating icon font CSS...');

        // Create a simple CSS-based icon system using existing SVGs
        let fontCSS = `/* Icon Font System */
.icon {
  display: inline-block;
  width: 1em;
  height: 1em;
  vertical-align: -0.125em;
  fill: currentColor;
}

.icon-sm { width: 0.75em; height: 0.75em; }
.icon-lg { width: 1.25em; height: 1.25em; }
.icon-xl { width: 1.5em; height: 1.5em; }
.icon-2xl { width: 2em; height: 2em; }

/* Icon Classes */
`;

        for (const [name] of this.icons) {
            fontCSS += `.icon-${name}::before {
  content: '';
  background-image: url('/static/icons/optimized/${name}.svg');
  background-size: contain;
  background-repeat: no-repeat;
  background-position: center;
  display: inline-block;
  width: 1em;
  height: 1em;
}

`;
        }

        const fontPath = path.join(this.config.outputDir, 'icons.css');
        await fs.writeFile(fontPath, fontCSS);

        console.log(`✅ Icon font CSS generated: ${fontPath}`);
    }

    async generateIconCSS() {
        console.log('📄 Generating icon utility CSS...');

        const css = `/* Icon Utility Classes */
.icon-sprite {
  display: inline-block;
  width: 1em;
  height: 1em;
  vertical-align: -0.125em;
  fill: currentColor;
}

/* Size variants */
.icon-xs { width: 0.75rem; height: 0.75rem; }
.icon-sm { width: 1rem; height: 1rem; }
.icon-md { width: 1.25rem; height: 1.25rem; }
.icon-lg { width: 1.5rem; height: 1.5rem; }
.icon-xl { width: 2rem; height: 2rem; }
.icon-2xl { width: 2.5rem; height: 2.5rem; }

/* Color variants */
.icon-primary { color: rgb(59 130 246); }
.icon-secondary { color: rgb(107 114 128); }
.icon-success { color: rgb(34 197 94); }
.icon-danger { color: rgb(239 68 68); }
.icon-warning { color: rgb(245 158 11); }

/* Interactive states */
.icon-button {
  padding: 0.5rem;
  border-radius: 0.375rem;
  transition: background-color 0.2s ease-in-out;
  cursor: pointer;
}

.icon-button:hover {
  background-color: rgb(243 244 246);
}

.dark .icon-button:hover {
  background-color: rgb(55 65 81);
}

/* Animation utilities */
.icon-spin {
  animation: icon-spin 1s linear infinite;
}

.icon-pulse {
  animation: icon-pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes icon-spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes icon-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
`;

        const cssPath = path.join(this.config.outputDir, 'icon-utilities.css');
        await fs.writeFile(cssPath, css);

        // Save individual optimized SVGs
        for (const [name, icon] of this.icons) {
            const svgPath = path.join(this.config.outputDir, 'optimized', `${name}.svg`);
            await fs.writeFile(svgPath, icon.optimized);
        }

        console.log(`✅ Icon utilities CSS generated: ${cssPath}`);
    }

    async generateIconComponents() {
        console.log('🧩 Generating icon components...');

        // Generate Django template tags for icons
        const templateTags = `{% comment %}
Icon Template Tags
Usage: {% icon "home" size="md" class="icon-primary" %}
{% endcomment %}

{% load static %}

{% if icon_name %}
<svg class="icon icon-sprite {{ class|default:'' }} icon-{{ size|default:'md' }}" aria-hidden="true">
  <use href="{% static 'icons/sprites/icons.svg' %}#icon-{{ icon_name }}"></use>
</svg>
{% endif %}`;

        const templateTagsPath = path.join(__dirname, '..', 'templates', 'partials', 'icon.html');
        await fs.mkdir(path.dirname(templateTagsPath), { recursive: true });
        await fs.writeFile(templateTagsPath, templateTags);

        // Generate JavaScript icon loader
        const iconLoader = `/**
 * Icon Loader Utility
 * Dynamically load and manage icons
 */

class IconLoader {
  constructor() {
    this.icons = new Map();
    this.spriteLoaded = false;
    this.basePath = '/static/icons/';
  }

  async loadSprite() {
    if (this.spriteLoaded) return;

    try {
      const response = await fetch(this.basePath + 'sprites/icons.svg');
      const svgText = await response.text();

      // Insert sprite into document
      const container = document.createElement('div');
      container.innerHTML = svgText;
      container.style.display = 'none';
      document.body.appendChild(container);

      this.spriteLoaded = true;
      console.log('✅ Icon sprite loaded');
    } catch (error) {
      console.warn('❌ Failed to load icon sprite:', error);
    }
  }

  createIcon(name, options = {}) {
    const {
      size = 'md',
      className = '',
      ariaLabel = null
    } = options;

    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.classList.add('icon', 'icon-sprite', \`icon-\${size}\`);

    if (className) {
      svg.classList.add(...className.split(' '));
    }

    if (ariaLabel) {
      svg.setAttribute('aria-label', ariaLabel);
    } else {
      svg.setAttribute('aria-hidden', 'true');
    }

    const use = document.createElementNS('http://www.w3.org/2000/svg', 'use');
    use.setAttributeNS('http://www.w3.org/1999/xlink', 'href', \`\${this.basePath}sprites/icons.svg#icon-\${name}\`);

    svg.appendChild(use);
    return svg;
  }

  // Initialize icon system
  init() {
    // Load sprite after DOM is ready
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => this.loadSprite());
    } else {
      this.loadSprite();
    }
  }
}

// Global icon loader instance
window.iconLoader = new IconLoader();
window.iconLoader.init();

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
  module.exports = IconLoader;
}`;

        const jsPath = path.join(this.config.outputDir, 'icon-loader.js');
        await fs.writeFile(jsPath, iconLoader);

        console.log(`✅ Icon components generated`);
    }

    async generateOptimizationSummary() {
        const summary = `# Icon Optimization Summary

## Generated Assets

### 1. SVG Sprite System
- **File**: \`static/icons/sprites/icons.svg\`
- **Icons**: ${this.icons.size} optimized icons
- **Usage**: \`<use href="/static/icons/sprites/icons.svg#icon-name">\`

### 2. Icon Utilities
- **CSS**: \`static/icons/icon-utilities.css\`
- **Sizes**: xs, sm, md, lg, xl, 2xl
- **Colors**: primary, secondary, success, danger, warning
- **Animations**: spin, pulse

### 3. Individual Optimized SVGs
- **Directory**: \`static/icons/optimized/\`
- **Format**: Compressed SVG files
- **Usage**: Direct file references

### 4. Icon Components
- **Template**: \`templates/partials/icon.html\`
- **JavaScript**: \`static/icons/icon-loader.js\`
- **Integration**: Django template tags

## Usage Examples

### HTML with Sprite
\`\`\`html
<svg class="icon icon-md icon-primary">
  <use href="/static/icons/sprites/icons.svg#icon-home"></use>
</svg>
\`\`\`

### Django Template
\`\`\`html
{% include 'partials/icon.html' with icon_name='home' size='md' class='icon-primary' %}
\`\`\`

### JavaScript
\`\`\`javascript
const homeIcon = window.iconLoader.createIcon('home', {
  size: 'lg',
  className: 'icon-primary',
  ariaLabel: 'Home'
});
document.body.appendChild(homeIcon);
\`\`\`

## Performance Benefits

- **Reduced HTTP Requests**: Single sprite file
- **Scalable**: Vector-based icons scale perfectly
- **Cacheable**: Static sprite file cached by browser
- **Optimized**: Compressed SVG content
- **Flexible**: CSS-based styling and sizing

## Available Icons
${Array.from(this.icons.keys()).map(name => `- ${name}`).join('\n')}
`;

        const summaryPath = path.join(__dirname, '..', 'ICON_OPTIMIZATION_SUMMARY.md');
        await fs.writeFile(summaryPath, summary);

        console.log(`📄 Icon optimization summary: ${summaryPath}`);
    }

    async optimize() {
        await this.init();
        await this.generateOptimizationSummary();
    }
}

// Run if called directly
if (require.main === module) {
    const optimizer = new IconOptimizer();
    optimizer.optimize().catch(error => {
        console.error('💥 Icon optimization failed:', error);
        process.exit(1);
    });
}

module.exports = { IconOptimizer };
