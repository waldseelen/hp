/**
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
        if (this.spriteLoaded) { return; }

        try {
            const response = await fetch(`${this.basePath}sprites/icons.svg`);
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
        svg.classList.add('icon', 'icon-sprite', `icon-${size}`);

        if (className) {
            svg.classList.add(...className.split(' '));
        }

        if (ariaLabel) {
            svg.setAttribute('aria-label', ariaLabel);
        } else {
            svg.setAttribute('aria-hidden', 'true');
        }

        const use = document.createElementNS('http://www.w3.org/2000/svg', 'use');
        use.setAttributeNS('http://www.w3.org/1999/xlink', 'href', `${this.basePath}sprites/icons.svg#icon-${name}`);

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
}
