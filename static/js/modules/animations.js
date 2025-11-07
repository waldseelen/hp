/**
 * Advanced Animations & Micro-interactions
 * Handles scroll-triggered animations, page transitions, and interactive effects
 */

class AnimationController {
    constructor() {
        this.isReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        this.observers = new Map();
        this.init();
    }

    init() {
        // Skip animations if user prefers reduced motion
        if (this.isReduced) {
            this.disableAnimations();
            return;
        }

        this.initPageTransitions();
        this.initScrollReveal();
        this.initMicroInteractions();
        this.initPerformanceOptimizations();

        // Initialize when DOM is ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.startAnimations());
        } else {
            this.startAnimations();
        }
    }

    /**
     * Disable all animations for users who prefer reduced motion
     */
    disableAnimations() {
        const style = document.createElement('style');
        style.textContent = `
            *, *::before, *::after {
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
            }
        `;
        document.head.appendChild(style);
    }

    /**
     * Initialize page transition animations
     */
    initPageTransitions() {
        // Add page transition class to main content
        const main = document.querySelector('main') || document.body;
        main.classList.add('page-transition');

        // Trigger page load animation
        window.addEventListener('load', () => {
            setTimeout(() => {
                main.classList.add('loaded');
            }, 100);
        });

        // Handle navigation transitions
        this.initNavigationTransitions();
    }

    /**
     * Initialize navigation transitions for SPA-like experience
     */
    initNavigationTransitions() {
        const links = document.querySelectorAll('a[href^="/"], a[href^="#"]');

        links.forEach(link => {
            // Skip external links and hash-only links
            if (link.hostname !== window.location.hostname ||
                link.getAttribute('href').startsWith('#')) {
                return;
            }

            link.addEventListener('click', e => {
                const main = document.querySelector('main') || document.body;

                // Add transition out effect
                main.style.opacity = '0';
                main.style.transform = 'translateY(-20px)';

                // Allow default navigation after transition
                setTimeout(() => {
                    // Navigation will happen naturally
                }, 200);
            });
        });
    }

    /**
     * Initialize scroll-triggered reveal animations
     */
    initScrollReveal() {
        // Create intersection observer for scroll reveals
        const revealObserver = new IntersectionObserver(
            entries => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('revealed');

                        // Stop observing once revealed
                        revealObserver.unobserve(entry.target);
                    }
                });
            },
            {
                threshold: 0.1,
                rootMargin: '0px 0px -50px 0px'
            }
        );

        // Observe all scroll reveal elements
        const revealElements = document.querySelectorAll([
            '.scroll-reveal',
            '.scroll-reveal-left',
            '.scroll-reveal-right',
            '.scroll-reveal-scale'
        ].join(', '));

        revealElements.forEach(el => {
            revealObserver.observe(el);
        });

        this.observers.set('reveal', revealObserver);
    }

    /**
     * Initialize micro-interactions for enhanced user feedback
     */
    initMicroInteractions() {
        this.initButtonInteractions();
        this.initFormInteractions();
        this.initCardInteractions();
        this.initHoverEffects();
    }

    /**
     * Enhanced button interactions
     */
    initButtonInteractions() {
        const buttons = document.querySelectorAll('button, .btn-primary, .btn-secondary, .btn-tertiary');

        buttons.forEach(button => {
            // Add micro-interaction classes
            button.classList.add('btn-micro', 'click-animation', 'gpu-accelerated');

            // Click feedback
            button.addEventListener('click', e => {
                // Create ripple effect at click position
                this.createRipple(e, button);

                // Haptic feedback on supported devices
                if (navigator.vibrate) {
                    navigator.vibrate(10);
                }
            });

            // Loading state management
            this.initButtonLoadingState(button);
        });
    }

    /**
     * Create ripple effect on button click
     */
    createRipple(event, element) {
        const rect = element.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = event.clientX - rect.left - size / 2;
        const y = event.clientY - rect.top - size / 2;

        const ripple = document.createElement('div');
        ripple.style.cssText = `
            position: absolute;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.3);
            width: ${size}px;
            height: ${size}px;
            left: ${x}px;
            top: ${y}px;
            animation: ripple-animation 0.6s ease-out;
            pointer-events: none;
            z-index: 1000;
        `;

        element.style.position = element.style.position || 'relative';
        element.appendChild(ripple);

        // Remove ripple after animation
        setTimeout(() => {
            if (ripple.parentNode) {
                ripple.parentNode.removeChild(ripple);
            }
        }, 600);
    }

    /**
     * Initialize button loading states
     */
    initButtonLoadingState(button) {
        // Handle form submission buttons
        const form = button.closest('form');
        if (form) {
            form.addEventListener('submit', () => {
                if (button.type === 'submit') {
                    this.setButtonLoading(button, true);
                }
            });
        }
    }

    /**
     * Set button loading state
     */
    setButtonLoading(button, isLoading) {
        if (isLoading) {
            button.classList.add('btn-loading');
            button.disabled = true;

            // Store original content
            button.dataset.originalContent = button.innerHTML;

            // Add spinner
            button.innerHTML = `
                <svg class="btn-spinner" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
                </svg>
                Loading...
            `;
        } else {
            button.classList.remove('btn-loading');
            button.disabled = false;
            button.innerHTML = button.dataset.originalContent || button.innerHTML;
        }
    }

    /**
     * Enhanced form interactions
     */
    initFormInteractions() {
        const inputs = document.querySelectorAll('input, textarea, select');

        inputs.forEach(input => {
            // Add focus animations
            input.classList.add('input-focus-animation', 'gpu-accelerated');

            // Error shake animation
            input.addEventListener('invalid', () => {
                input.classList.add('animate-shake');
                setTimeout(() => {
                    input.classList.remove('animate-shake');
                }, 500);
            });

            // Success feedback
            input.addEventListener('input', () => {
                if (input.validity.valid && input.value) {
                    input.classList.add('input-valid-feedback');
                } else {
                    input.classList.remove('input-valid-feedback');
                }
            });
        });
    }

    /**
     * Enhanced card interactions
     */
    initCardInteractions() {
        const cards = document.querySelectorAll('.card-base, .glass-card');

        cards.forEach(card => {
            // Add hover glow effect to interactive cards
            if (card.classList.contains('card-interactive')) {
                card.classList.add('hover-glow');
            }

            // Parallax effect on mouse move
            this.initCardParallax(card);

            // Stagger animations for card grids
            this.initCardGridAnimations(card);
        });
    }

    /**
     * Add subtle parallax effect to cards
     */
    initCardParallax(card) {
        card.addEventListener('mousemove', e => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;

            const centerX = rect.width / 2;
            const centerY = rect.height / 2;

            const rotateX = (y - centerY) / 20;
            const rotateY = (centerX - x) / 20;

            card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateZ(0)`;
        });

        card.addEventListener('mouseleave', () => {
            card.style.transform = 'perspective(1000px) rotateX(0) rotateY(0) translateZ(0)';
        });
    }

    /**
     * Stagger animations for card grids
     */
    initCardGridAnimations(card) {
        const cardGrid = card.closest('.card-grid');
        if (!cardGrid) { return; }

        const cards = Array.from(cardGrid.children);
        const index = cards.indexOf(card);

        // Add stagger delay
        card.style.animationDelay = `${index * 0.1}s`;
        card.classList.add('animate-fade-in');
    }

    /**
     * Initialize hover effects
     */
    initHoverEffects() {
        // Add floating animation to specific elements
        const floatingElements = document.querySelectorAll('.animate-float');
        floatingElements.forEach(el => {
            el.classList.add('gpu-accelerated');
        });

        // Add pulse animation to call-to-action elements
        const ctaElements = document.querySelectorAll('.btn-primary, .btn-fab');
        ctaElements.forEach(el => {
            el.addEventListener('mouseenter', () => {
                el.classList.add('animate-pulse-soft');
            });

            el.addEventListener('mouseleave', () => {
                el.classList.remove('animate-pulse-soft');
            });
        });
    }

    /**
     * Performance optimizations
     */
    initPerformanceOptimizations() {
        // Add will-change properties to animated elements
        const animatedElements = document.querySelectorAll([
            '.btn-base', '.card-base', '.glass-card',
            '.animate-fade-in', '.animate-slide-up',
            '.scroll-reveal', '.nav-link-modern'
        ].join(', '));

        animatedElements.forEach(el => {
            el.classList.add('gpu-accelerated');

            // Add will-change on interaction
            el.addEventListener('mouseenter', () => {
                el.classList.add('will-change-transform');
            });

            el.addEventListener('mouseleave', () => {
                setTimeout(() => {
                    el.classList.remove('will-change-transform');
                }, 300);
            });
        });
    }

    /**
     * Start all animations
     */
    startAnimations() {
        // Trigger initial animations with stagger
        const elements = document.querySelectorAll('.animate-fade-in, .animate-slide-up');
        elements.forEach((el, index) => {
            setTimeout(() => {
                el.style.opacity = '1';
                el.style.transform = 'translateY(0)';
            }, index * 100);
        });
    }

    /**
     * Cleanup method
     */
    destroy() {
        this.observers.forEach(observer => observer.disconnect());
        this.observers.clear();
    }
}

// Add ripple animation keyframes
const style = document.createElement('style');
style.textContent = `
    @keyframes ripple-animation {
        to {
            transform: scale(2);
            opacity: 0;
        }
    }

    .input-valid-feedback {
        border-color: #059669 !important;
        box-shadow: 0 0 0 3px rgba(5, 150, 105, 0.1) !important;
    }
`;
document.head.appendChild(style);

// Initialize animations when script loads
const animationController = new AnimationController();

// Export for potential external use
window.AnimationController = AnimationController;
window.animationController = animationController;
