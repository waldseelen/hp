// Main JavaScript for Portfolio Site
/* eslint-disable brace-style, no-unused-vars, radix */

document.addEventListener('DOMContentLoaded', function () {
    // Initialize main functionality
    initSmoothScrolling();
    initFormValidation();
    initLoadingStates();
    initMobileMenu();
    initPerformanceOptimizations();
});

// Dark Mode Toggle Functionality
function initDarkMode() {
    const darkModeToggle = document.querySelector('[data-dark-mode-toggle]');
    const body = document.body;
    const html = document.documentElement;

    // Load saved theme or default to dark
    const savedTheme = localStorage.getItem('darkMode');
    const isDark = savedTheme ? JSON.parse(savedTheme) : true;

    if (isDark) {
        html.classList.add('dark');
    } else {
        html.classList.remove('dark');
        body.classList.remove('bg-gray-900');
        body.classList.add('bg-white', 'text-gray-900');
    }

    // Update Alpine.js state if available
    if (window.Alpine) {
        Alpine.store('darkMode', isDark);
    }
}

// Smooth Scrolling for Anchor Links
function initSmoothScrolling() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// Form Validation Enhancement
function initFormValidation() {
    const forms = document.querySelectorAll('form[data-validate]');

    forms.forEach(form => {
        const inputs = form.querySelectorAll('input, textarea, select');
        const submitBtn = form.querySelector('[type="submit"]');

        inputs.forEach(input => {
            input.addEventListener('blur', () => validateField(input));
            input.addEventListener('input', () => clearFieldError(input));
        });

        form.addEventListener('submit', function (e) {
            e.preventDefault();

            let isValid = true;
            inputs.forEach(input => {
                if (!validateField(input)) {
                    isValid = false;
                }
            });

            if (isValid) {
                showLoadingState(submitBtn);
                // Allow form to submit
                this.submit();
            }
        });
    });
}

function validateField(field) {
    const value = field.value.trim();
    const type = field.type;
    const required = field.hasAttribute('required');
    let isValid = true;
    let errorMessage = '';

    // Clear previous errors
    clearFieldError(field);

    // Required field validation
    if (required && !value) {
        isValid = false;
        errorMessage = 'This field is required';
    }

    // Email validation
    else if (type === 'email' && value) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(value)) {
            isValid = false;
            errorMessage = 'Please enter a valid email address';
        }
    }

    // Minimum length validation
    else if (field.hasAttribute('minlength')) {
        const minLength = parseInt(field.getAttribute('minlength'));
        if (value.length < minLength) {
            isValid = false;
            errorMessage = `Minimum ${minLength} characters required`;
        }
    }

    // Show error if validation failed
    if (!isValid) {
        showFieldError(field, errorMessage);
        field.classList.add('border-red-500', 'focus:border-red-500', 'focus:ring-red-500');
        field.classList.remove('border-gray-600', 'focus:border-primary-400');
    } else {
        field.classList.remove('border-red-500', 'focus:border-red-500', 'focus:ring-red-500');
        field.classList.add('border-green-500', 'focus:border-primary-400');
        setTimeout(() => {
            field.classList.remove('border-green-500');
            field.classList.add('border-gray-600');
        }, 2000);
    }

    return isValid;
}

function showFieldError(field, message) {
    const existingError = field.parentElement.querySelector('.form-error');
    if (!existingError) {
        const errorElement = document.createElement('div');
        errorElement.className = 'form-error text-red-400 text-sm mt-1';
        errorElement.textContent = message;
        field.parentElement.appendChild(errorElement);
    }
}

function clearFieldError(field) {
    const error = field.parentElement.querySelector('.form-error');
    if (error) {
        error.remove();
    }
}

// Loading States for Buttons
function initLoadingStates() {
    const loadingButtons = document.querySelectorAll('[data-loading]');

    loadingButtons.forEach(button => {
        button.addEventListener('click', function () {
            if (!this.classList.contains('btn-loading')) {
                showLoadingState(this);
            }
        });
    });
}

function showLoadingState(button) {
    if (!button || button.classList.contains('btn-loading')) { return; }

    const originalHtml = button.innerHTML;
    const loadingText = button.getAttribute('data-loading') || 'Loading...';

    button.classList.add('btn-loading');
    button.disabled = true;
    button.setAttribute('aria-disabled', 'true');
    button.setAttribute('aria-busy', 'true');
    button.setAttribute('aria-live', 'polite');

    button.innerHTML = `
        <svg class="btn-spinner loading-spinner loading-spinner-sm mr-2" viewBox="0 0 24 24" aria-hidden="true">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none" class="opacity-25"></circle>
            <path fill="currentColor" class="opacity-75" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <span class="loading-text">${loadingText}</span>
    `;

    button.setAttribute('data-original-html', originalHtml);
}

function hideLoadingState(button) {
    if (!button) { return; }

    const originalHtml = button.getAttribute('data-original-html');

    button.classList.remove('btn-loading');
    button.disabled = false;
    button.removeAttribute('aria-disabled');
    button.removeAttribute('aria-busy');
    button.removeAttribute('aria-live');

    if (originalHtml !== null) {
        button.innerHTML = originalHtml;
    }

    button.removeAttribute('data-original-html');
}

// Mobile Menu Enhancements
function initMobileMenu() {
    const mobileMenuButtons = document.querySelectorAll('[data-mobile-menu]');

    mobileMenuButtons.forEach(button => {
        button.addEventListener('click', function () {
            const menu = document.querySelector(this.getAttribute('data-mobile-menu'));
            if (menu) {
                menu.classList.toggle('hidden');

                // Update ARIA attributes
                const expanded = !menu.classList.contains('hidden');
                this.setAttribute('aria-expanded', expanded);
            }
        });
    });

    // Close mobile menu when clicking outside
    document.addEventListener('click', function (e) {
        const mobileMenus = document.querySelectorAll('[data-mobile-menu-content]');
        const menuButtons = document.querySelectorAll('[data-mobile-menu]');

        mobileMenus.forEach(menu => {
            if (!menu.contains(e.target) && !Array.from(menuButtons).some(btn => btn.contains(e.target))) {
                menu.classList.add('hidden');
                menuButtons.forEach(btn => btn.setAttribute('aria-expanded', 'false'));
            }
        });
    });
}

// Performance Optimizations
function initPerformanceOptimizations() {
    // Optimize animations for reduced motion preference
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        document.documentElement.style.setProperty('--animation-duration', '0.01ms');
        document.querySelectorAll('.starfield').forEach(el => {
            el.style.animation = 'none';
        });
    }

    // Debounce scroll events
    let scrollTimeout;
    window.addEventListener('scroll', function () {
        if (scrollTimeout) {
            clearTimeout(scrollTimeout);
        }
        scrollTimeout = setTimeout(handleScroll, 10);
    });
}

function handleScroll() {
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    const navbar = document.querySelector('nav');

    // Add/remove navbar background on scroll
    if (navbar) {
        if (scrollTop > 100) {
            navbar.classList.add('bg-gray-900/95');
            navbar.classList.remove('bg-gray-900/90');
        } else {
            navbar.classList.remove('bg-gray-900/95');
            navbar.classList.add('bg-gray-900/90');
        }
    }

    // Update scroll progress indicator
    const progressBar = document.querySelector('[data-scroll-progress]');
    if (progressBar) {
        const documentHeight = document.documentElement.scrollHeight - window.innerHeight;
        const scrollProgress = (scrollTop / documentHeight) * 100;
        progressBar.style.width = `${scrollProgress}%`;
    }
}

// Utility Functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function throttle(func, limit) {
    let inThrottle;
    return function () {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// External link handling
document.addEventListener('click', function (e) {
    const link = e.target.closest('a[href^="http"]');
    if (link && !link.hasAttribute('target')) {
        link.setAttribute('target', '_blank');
        link.setAttribute('rel', 'noopener noreferrer');
    }
});

// Show loading for external links
document.querySelectorAll('a[href^="http"]').forEach(link => {
    link.addEventListener('click', function () {
        const icon = this.querySelector('.external-link-icon');
        if (icon) {
            icon.classList.add('animate-spin');
            setTimeout(() => {
                icon.classList.remove('animate-spin');
            }, 1000);
        }
    });
});

// Initialize tooltips (simple implementation)
function initTooltips() {
    const tooltipElements = document.querySelectorAll('[data-tooltip]');

    tooltipElements.forEach(element => {
        element.addEventListener('mouseenter', showTooltip);
        element.addEventListener('mouseleave', hideTooltip);
    });
}

function showTooltip(e) {
    const text = e.target.getAttribute('data-tooltip');
    const tooltip = document.createElement('div');
    tooltip.className = 'absolute z-50 px-2 py-1 text-sm bg-gray-800 text-white rounded shadow-lg pointer-events-none';
    tooltip.textContent = text;
    tooltip.id = 'tooltip';

    document.body.appendChild(tooltip);

    const rect = e.target.getBoundingClientRect();
    tooltip.style.left = `${rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2)}px`;
    tooltip.style.top = `${rect.top - tooltip.offsetHeight - 5}px`;
}

function hideTooltip() {
    const tooltip = document.getElementById('tooltip');
    if (tooltip) {
        tooltip.remove();
    }
}

// Initialize tooltips after DOM load
document.addEventListener('DOMContentLoaded', initTooltips);

// Error handling for failed resource loads
window.addEventListener('error', function (e) {
    if (e.target.tagName === 'IMG') {
        e.target.src = '/static/images/placeholder.png';
        e.target.alt = 'Image not available';
    }
});
