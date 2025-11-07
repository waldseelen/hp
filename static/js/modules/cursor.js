/**
 * Custom Cursor Effects Controller
 * Provides enhanced cursor interactions and visual feedback
 */

class CustomCursorController {
    constructor() {
        this.cursor = null;
        this.trails = [];
        this.particles = [];
        this.isTouch = false;
        this.currentState = 'default';
        this.lastPosition = { x: 0, y: 0 };
        this.isMoving = false;
        this.moveTimeout = null;

        this.init();
    }

    init() {
        // Check if device supports hover (not a touch device)
        this.isTouch = !window.matchMedia('(hover: hover) and (pointer: fine)').matches;

        if (this.isTouch) {
            console.log('👆 Touch device detected - custom cursor disabled');
            return;
        }

        // Check for reduced motion preference
        if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
            console.log('⚡ Reduced motion preference detected - simplified cursor');
            this.createSimpleCursor();
            return;
        }

        this.createCursor();
        this.createTrails();
        this.bindEvents();

        console.log('✨ Custom cursor controller initialized');
    }

    createCursor() {
        this.cursor = document.createElement('div');
        this.cursor.className = 'custom-cursor';
        this.cursor.setAttribute('aria-hidden', 'true');
        document.body.appendChild(this.cursor);
    }

    createSimpleCursor() {
        // Create a simpler cursor for reduced motion
        this.cursor = document.createElement('div');
        this.cursor.className = 'custom-cursor';
        this.cursor.style.transition = 'none';
        this.cursor.style.animation = 'none';
        this.cursor.setAttribute('aria-hidden', 'true');
        document.body.appendChild(this.cursor);

        this.bindBasicEvents();
    }

    createTrails() {
        const trailCount = 3;
        for (let i = 0; i < trailCount; i++) {
            const trail = document.createElement('div');
            trail.className = 'custom-cursor-trail';
            trail.style.transitionDelay = `${i * 0.1}s`;
            trail.setAttribute('aria-hidden', 'true');
            document.body.appendChild(trail);
            this.trails.push(trail);
        }
    }

    bindEvents() {
        // Mouse movement
        document.addEventListener('mousemove', this.handleMouseMove.bind(this), { passive: true });

        // Mouse events
        document.addEventListener('mousedown', this.handleMouseDown.bind(this));
        document.addEventListener('mouseup', this.handleMouseUp.bind(this));

        // Hover events for interactive elements
        this.bindInteractiveElements();

        // Text selection events
        document.addEventListener('selectstart', this.handleTextSelect.bind(this));
        document.addEventListener('selectionchange', this.handleSelectionChange.bind(this));

        // Window events
        document.addEventListener('visibilitychange', this.handleVisibilityChange.bind(this));
        window.addEventListener('blur', this.handleWindowBlur.bind(this));
        window.addEventListener('focus', this.handleWindowFocus.bind(this));
    }

    bindBasicEvents() {
        // Simplified events for reduced motion
        document.addEventListener('mousemove', this.handleBasicMouseMove.bind(this), { passive: true });
        document.addEventListener('mousedown', this.handleMouseDown.bind(this));
        document.addEventListener('mouseup', this.handleMouseUp.bind(this));
    }

    bindInteractiveElements() {
        const interactiveSelectors = [
            'a', 'button', 'input', 'textarea', 'select',
            '[role="button"]', '[tabindex]', '.clickable',
            '.btn-primary', '.btn-secondary', '.btn-tertiary',
            '.nav-link-modern', '.card-interactive'
        ].join(', ');

        const elements = document.querySelectorAll(interactiveSelectors);

        elements.forEach(element => {
            element.addEventListener('mouseenter', this.handleElementHover.bind(this));
            element.addEventListener('mouseleave', this.handleElementLeave.bind(this));
        });

        // Text inputs
        const textInputs = document.querySelectorAll('input[type="text"], input[type="email"], input[type="password"], textarea');
        textInputs.forEach(input => {
            input.addEventListener('focus', this.handleTextFocus.bind(this));
            input.addEventListener('blur', this.handleTextBlur.bind(this));
        });

        // Disabled elements
        const disabledElements = document.querySelectorAll('[disabled], .disabled');
        disabledElements.forEach(element => {
            element.addEventListener('mouseenter', this.handleDisabledHover.bind(this));
            element.addEventListener('mouseleave', this.handleElementLeave.bind(this));
        });
    }

    handleMouseMove(e) {
        const x = e.clientX;
        const y = e.clientY;

        this.updateCursorPosition(x, y);
        this.updateTrails(x, y);

        // Create particles on movement
        if (this.isMoving && Math.random() > 0.8) {
            this.createParticle(x, y);
        }

        // Track movement state
        this.isMoving = true;
        clearTimeout(this.moveTimeout);
        this.moveTimeout = setTimeout(() => {
            this.isMoving = false;
        }, 100);

        this.lastPosition = { x, y };
    }

    handleBasicMouseMove(e) {
        if (this.cursor) {
            this.cursor.style.left = `${e.clientX}px`;
            this.cursor.style.top = `${e.clientY}px`;
        }
    }

    updateCursorPosition(x, y) {
        if (this.cursor) {
            requestAnimationFrame(() => {
                this.cursor.style.left = `${x}px`;
                this.cursor.style.top = `${y}px`;
            });
        }
    }

    updateTrails(x, y) {
        this.trails.forEach((trail, index) => {
            requestAnimationFrame(() => {
                trail.style.left = `${x}px`;
                trail.style.top = `${y}px`;
                trail.style.opacity = this.isMoving ? '1' : '0';
            });
        });
    }

    handleMouseDown(e) {
        if (this.cursor) {
            this.cursor.classList.add('click');
            this.createRippleEffect(e.clientX, e.clientY);

            // Haptic feedback if supported
            if (navigator.vibrate) {
                navigator.vibrate(50);
            }
        }
    }

    handleMouseUp() {
        if (this.cursor) {
            setTimeout(() => {
                this.cursor.classList.remove('click');
            }, 300);
        }
    }

    handleElementHover(e) {
        if (this.cursor) {
            this.currentState = 'hover';
            this.cursor.classList.add('hover');
            this.cursor.classList.remove('text', 'disabled');

            // Add special effects for different element types
            if (e.target.matches('a, .btn-primary, .btn-secondary')) {
                this.createHoverEffect(e.clientX, e.clientY);
            }
        }
    }

    handleElementLeave() {
        if (this.cursor) {
            this.currentState = 'default';
            this.cursor.classList.remove('hover', 'text', 'disabled');
        }
    }

    handleTextFocus() {
        if (this.cursor) {
            this.currentState = 'text';
            this.cursor.classList.add('text');
            this.cursor.classList.remove('hover', 'disabled');
        }
    }

    handleTextBlur() {
        if (this.cursor) {
            this.currentState = 'default';
            this.cursor.classList.remove('text');
        }
    }

    handleDisabledHover() {
        if (this.cursor) {
            this.currentState = 'disabled';
            this.cursor.classList.add('disabled');
            this.cursor.classList.remove('hover', 'text');
        }
    }

    handleTextSelect() {
        if (this.cursor && this.currentState !== 'text') {
            this.cursor.classList.add('text');
        }
    }

    handleSelectionChange() {
        if (this.cursor && window.getSelection().toString() === '') {
            this.cursor.classList.remove('text');
        }
    }

    handleVisibilityChange() {
        if (this.cursor) {
            if (document.hidden) {
                this.cursor.style.opacity = '0';
                this.trails.forEach(trail => trail.style.opacity = '0');
            } else {
                this.cursor.style.opacity = '1';
            }
        }
    }

    handleWindowBlur() {
        if (this.cursor) {
            this.cursor.style.opacity = '0.3';
        }
    }

    handleWindowFocus() {
        if (this.cursor) {
            this.cursor.style.opacity = '1';
        }
    }

    createParticle(x, y) {
        const particle = document.createElement('div');
        particle.className = 'cursor-particle';
        particle.style.left = `${x}px`;
        particle.style.top = `${y}px`;
        particle.setAttribute('aria-hidden', 'true');

        // Random offset
        const offsetX = (Math.random() - 0.5) * 20;
        const offsetY = (Math.random() - 0.5) * 20;
        particle.style.transform = `translate(${offsetX}px, ${offsetY}px)`;

        document.body.appendChild(particle);

        // Remove particle after animation
        setTimeout(() => {
            if (particle.parentNode) {
                particle.parentNode.removeChild(particle);
            }
        }, 1000);
    }

    createRippleEffect(x, y) {
        const ripple = document.createElement('div');
        ripple.style.cssText = `
            position: fixed;
            left: ${x}px;
            top: ${y}px;
            width: 20px;
            height: 20px;
            background: rgba(255, 215, 0, 0.3);
            border: 2px solid rgba(255, 215, 0, 0.6);
            border-radius: 50%;
            pointer-events: none;
            z-index: 9996;
            transform: translate(-50%, -50%) scale(0);
            animation: cursor-ripple 0.6s ease-out forwards;
        `;
        ripple.setAttribute('aria-hidden', 'true');

        document.body.appendChild(ripple);

        setTimeout(() => {
            if (ripple.parentNode) {
                ripple.parentNode.removeChild(ripple);
            }
        }, 600);
    }

    createHoverEffect(x, y) {
        // Create subtle glow effect on hover
        const glow = document.createElement('div');
        glow.style.cssText = `
            position: fixed;
            left: ${x}px;
            top: ${y}px;
            width: 60px;
            height: 60px;
            background: radial-gradient(circle, rgba(255, 215, 0, 0.1) 0%, transparent 70%);
            border-radius: 50%;
            pointer-events: none;
            z-index: 9995;
            transform: translate(-50%, -50%);
            animation: cursor-glow 0.8s ease-out forwards;
        `;
        glow.setAttribute('aria-hidden', 'true');

        document.body.appendChild(glow);

        setTimeout(() => {
            if (glow.parentNode) {
                glow.parentNode.removeChild(glow);
            }
        }, 800);
    }

    // Public method to update interactive elements (for dynamic content)
    refreshInteractiveElements() {
        if (!this.isTouch) {
            this.bindInteractiveElements();
        }
    }

    // Public method to temporarily disable cursor
    disable() {
        if (this.cursor) {
            this.cursor.style.display = 'none';
            this.trails.forEach(trail => trail.style.display = 'none');
        }
    }

    // Public method to re-enable cursor
    enable() {
        if (this.cursor && !this.isTouch) {
            this.cursor.style.display = 'block';
            this.trails.forEach(trail => trail.style.display = 'block');
        }
    }

    // Cleanup method
    destroy() {
        if (this.cursor && this.cursor.parentNode) {
            this.cursor.parentNode.removeChild(this.cursor);
        }

        this.trails.forEach(trail => {
            if (trail.parentNode) {
                trail.parentNode.removeChild(trail);
            }
        });

        // Remove event listeners
        document.removeEventListener('mousemove', this.handleMouseMove);
        document.removeEventListener('mousedown', this.handleMouseDown);
        document.removeEventListener('mouseup', this.handleMouseUp);

        console.log('🧹 Custom cursor controller destroyed');
    }
}

// Add necessary CSS animations via JavaScript
const cursorStyles = document.createElement('style');
cursorStyles.textContent = `
    @keyframes cursor-glow {
        0% {
            opacity: 0;
            transform: translate(-50%, -50%) scale(0.5);
        }
        50% {
            opacity: 1;
            transform: translate(-50%, -50%) scale(1);
        }
        100% {
            opacity: 0;
            transform: translate(-50%, -50%) scale(1.2);
        }
    }
`;
document.head.appendChild(cursorStyles);

// Initialize cursor controller when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.customCursor = new CustomCursorController();
});

// Export for module usage if needed
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CustomCursorController;
}
