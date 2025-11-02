/**
 * Parallax Effect Controller
 * Handles scroll-based parallax movement for enhanced visual depth
 */

class ParallaxController {
    constructor() {
        this.parallaxElements = [];
        this.rafId = null;
        this.isScrolling = false;
        this.lastScrollY = window.scrollY;

        this.init();
    }

    init() {
        // Find all parallax elements
        this.parallaxElements = document.querySelectorAll('.scroll-parallax');

        if (this.parallaxElements.length === 0) {
            return;
        }

        // Check for reduced motion preference
        if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
            return;
        }

        // Bind scroll events
        this.bindEvents();

        // Initial parallax calculation
        this.updateParallax();

        console.log(`✨ Parallax controller initialized with ${this.parallaxElements.length} elements`);
    }

    bindEvents() {
        // Optimized scroll handler with requestAnimationFrame
        window.addEventListener('scroll', this.handleScroll.bind(this), { passive: true });

        // Handle resize events
        window.addEventListener('resize', this.handleResize.bind(this), { passive: true });

        // Handle visibility change for performance
        document.addEventListener('visibilitychange', this.handleVisibilityChange.bind(this));
    }

    handleScroll() {
        if (!this.isScrolling) {
            this.isScrolling = true;
            this.rafId = requestAnimationFrame(this.updateParallax.bind(this));
        }
    }

    handleResize() {
        // Debounce resize updates
        clearTimeout(this.resizeTimeout);
        this.resizeTimeout = setTimeout(() => {
            this.updateParallax();
        }, 100);
    }

    handleVisibilityChange() {
        if (document.hidden) {
            // Pause animations when tab is not visible
            if (this.rafId) {
                cancelAnimationFrame(this.rafId);
                this.rafId = null;
            }
        } else {
            // Resume when tab becomes visible
            this.updateParallax();
        }
    }

    updateParallax() {
        const scrollY = window.scrollY;
        const windowHeight = window.innerHeight;
        const documentHeight = document.documentElement.scrollHeight;

        // Calculate scroll progress (0 to 1)
        const scrollProgress = scrollY / (documentHeight - windowHeight);

        this.parallaxElements.forEach((element, index) => {
            // Get parallax speed from data attribute (default: 0.5)
            const speed = parseFloat(element.dataset.speed) || 0.5;

            // Get element position relative to viewport
            const rect = element.getBoundingClientRect();
            const elementTop = rect.top + scrollY;
            const elementHeight = rect.height;

            // Check if element is in viewport (with buffer)
            const buffer = windowHeight * 0.5;
            const isInView = (
                scrollY + windowHeight + buffer > elementTop &&
                scrollY - buffer < elementTop + elementHeight
            );

            if (isInView) {
                // Calculate parallax offset based on scroll position and speed
                const yPos = (scrollY - elementTop) * speed;

                // Apply different parallax calculations based on element type
                if (element.classList.contains('parallax-layer-back')) {
                    // Furthest layer moves slower and with slight rotation
                    const rotation = scrollProgress * 2;
                    const scale = 1 + (scrollProgress * 0.1);
                    element.style.transform = `translateZ(-300px) scale(${1.3 * scale}) translate3d(0, ${yPos}px, 0) rotate(${rotation}deg)`;
                } else if (element.classList.contains('parallax-layer-base')) {
                    // Base layer with moderate movement
                    const scale = 1 + (scrollProgress * 0.05);
                    element.style.transform = `translateZ(-100px) scale(${1.1 * scale}) translate3d(0, ${yPos}px, 0)`;
                } else if (element.classList.contains('parallax-layer-mid')) {
                    // Mid layer with subtle movement
                    element.style.transform = `translateZ(-50px) scale(1.05) translate3d(0, ${yPos}px, 0)`;
                } else if (element.classList.contains('parallax-layer-front')) {
                    // Front layer with minimal movement
                    element.style.transform = `translateZ(0px) scale(1) translate3d(0, ${yPos * 0.3}px, 0)`;
                } else {
                    // Default parallax movement
                    element.style.transform = `translate3d(0, ${yPos}px, 0)`;
                }

                // Add subtle opacity changes based on scroll position
                const opacityFactor = 1 - (Math.abs(yPos) / (windowHeight * 2));
                const opacity = Math.max(0.3, Math.min(1, opacityFactor));
                element.style.opacity = opacity;
            }
        });

        // Update scroll position
        this.lastScrollY = scrollY;
        this.isScrolling = false;
    }

    // Public method to add new parallax elements dynamically
    addElement(element, speed = 0.5) {
        if (element && !element.classList.contains('scroll-parallax')) {
            element.classList.add('scroll-parallax');
            element.dataset.speed = speed;
            this.parallaxElements.push(element);
        }
    }

    // Public method to remove parallax effects
    removeElement(element) {
        const index = Array.from(this.parallaxElements).indexOf(element);
        if (index > -1) {
            element.classList.remove('scroll-parallax');
            element.style.transform = '';
            element.style.opacity = '';
            this.parallaxElements.splice(index, 1);
        }
    }

    // Cleanup method
    destroy() {
        if (this.rafId) {
            cancelAnimationFrame(this.rafId);
        }

        window.removeEventListener('scroll', this.handleScroll);
        window.removeEventListener('resize', this.handleResize);
        document.removeEventListener('visibilitychange', this.handleVisibilityChange);

        // Reset all elements
        this.parallaxElements.forEach(element => {
            element.style.transform = '';
            element.style.opacity = '';
        });

        this.parallaxElements = [];
        console.log('🧹 Parallax controller destroyed');
    }
}

// Initialize parallax controller when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Check if parallax elements exist before initializing
    if (document.querySelector('.scroll-parallax')) {
        window.parallaxController = new ParallaxController();
    }
});

// Export for module usage if needed
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ParallaxController;
}
