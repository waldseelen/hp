/**
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
        const criticalFonts = [
            {
                'family': 'Inter',
                'weights': [
                    400,
                    500,
                    600,
                    700
                ],
                'styles': [
                    'normal'
                ],
                'display': 'swap',
                'source': 'google'
            }
        ];

        for (const font of criticalFonts) {
            for (const weight of font.weights) {
                const fontFace = new FontFace(font.family, 'url(data:,)', {
                    weight: weight.toString(),
                    style: 'normal'
                });

                try {
                    await fontFace.load();
                    if (document.fonts.check(`${weight} 12px ${font.family}`)) {
                        this.fontsLoaded.add(`${font.family}-${weight}`);
                        document.documentElement.classList.add(`font-${font.family.toLowerCase().replace(/\s+/g, '-')}-${weight}-loaded`);
                    }
                } catch (error) {
                    console.warn(`Font check failed for ${font.family}:`, error);
                }
            }
        }
    }

    loadNonCriticalFonts() {
        const nonCriticalFonts = [
            {
                'family': 'JetBrains Mono',
                'weights': [
                    400,
                    500
                ],
                'styles': [
                    'normal'
                ],
                'display': 'optional',
                'source': 'google'
            }
        ];

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
                const fontKey = `${font.family}-${weight}`;

                if (!this.fontsLoaded.has(fontKey)) {
                    try {
                        const fontUrl = this.generateFontURL(font, weight);
                        const fontFace = new FontFace(font.family, `url(${fontUrl})`, {
                            weight: weight.toString(),
                            style: 'normal',
                            display: font.display || 'swap'
                        });

                        await fontFace.load();
                        document.fonts.add(fontFace);
                        this.fontsLoaded.add(fontKey);

                        // Add loaded class for CSS targeting
                        document.documentElement.classList.add(`font-${font.family.toLowerCase().replace(/\s+/g, '-')}-loaded`);

                    } catch (error) {
                        console.warn(`Failed to load font ${font.family} ${weight}:`, error);
                    }
                }
            }
        }
    }

    generateFontURL(font, weight) {
        if (font.source === 'google') {
            const family = font.family.replace(/\s+/g, '+');
            return `https://fonts.gstatic.com/s/${family.toLowerCase()}/normal/${weight}/font.woff2`;
        }
        return '';
    }

    setupFontLoadingEvents() {
    // Listen for font loading events
        document.fonts.addEventListener('loading', event => {
            document.documentElement.classList.add('fonts-loading');
        });

        document.fonts.addEventListener('loadingdone', event => {
            document.documentElement.classList.remove('fonts-loading');
            document.documentElement.classList.add('fonts-loaded');
        });

        document.fonts.addEventListener('loadingerror', event => {
            document.documentElement.classList.add('fonts-error');
            console.warn('Font loading error:', event);
        });
    }
}

// Initialize font loader
if (typeof window !== 'undefined') {
    new FontLoader();
}
