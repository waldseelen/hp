// Enhanced Scroll Animations with Intersection Observer
(function () {
    'use strict';

    // Configuration
    const config = {
        threshold: 0.1,
        rootMargin: '0px 0px -10% 0px',
        staggerDelay: 100,
        animationDuration: 800
    };

    // Intersection Observer for scroll animations
    function initScrollAnimations() {
        // Check if Intersection Observer is supported
        if (!window.IntersectionObserver) {
            // Fallback: show all elements immediately
            document.querySelectorAll('.scroll-reveal, .scroll-reveal-left, .scroll-reveal-right, .scroll-reveal-scale').forEach(el => {
                el.style.opacity = '1';
                el.style.transform = 'none';
            });
            return;
        }

        const observer = new IntersectionObserver(entries => {
            entries.forEach((entry, index) => {
                if (entry.isIntersecting) {
                    const element = entry.target;

                    // Add stagger delay for multiple elements
                    const staggerIndex = parseInt(element.dataset.stagger, 10) || 0;
                    const delay = staggerIndex * config.staggerDelay;

                    setTimeout(() => {
                        element.classList.add('visible');

                        // Add custom animation class if specified
                        const animationType = element.dataset.animation;
                        if (animationType) {
                            element.classList.add(animationType);
                        }

                        // Dispatch custom event
                        element.dispatchEvent(new CustomEvent('elementRevealed', {
                            detail: { element, delay }
                        }));
                    }, delay);

                    // Stop observing this element
                    observer.unobserve(element);
                }
            });
        }, {
            threshold: config.threshold,
            rootMargin: config.rootMargin
        });

        // Observe all scroll reveal elements
        const scrollElements = document.querySelectorAll(
            '.scroll-reveal, .scroll-reveal-left, .scroll-reveal-right, .scroll-reveal-scale'
        );

        scrollElements.forEach((element, index) => {
            // Set initial state
            element.style.opacity = '0';

            // Add stagger index as data attribute
            if (element.classList.contains(`stagger-${index + 1}`)) {
                element.dataset.stagger = index;
            }

            observer.observe(element);
        });
    }

    // Enhanced hover effects for cards
    function initEnhancedHoverEffects() {
        const cards = document.querySelectorAll('.card-interactive, .hover-glow');

        cards.forEach(card => {
            // Mouse enter effect
            card.addEventListener('mouseenter', function (e) {
                this.style.setProperty('--mouse-x', `${e.clientX - this.offsetLeft}px`);
                this.style.setProperty('--mouse-y', `${e.clientY - this.offsetTop}px`);

                // Add ripple effect
                createRippleEffect(this, e);
            });

            // Mouse move effect for gradient following
            card.addEventListener('mousemove', function (e) {
                const rect = this.getBoundingClientRect();
                const x = ((e.clientX - rect.left) / rect.width) * 100;
                const y = ((e.clientY - rect.top) / rect.height) * 100;

                this.style.setProperty('--mouse-x-percent', `${x}%`);
                this.style.setProperty('--mouse-y-percent', `${y}%`);
            });
        });
    }

    // Create ripple effect
    function createRippleEffect(element, event) {
        const ripple = document.createElement('div');
        const rect = element.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = event.clientX - rect.left - size / 2;
        const y = event.clientY - rect.top - size / 2;

        ripple.style.cssText = `
            position: absolute;
            width: ${size}px;
            height: ${size}px;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(59, 130, 246, 0.3) 0%, transparent 70%);
            left: ${x}px;
            top: ${y}px;
            transform: scale(0);
            animation: ripple 0.6s linear forwards;
            pointer-events: none;
            z-index: 0;
        `;

        // Add ripple animation keyframes if not exists
        if (!document.querySelector('#ripple-styles')) {
            const style = document.createElement('style');
            style.id = 'ripple-styles';
            style.textContent = `
                @keyframes ripple {
                    to {
                        transform: scale(2);
                        opacity: 0;
                    }
                }
            `;
            document.head.appendChild(style);
        }

        element.style.position = 'relative';
        element.style.overflow = 'hidden';
        element.appendChild(ripple);

        // Remove ripple after animation
        setTimeout(() => {
            if (ripple.parentNode) {
                ripple.parentNode.removeChild(ripple);
            }
        }, 600);
    }

    // Smooth scroll for anchor links
    function initSmoothScroll() {
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                const targetId = this.getAttribute('href').substring(1);
                const targetElement = document.getElementById(targetId);

                if (targetElement) {
                    e.preventDefault();

                    targetElement.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });

                    // Update URL without scrolling
                    history.pushState(null, null, `#${targetId}`);
                }
            });
        });
    }

    // Parallax scroll effect for background elements
    function initParallaxEffect() {
        const parallaxElements = document.querySelectorAll('.scroll-parallax');

        if (parallaxElements.length === 0) { return; }

        let ticking = false;

        function updateParallax() {
            const scrollY = window.pageYOffset;

            parallaxElements.forEach(element => {
                const speed = parseFloat(element.dataset.speed) || 0.5;
                const yPos = -(scrollY * speed);
                element.style.transform = `translateY(${yPos}px)`;
            });

            ticking = false;
        }

        function requestTick() {
            if (!ticking) {
                requestAnimationFrame(updateParallax);
                ticking = true;
            }
        }

        // Throttled scroll listener
        window.addEventListener('scroll', requestTick, { passive: true });
    }

    // Loading state animations
    function initLoadingAnimations() {
        // Simulate loading for skeleton elements
        const skeletonElements = document.querySelectorAll('.skeleton, .skeleton-dark');

        skeletonElements.forEach((element, index) => {
            setTimeout(() => {
                element.classList.add('loaded');
                element.style.animation = 'none';
            }, 1000 + (index * 200));
        });
    }

    // Performance optimization: Use ResizeObserver for responsive animations
    function initResponsiveAnimations() {
        if (!window.ResizeObserver) { return; }

        const resizeObserver = new ResizeObserver(entries => {
            entries.forEach(entry => {
                const element = entry.target;
                const { width } = entry.contentRect;

                // Adjust animation timing based on screen size
                if (width < 768) {
                    element.style.setProperty('--animation-duration', '0.4s');
                } else {
                    element.style.setProperty('--animation-duration', '0.6s');
                }
            });
        });

        // Observe the body element
        resizeObserver.observe(document.body);
    }

    // Initialize all enhancements
    function init() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', init);
            return;
        }

        try {
            initScrollAnimations();
            initEnhancedHoverEffects();
            initSmoothScroll();
            initParallaxEffect();
            initLoadingAnimations();
            initResponsiveAnimations();

            // Dispatch initialization complete event
            document.dispatchEvent(new CustomEvent('scrollAnimationsReady'));

            console.log('✨ Enhanced scroll animations initialized');
        } catch (error) {
            console.warn('Error initializing scroll animations:', error);
        }
    }

    // Reduced motion support
    function respectsReducedMotion() {
        return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    }

    if (respectsReducedMotion()) {
        // Disable animations for users who prefer reduced motion
        document.documentElement.style.setProperty('--animation-duration', '0s');
        document.documentElement.style.setProperty('--transition-duration', '0s');
    }

    // Initialize
    init();

    // Export functions for external use
    window.ScrollAnimations = {
        init,
        initScrollAnimations,
        initEnhancedHoverEffects,
        createRippleEffect
    };
})();
