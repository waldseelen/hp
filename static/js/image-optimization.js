/**
 * Image Optimization and Lazy Loading System
 * Implements:
 * - Intersection Observer based lazy loading
 * - Progressive image loading (LQIP - Low Quality Image Placeholder)
 * - WebP format detection and fallback
 * - Performance monitoring
 */

class ImageOptimizer {
    constructor(options = {}) {
        this.options = {
            rootMargin: '50px 0px',
            threshold: 0.1,
            lazyClass: 'lazy',
            loadedClass: 'loaded',
            errorClass: 'error',
            progressiveClass: 'progressive',
            placeholderClass: 'placeholder',
            ...options
        };

        this.observer = null;
        this.images = [];
        this.loadedCount = 0;
        this.totalCount = 0;

        this.init();
    }

    /**
     * Initialize the image optimizer
     */
    init() {
        if ('IntersectionObserver' in window) {
            this.setupIntersectionObserver();
        } else {
            // Fallback for older browsers
            this.loadAllImages();
        }

        this.setupProgressiveLoading();
        this.detectWebPSupport();

        // Monitor performance
        this.monitorPerformance();
    }

    /**
     * Setup Intersection Observer for lazy loading
     */
    setupIntersectionObserver() {
        this.observer = new IntersectionObserver(entries => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    this.loadImage(entry.target);
                    this.observer.unobserve(entry.target);
                }
            });
        }, {
            rootMargin: this.options.rootMargin,
            threshold: this.options.threshold
        });

        // Find all lazy images
        this.images = document.querySelectorAll(`img.${this.options.lazyClass}`);
        this.totalCount = this.images.length;

        // Start observing
        this.images.forEach(img => {
            this.observer.observe(img);
        });
    }

    /**
     * Load a single image with progressive enhancement
     */
    loadImage(img) {
        const src = img.dataset.src || img.src;
        const srcset = img.dataset.srcset;

        if (!src) { return; }

        // Create new image element for loading
        const imageLoader = new Image();

        imageLoader.onload = () => {
            // Successfully loaded
            img.src = src;
            if (srcset) {
                img.srcset = srcset;
            }

            img.classList.remove(this.options.lazyClass);
            img.classList.add(this.options.loadedClass);

            this.loadedCount++;
            this.onImageLoad(img);
        };

        imageLoader.onerror = () => {
            // Failed to load
            img.classList.add(this.options.errorClass);
            this.onImageError(img);
        };

        // Start loading
        if (srcset) {
            imageLoader.srcset = srcset;
        }
        imageLoader.src = src;
    }

    /**
     * Setup progressive image loading with LQIP
     */
    setupProgressiveLoading() {
        const progressiveImages = document.querySelectorAll(`img.${this.options.progressiveClass}`);

        progressiveImages.forEach(img => {
            const placeholder = img.dataset.placeholder;
            const highRes = img.dataset.src || img.src;

            if (placeholder) {
                // Load low quality placeholder first
                img.src = placeholder;
                img.classList.add(this.options.placeholderClass);

                // Preload high resolution image
                const highResLoader = new Image();
                highResLoader.onload = () => {
                    img.src = highRes;
                    img.classList.remove(this.options.placeholderClass);
                    img.classList.add(this.options.loadedClass);
                };
                highResLoader.src = highRes;
            }
        });
    }

    /**
     * Detect WebP support and update image sources
     */
    detectWebPSupport() {
        const webp = new Image();
        webp.onload = webp.onerror = () => {
            const hasWebPSupport = webp.height === 2;

            if (hasWebPSupport) {
                document.documentElement.classList.add('webp-support');
                this.updateWebPSources();
            } else {
                document.documentElement.classList.add('no-webp-support');
            }
        };

        webp.src = 'data:image/webp;base64,UklGRjoAAABXRUJQVlA4IC4AAACyAgCdASoCAAIALmk0mk0iIiIiIgBoSygABc6WWgAA/veff/0PP8bA//LwYAAA';
    }

    /**
     * Update image sources to use WebP format if supported
     */
    updateWebPSources() {
        const images = document.querySelectorAll('img[data-webp]');
        images.forEach(img => {
            const webpSrc = img.dataset.webp;
            if (webpSrc) {
                img.dataset.src = webpSrc;
            }
        });
    }

    /**
     * Load all images immediately (fallback for old browsers)
     */
    loadAllImages() {
        this.images = document.querySelectorAll(`img.${this.options.lazyClass}`);
        this.totalCount = this.images.length;

        this.images.forEach(img => {
            this.loadImage(img);
        });
    }

    /**
     * Handle successful image load
     */
    onImageLoad(img) {
        // Dispatch custom event
        img.dispatchEvent(new CustomEvent('imageLoaded', {
            detail: {
                src: img.src,
                loadTime: performance.now()
            }
        }));

        // Check if all images are loaded
        if (this.loadedCount >= this.totalCount) {
            this.onAllImagesLoaded();
        }
    }

    /**
     * Handle image load error
     */
    onImageError(img) {
        console.warn('Failed to load image:', img.dataset.src || img.src);

        // Try to use fallback image if available
        const fallback = img.dataset.fallback;
        if (fallback) {
            img.src = fallback;
            img.classList.remove(this.options.errorClass);
            img.classList.add(this.options.loadedClass);
        }
    }

    /**
     * Handle all images loaded
     */
    onAllImagesLoaded() {
        document.dispatchEvent(new CustomEvent('allImagesLoaded', {
            detail: {
                totalImages: this.totalCount,
                loadedImages: this.loadedCount
            }
        }));

        console.log(`Image optimization complete: ${this.loadedCount}/${this.totalCount} images loaded`);
    }

    /**
     * Monitor image loading performance
     */
    monitorPerformance() {
        if ('PerformanceObserver' in window) {
            const perfObserver = new PerformanceObserver(list => {
                list.getEntries().forEach(entry => {
                    if (entry.initiatorType === 'img') {
                        console.log(`Image load performance: ${entry.name} - ${entry.duration.toFixed(2)}ms`);
                    }
                });
            });

            perfObserver.observe({ entryTypes: ['resource'] });
        }
    }

    /**
     * Manually trigger loading of specific image
     */
    loadImageById(imageId) {
        const img = document.getElementById(imageId);
        if (img && img.classList.contains(this.options.lazyClass)) {
            this.loadImage(img);
            if (this.observer) {
                this.observer.unobserve(img);
            }
        }
    }

    /**
     * Cleanup and destroy
     */
    destroy() {
        if (this.observer) {
            this.observer.disconnect();
            this.observer = null;
        }

        this.images = [];
        this.loadedCount = 0;
        this.totalCount = 0;
    }
}

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Initialize image optimizer
    window.imageOptimizer = new ImageOptimizer({
        rootMargin: '100px 0px', // Load images 100px before they enter viewport
        threshold: 0.1,
        lazyClass: 'lazy-load',
        loadedClass: 'lazy-loaded',
        progressiveClass: 'progressive-load'
    });

    // Add fade-in animation for loaded images
    document.addEventListener('imageLoaded', e => {
        const img = e.target;
        img.style.opacity = '0';
        img.style.transition = 'opacity 0.3s ease-in-out';

        requestAnimationFrame(() => {
            img.style.opacity = '1';
        });
    });

    console.log('Image optimization system initialized');
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ImageOptimizer;
}
