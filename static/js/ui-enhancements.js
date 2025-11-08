/**
 * UI Enhancements Module
 * Advanced user interface enhancements for improved user experience
 */

class UIEnhancements {
    constructor() {
        this.init();
        this.setupEventListeners();
        this.initializeComponents();
    }

    init() {
        // Initialize UI enhancement systems
        this.toastManager = new ToastManager();
        this.modalManager = new ModalManager();
        this.scrollManager = new ScrollManager();
        this.loadingManager = new LoadingManager();
        this.searchManager = new SearchManager();
        this.animationManager = new AnimationManager();
        this.keyboardManager = new KeyboardManager();
        this.themeManager = new ThemeManager();
    }

    setupEventListeners() {
        // DOM content loaded
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.onDOMReady());
        } else {
            this.onDOMReady();
        }

        // Window events
        window.addEventListener('load', () => this.onWindowLoad());
        window.addEventListener('resize', () => this.onWindowResize());
        window.addEventListener('scroll', this.throttle(this.onWindowScroll, 16), { passive: true });

        // Page visibility
        document.addEventListener('visibilitychange', () => this.onVisibilityChange());

        // Network status
        window.addEventListener('online', () => this.onNetworkChange(true));
        window.addEventListener('offline', () => this.onNetworkChange(false));
    }

    initializeComponents() {
        // Initialize all UI components
        this.setupBackToTop();
        this.setupScrollProgress();
        this.setupImageLazyLoading();
        this.setupFormEnhancements();
        this.setupCardInteractions();
        this.setupNavigationEnhancements();
        this.setupAccessibilityFeatures();
    }

    onDOMReady() {
        console.log('UI Enhancements: DOM Ready');
        this.animationManager.initializeScrollAnimations();
        this.loadingManager.hideInitialLoader();
    }

    onWindowLoad() {
        console.log('UI Enhancements: Window Loaded');
        this.animationManager.triggerDelayedAnimations();
    }

    onWindowResize() {
        this.scrollManager.updateScrollProgress();
    }

    onWindowScroll = () => {
        if (!this.scrollAnimationFrame) {
            this.scrollAnimationFrame = requestAnimationFrame(() => {
                this.scrollManager.handleScroll();
                this.animationManager.handleScrollAnimations();
                this.scrollAnimationFrame = null;
            });
        }
    };

    onVisibilityChange() {
        if (document.hidden) {
            this.pauseAnimations();
        } else {
            this.resumeAnimations();
        }
    }

    onNetworkChange(isOnline) {
        const message = isOnline ? 'Connection restored' : 'Connection lost';
        const type = isOnline ? 'success' : 'warning';
        this.toastManager.show(message, type);
    }

    setupBackToTop() {
        const backToTopBtn = document.getElementById('back-to-top');
        if (!backToTopBtn) { return; }

        backToTopBtn.addEventListener('click', e => {
            e.preventDefault();
            this.scrollManager.scrollToTop();
        });
    }

    setupScrollProgress() {
        const progressBar = document.getElementById('scroll-progress');
        if (progressBar) {
            this.scrollManager.setProgressBar(progressBar);
        }
    }

    setupImageLazyLoading() {
        // Skip image lazy loading if already handled by performance.js
        if (window.__imgLazyOwner && window.__imgLazyOwner !== 'ui-enhancements') {
            return;
        }

        // Set owner if not already set
        if (!window.__imgLazyOwner) {
            window.__imgLazyOwner = 'ui-enhancements';
        }

        const images = document.querySelectorAll('img[data-src]');
        if ('IntersectionObserver' in window) {
            const observerOptions = {
                root: null,
                rootMargin: '50px',
                threshold: 0.1
            };

            const imageObserver = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;

                        // Add error handling for failed image loads
                        img.addEventListener('error', () => {
                            img.classList.remove('loading');
                            img.classList.add('load-error');

                            // Try fallback image if available
                            if (img.dataset.fallback) {
                                img.src = img.dataset.fallback;
                            } else {
                                // Use placeholder or hide image
                                img.style.display = 'none';
                                console.warn('Image failed to load:', img.dataset.src);
                            }
                        });

                        img.addEventListener('load', () => {
                            img.classList.remove('loading');
                            img.classList.add('loaded');
                        });

                        img.src = img.dataset.src;
                        observer.unobserve(img);
                    }
                });
            }, observerOptions);

            images.forEach(img => {
                img.classList.add('loading');
                imageObserver.observe(img);
            });
        }
    }

    setupFormEnhancements() {
        // Real-time form validation
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            this.enhanceForm(form);
        });
    }

    enhanceForm(form) {
        const inputs = form.querySelectorAll('input, textarea, select');

        inputs.forEach(input => {
            // Add floating label effect
            this.addFloatingLabel(input);

            // Add validation feedback
            input.addEventListener('blur', () => this.validateInput(input));
            input.addEventListener('input', () => this.clearValidationErrors(input));
        });

        form.addEventListener('submit', e => this.handleFormSubmit(e, form));
    }

    addFloatingLabel(input) {
        const container = input.closest('.form-group');
        if (!container) { return; }

        const label = container.querySelector('label');
        if (!label) { return; }

        input.addEventListener('focus', () => label.classList.add('focused'));
        input.addEventListener('blur', () => {
            if (!input.value) {
                label.classList.remove('focused');
            }
        });

        // Initial state
        if (input.value) {
            label.classList.add('focused');
        }
    }

    validateInput(input) {
        const isValid = input.checkValidity();
        const container = input.closest('.form-group');

        if (container) {
            container.classList.toggle('has-error', !isValid);
            container.classList.toggle('has-success', isValid && input.value);
        }

        return isValid;
    }

    clearValidationErrors(input) {
        const container = input.closest('.form-group');
        if (container) {
            container.classList.remove('has-error');
        }
    }

    handleFormSubmit(e, form) {
        const inputs = form.querySelectorAll('input[required], textarea[required], select[required]');
        let isFormValid = true;

        inputs.forEach(input => {
            if (!this.validateInput(input)) {
                isFormValid = false;
            }
        });

        if (!isFormValid) {
            e.preventDefault();
            this.toastManager.show('Please fill in all required fields', 'error');
            return;
        }

        // Show loading state
        const submitBtn = form.querySelector('[type="submit"]');
        if (submitBtn) {
            submitBtn.classList.add('btn-loading');
            submitBtn.disabled = true;
        }
    }

    setupCardInteractions() {
        const cards = document.querySelectorAll('.card-interactive');

        cards.forEach(card => {
            // Mouse move effect for cards
            card.addEventListener('mousemove', e => {
                const { clientX, clientY } = e;
                const { left, top } = card.getBoundingClientRect();
                const x = clientX - left;
                const y = clientY - top;

                card.style.setProperty('--mouse-x', `${x}px`);
                card.style.setProperty('--mouse-y', `${y}px`);
            });

            // Click ripple effect
            card.addEventListener('click', e => {
                this.createRippleEffect(e, card);
            });
        });
    }

    createRippleEffect(e, element) {
        const ripple = document.createElement('span');
        const { width, height, left, top } = element.getBoundingClientRect();
        const size = Math.max(width, height);
        const { clientX, clientY } = e;
        const x = clientX - left - size / 2;
        const y = clientY - top - size / 2;

        ripple.style.cssText = `
            width: ${size}px;
            height: ${size}px;
            left: ${x}px;
            top: ${y}px;
            position: absolute;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.1);
            transform: scale(0);
            animation: ripple 0.6s linear;
            pointer-events: none;
            z-index: 1;
        `;

        element.style.position = 'relative';
        element.style.overflow = 'hidden';
        element.appendChild(ripple);

        // Add ripple animation
        const style = document.createElement('style');
        style.textContent = `
            @keyframes ripple {
                to {
                    transform: scale(2);
                    opacity: 0;
                }
            }
        `;
        document.head.appendChild(style);

        setTimeout(() => {
            ripple.remove();
            if (element.querySelectorAll('span').length === 0) {
                style.remove();
            }
        }, 600);
    }

    setupNavigationEnhancements() {
        // Smooth scroll for anchor links
        document.addEventListener('click', e => {
            const link = e.target.closest('a[href^="#"]');
            if (link && link.getAttribute('href') !== '#') {
                e.preventDefault();
                const target = document.querySelector(link.getAttribute('href'));
                if (target) {
                    this.scrollManager.scrollToElement(target);
                }
            }
        });

        // Active navigation highlighting
        this.highlightActiveNavigation();
    }

    highlightActiveNavigation() {
        const navLinks = document.querySelectorAll('.nav-link');
        const currentPath = window.location.pathname;

        navLinks.forEach(link => {
            if (link.getAttribute('href') === currentPath) {
                link.classList.add('active');
            }
        });
    }

    setupAccessibilityFeatures() {
        // Focus management
        document.addEventListener('keydown', e => {
            if (e.key === 'Tab') {
                document.body.classList.add('keyboard-navigation');
            }
        });

        document.addEventListener('mousedown', () => {
            document.body.classList.remove('keyboard-navigation');
        });

        // Skip links
        const skipLinks = document.querySelectorAll('.skip-link');
        skipLinks.forEach(link => {
            link.addEventListener('click', e => {
                e.preventDefault();
                const target = document.querySelector(link.getAttribute('href'));
                if (target) {
                    target.focus();
                    target.scrollIntoView({ behavior: 'smooth' });
                }
            });
        });
    }

    pauseAnimations() {
        document.body.classList.add('animations-paused');
    }

    resumeAnimations() {
        document.body.classList.remove('animations-paused');
    }
}

// Toast Manager Class
class ToastManager {
    constructor() {
        this.container = document.getElementById('toast-container');
        this.toasts = new Map();
        this.defaultDuration = 5000;
    }

    show = (message, type = 'info', options = {}) => {
        const id = Date.now().toString();
        const toast = this.createToast(id, message, type, options);

        if (this.container) {
            this.container.appendChild(toast);
            this.toasts.set(id, toast);

            // Trigger entrance animation
            requestAnimationFrame(() => {
                toast.classList.add('toast-entering');
            });

            // Auto dismiss
            if (options.autoDismiss !== false) {
                setTimeout(() => {
                    this.dismiss(id);
                }, options.duration || this.defaultDuration);
            }

            // Screen reader announcement
            this.announceToScreenReader(message);
        }

        return id;
    };

    createToast(id, message, type, options) {
        const template = document.getElementById('toast-template');
        if (!template) { return null; }

        const toast = template.content.cloneNode(true).querySelector('.toast-notification');
        toast.setAttribute('data-toast-id', id);
        toast.classList.add(`toast-${type}`);

        // Set content
        const titleEl = toast.querySelector('.toast-title');
        const messageEl = toast.querySelector('.toast-message');
        const iconEl = toast.querySelector('.toast-icon');

        if (titleEl) { titleEl.textContent = options.title || this.getDefaultTitle(type); }
        if (messageEl) { messageEl.textContent = message; }
        if (iconEl) { this.setToastIcon(iconEl, type); }

        // Setup close button
        const closeBtn = toast.querySelector('.toast-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.dismiss(id));
        }

        // Setup actions
        if (options.actions) {
            this.setupToastActions(toast, options.actions, id);
        }

        // Setup progress bar for auto-dismiss
        if (options.autoDismiss !== false) {
            this.setupProgressBar(toast, options.duration || this.defaultDuration);
        }

        return toast;
    }

    setToastIcon(iconEl, type) {
        const iconId = `toast-${type}-icon`;
        const sourceIcon = document.getElementById(iconId);
        if (sourceIcon) {
            iconEl.innerHTML = sourceIcon.innerHTML;
            iconEl.className = sourceIcon.className;
        }
    }

    setupToastActions(toast, actions, toastId) {
        const actionsContainer = toast.querySelector('.toast-actions');
        if (!actionsContainer || !actions.length) { return; }

        actionsContainer.classList.remove('hidden');

        actions.forEach((action, index) => {
            const button = actionsContainer.querySelector(
                index === 0 ? '.toast-action-primary' : '.toast-action-secondary'
            );
            if (button) {
                button.textContent = action.text;
                button.onclick = () => {
                    action.handler();
                    this.dismiss(toastId);
                };
            }
        });
    }

    setupProgressBar(toast, duration) {
        const progressContainer = toast.querySelector('.toast-progress-container');
        const progressBar = toast.querySelector('.toast-progress');

        if (progressContainer && progressBar) {
            progressContainer.classList.remove('hidden');
            progressBar.style.setProperty('--duration', `${duration}ms`);

            requestAnimationFrame(() => {
                progressBar.style.width = '0%';
            });
        }
    }

    dismiss(id) {
        const toast = this.toasts.get(id);
        if (toast) {
            toast.classList.add('toast-removing');
            setTimeout(() => {
                toast.remove();
                this.toasts.delete(id);
            }, 300);
        }
    }

    dismissAll() {
        this.toasts.forEach((toast, id) => {
            this.dismiss(id);
        });
    }

    getDefaultTitle(type) {
        const titles = {
            success: 'Success',
            error: 'Error',
            warning: 'Warning',
            info: 'Info'
        };
        return titles[type] || 'Notification';
    }

    announceToScreenReader(message) {
        const announcement = document.getElementById('toast-announcement');
        if (announcement) {
            announcement.textContent = message;
            setTimeout(() => {
                announcement.textContent = '';
            }, 1000);
        }
    }
}

// Modal Manager Class
class ModalManager {
    constructor() {
        this.activeModal = null;
        this.previousFocus = null;
    }

    open(modalId) {
        const modal = document.getElementById(modalId);
        if (!modal) { return; }

        this.previousFocus = document.activeElement;
        this.activeModal = modal;

        modal.classList.add('modal-open');
        modal.setAttribute('aria-hidden', 'false');

        // Focus management
        const focusableElements = modal.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );

        if (focusableElements.length > 0) {
            focusableElements[0].focus();
        }

        // Escape key to close
        document.addEventListener('keydown', this.handleModalEscape);

        // Prevent body scroll
        document.body.style.overflow = 'hidden';
    }

    close(modalId) {
        const modal = document.getElementById(modalId);
        if (!modal) { return; }

        modal.classList.remove('modal-open');
        modal.setAttribute('aria-hidden', 'true');

        // Restore focus
        if (this.previousFocus) {
            this.previousFocus.focus();
        }

        // Remove event listeners
        document.removeEventListener('keydown', this.handleModalEscape);

        // Restore body scroll
        document.body.style.overflow = '';

        this.activeModal = null;
        this.previousFocus = null;
    }

    handleModalEscape = e => {
        if (e.key === 'Escape' && this.activeModal) {
            this.close(this.activeModal.id);
        }
    };
}

// Scroll Manager Class
class ScrollManager {
    constructor() {
        this.progressBar = null;
        this.backToTopBtn = document.getElementById('back-to-top');
        this.scrollThreshold = 300;
        this.ticking = false;
    }

    setProgressBar(element) {
        this.progressBar = element;
    }

    handleScroll() {
        if (!this.ticking) {
            requestAnimationFrame(() => {
                this.updateScrollProgress();
                this.updateBackToTopButton();
                this.ticking = false;
            });
            this.ticking = true;
        }
    }

    updateScrollProgress() {
        if (!this.progressBar) { return; }

        const scrollTop = window.pageYOffset;
        const docHeight = document.documentElement.scrollHeight - window.innerHeight;
        const scrolled = (scrollTop / docHeight) * 100;

        this.progressBar.style.width = `${Math.min(scrolled, 100)}%`;
    }

    updateBackToTopButton() {
        if (!this.backToTopBtn) { return; }

        const shouldShow = window.pageYOffset > this.scrollThreshold;
        this.backToTopBtn.classList.toggle('visible', shouldShow);
    }

    scrollToTop() {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    }

    scrollToElement(element, offset = 80) {
        const elementPosition = element.offsetTop - offset;
        window.scrollTo({
            top: elementPosition,
            behavior: 'smooth'
        });
    }
}

// Loading Manager Class
class LoadingManager {
    constructor() {
        this.overlay = document.getElementById('loading-overlay');
        this.loadingMessages = [
            'Loading content...',
            'Preparing your experience...',
            'Almost ready...',
            'Just a moment...'
        ];
        this.currentMessageIndex = 0;
    }

    show(message) {
        if (!this.overlay) { return; }

        if (message) {
            const messageEl = document.getElementById('loading-message');
            if (messageEl) { messageEl.textContent = message; }
        }

        this.overlay.classList.add('show');
        this.announceToScreenReader('Loading');
    }

    hide() {
        if (!this.overlay) { return; }

        this.overlay.classList.remove('show');
    }

    hideInitialLoader() {
        // Hide any initial page loader
        const initialLoader = document.querySelector('.initial-loader');
        if (initialLoader) {
            initialLoader.style.opacity = '0';
            setTimeout(() => {
                initialLoader.remove();
            }, 300);
        }
    }

    updateProgress(percent) {
        const progressBar = document.getElementById('loading-progress');
        if (progressBar) {
            progressBar.style.width = `${percent}%`;
        }
    }

    updateMessage(message) {
        const messageEl = document.getElementById('loading-message');
        if (messageEl) {
            messageEl.textContent = message;
        }
    }

    cycleMessages(interval = 2000) {
        setInterval(() => {
            this.currentMessageIndex = (this.currentMessageIndex + 1) % this.loadingMessages.length;
            this.updateMessage(this.loadingMessages[this.currentMessageIndex]);
        }, interval);
    }

    announceToScreenReader(message) {
        const announcement = document.getElementById('loading-announcement');
        if (announcement) {
            announcement.textContent = message;
        }
    }
}

// Search Manager Class
class SearchManager {
    constructor() {
        this.modal = document.getElementById('search-modal');
        this.input = document.getElementById('search-input');
        this.resultsContainer = document.getElementById('search-results');
        this.debounceTimer = null;
        this.currentQuery = '';
        this.selectedIndex = -1;
        this.results = [];
    }

    initialize() {
        if (!this.modal || !this.input) { return; }

        // Setup event listeners
        this.input.addEventListener('input', this.debounce(e => this.handleInput(e.target.value), 300));
        this.input.addEventListener('keydown', e => this.handleKeydown(e));

        // Setup filter buttons
        const filters = this.modal.querySelectorAll('.search-filter');
        filters.forEach(filter => {
            filter.addEventListener('click', e => this.handleFilterClick(e.target));
        });

        // Setup suggestions
        const suggestions = this.modal.querySelectorAll('.search-suggestion');
        suggestions.forEach(suggestion => {
            suggestion.addEventListener('click', e => {
                this.input.value = e.target.textContent;
                this.handleInput(e.target.textContent);
            });
        });
    }

    open() {
        if (!this.modal) { return; }

        this.modal.classList.add('search-modal-open');
        this.modal.style.opacity = '1';
        this.modal.style.visibility = 'visible';

        if (this.input) {
            this.input.focus();
        }

        // Show recent searches initially
        this.showRecentSearches();
    }

    close() {
        if (!this.modal) { return; }

        this.modal.classList.remove('search-modal-open');
        this.modal.style.opacity = '0';
        this.modal.style.visibility = 'hidden';

        this.clearResults();
        this.selectedIndex = -1;
    }

    handleInput(query) {
        this.currentQuery = query.trim();

        if (this.debounceTimer) {
            clearTimeout(this.debounceTimer);
        }

        this.debounceTimer = setTimeout(() => {
            if (this.currentQuery.length >= 2) {
                this.performSearch(this.currentQuery);
            } else {
                this.showRecentSearches();
            }
        }, 300);
    }

    handleKeydown(e) {
        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                this.selectedIndex = Math.min(this.selectedIndex + 1, this.results.length - 1);
                this.updateSelection();
                break;
            case 'ArrowUp':
                e.preventDefault();
                this.selectedIndex = Math.max(this.selectedIndex - 1, -1);
                this.updateSelection();
                break;
            case 'Enter':
                e.preventDefault();
                if (this.selectedIndex >= 0) {
                    this.selectResult(this.selectedIndex);
                }
                break;
            case 'Escape':
                this.close();
                break;
        }
    }

    handleFilterClick(filterBtn) {
        // Update active filter
        this.modal.querySelectorAll('.search-filter').forEach(btn => {
            btn.classList.remove('active');
        });
        filterBtn.classList.add('active');

        // Re-run search with new filter
        if (this.currentQuery) {
            this.performSearch(this.currentQuery);
        }
    }

    async performSearch(query) {
        this.showLoading();

        try {
            const activeFilter = this.modal.querySelector('.search-filter.active')?.dataset.filter || 'all';
            const response = await fetch(`/search/?q=${encodeURIComponent(query)}&filter=${activeFilter}`, {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            this.results = data.results || [];
            this.displayResults(this.results);

            // Save to recent searches
            this.saveRecentSearch(query);

        } catch (error) {
            console.error('Search error:', error);
            this.showError('Search temporarily unavailable');
        } finally {
            this.hideLoading();
        }
    }

    showLoading() {
        const loading = document.getElementById('search-loading');
        if (loading) { loading.classList.remove('hidden'); }

        const recent = document.getElementById('search-recent');
        if (recent) { recent.style.display = 'none'; }
    }

    hideLoading() {
        const loading = document.getElementById('search-loading');
        if (loading) { loading.classList.add('hidden'); }
    }

    displayResults(results) {
        if (!this.resultsContainer) { return; }

        this.resultsContainer.innerHTML = '';

        if (results.length === 0) {
            this.showNoResults();
            return;
        }

        results.forEach((result, index) => {
            const resultEl = this.createResultElement(result, index);
            this.resultsContainer.appendChild(resultEl);
        });

        // Hide other sections
        const recent = document.getElementById('search-recent');
        const noResults = document.getElementById('search-no-results');
        if (recent) { recent.style.display = 'none'; }
        if (noResults) { noResults.classList.add('hidden'); }
    }

    createResultElement(result, index) {
        const template = document.getElementById('search-result-template');
        if (!template) { return document.createElement('div'); }

        const element = template.content.cloneNode(true).querySelector('.search-result');
        element.dataset.index = index;

        // Fill in result data
        const title = element.querySelector('.result-title');
        const description = element.querySelector('.result-description');
        const category = element.querySelector('.result-category');
        const date = element.querySelector('.result-date');
        const icon = element.querySelector('.result-icon');

        if (title) { title.textContent = result.title; }
        if (description) { description.textContent = result.description; }
        if (category) { category.textContent = result.category; }
        if (date) { date.textContent = result.date; }
        if (icon) { this.setResultIcon(icon, result.type); }

        // Click handler
        element.addEventListener('click', () => this.selectResult(index));

        return element;
    }

    setResultIcon(iconEl, type) {
        const icons = {
            blog: '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"></path></svg>',
            project: '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"></path></svg>',
            tool: '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path></svg>'
        };
        iconEl.innerHTML = icons[type] || icons.blog;
    }

    updateSelection() {
        const results = this.resultsContainer.querySelectorAll('.search-result');
        results.forEach((result, index) => {
            result.classList.toggle('selected', index === this.selectedIndex);
        });
    }

    selectResult(index) {
        if (index >= 0 && index < this.results.length) {
            const result = this.results[index];
            window.location.href = result.url;
        }
    }

    showNoResults() {
        const noResults = document.getElementById('search-no-results');
        if (noResults) { noResults.classList.remove('hidden'); }
    }

    showError(message) {
        // Implementation for showing error message
        console.error('Search error:', message);
    }

    showRecentSearches() {
        const recent = document.getElementById('search-recent');
        if (recent) { recent.style.display = 'block'; }

        // Load and display recent searches from localStorage
        const recentSearches = this.getRecentSearches();
        const listContainer = document.getElementById('recent-searches-list');

        if (listContainer && recentSearches.length > 0) {
            listContainer.innerHTML = '';
            recentSearches.forEach(search => {
                const item = document.createElement('button');
                item.className = 'text-left text-sm text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white py-1';
                item.textContent = search;
                item.addEventListener('click', () => {
                    this.input.value = search;
                    this.handleInput(search);
                });
                listContainer.appendChild(item);
            });
        }
    }

    saveRecentSearch(query) {
        let recent = this.getRecentSearches();
        recent = recent.filter(item => item !== query);
        recent.unshift(query);
        recent = recent.slice(0, 5); // Keep only 5 recent searches

        localStorage.setItem('recentSearches', JSON.stringify(recent));
    }

    getRecentSearches() {
        try {
            return JSON.parse(localStorage.getItem('recentSearches') || '[]');
        } catch {
            return [];
        }
    }

    clearRecentSearches() {
        localStorage.removeItem('recentSearches');
        this.showRecentSearches();
    }
}

// Animation Manager Class
class AnimationManager {
    constructor() {
        this.observers = new Map();
        this.setupIntersectionObserver();
    }

    setupIntersectionObserver() {
        if (!('IntersectionObserver' in window)) { return; }

        const options = {
            root: null,
            rootMargin: '-10% 0px',
            threshold: 0.1
        };

        this.scrollObserver = new IntersectionObserver(entries => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    this.triggerAnimation(entry.target);
                }
            });
        }, options);
    }

    initializeScrollAnimations() {
        const elements = document.querySelectorAll('[data-animate]');
        elements.forEach(element => {
            this.scrollObserver.observe(element);
        });
    }

    triggerAnimation(element) {
        const animationType = element.dataset.animate;
        const delay = element.dataset.delay || 0;

        setTimeout(() => {
            switch (animationType) {
                case 'fade-in':
                    element.classList.add('animate-fade-in');
                    break;
                case 'slide-up':
                    element.classList.add('animate-slide-up');
                    break;
                case 'slide-in-left':
                    element.classList.add('animate-slide-in-left');
                    break;
                case 'slide-in-right':
                    element.classList.add('animate-slide-in-right');
                    break;
                case 'scale-in':
                    element.classList.add('animate-scale-in');
                    break;
            }
        }, delay);

        // Stop observing this element
        this.scrollObserver.unobserve(element);
    }

    handleScrollAnimations() {
        // Handle scroll-based animations that need continuous updates
    }

    triggerDelayedAnimations() {
        // Trigger animations that should happen after page load
        const delayedElements = document.querySelectorAll('[data-animate-delay]');
        delayedElements.forEach(element => {
            const delay = parseInt(element.dataset.animateDelay, 10) || 0;
            setTimeout(() => {
                element.classList.add('animate-fade-in');
            }, delay);
        });
    }
}

// Keyboard Manager Class
class KeyboardManager {
    constructor() {
        this.shortcuts = new Map();
        this.setupGlobalShortcuts();
        this.setupEventListeners();
    }

    setupGlobalShortcuts() {
        // Search shortcut
        this.addShortcut('ctrl+k', () => {
            if (window.uiEnhancements?.searchManager) {
                window.uiEnhancements.searchManager.open();
            }
        });

        // Escape to close modals
        this.addShortcut('escape', () => {
            if (window.uiEnhancements?.modalManager?.activeModal) {
                window.uiEnhancements.modalManager.close(
                    window.uiEnhancements.modalManager.activeModal.id
                );
            }
            if (window.uiEnhancements?.searchManager?.modal?.classList.contains('search-modal-open')) {
                window.uiEnhancements.searchManager.close();
            }
        });
    }

    addShortcut(key, handler) {
        this.shortcuts.set(key.toLowerCase(), handler);
    }

    setupEventListeners() {
        document.addEventListener('keydown', e => {
            const key = this.getKeyString(e);
            const handler = this.shortcuts.get(key);

            if (handler) {
                // Don't trigger shortcuts when typing in inputs
                if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
                    // Only allow escape key in inputs
                    if (key === 'escape') {
                        e.preventDefault();
                        handler(e);
                    }
                    return;
                }

                e.preventDefault();
                handler(e);
            }
        });
    }

    getKeyString(e) {
        let key = e.key.toLowerCase();

        if (e.ctrlKey) { key = `ctrl+${key}`; }
        if (e.altKey) { key = `alt+${key}`; }
        if (e.shiftKey && key.length > 1) { key = `shift+${key}`; }

        return key;
    }
}

// Theme Manager Class
class ThemeManager {
    constructor() {
        this.currentTheme = localStorage.getItem('theme') || 'dark';
        this.applyTheme(this.currentTheme);
    }

    toggleTheme() {
        this.currentTheme = this.currentTheme === 'light' ? 'dark' : 'light';
        this.applyTheme(this.currentTheme);
        localStorage.setItem('theme', this.currentTheme);
    }

    applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);

        // Update theme color meta tag
        const themeColorMeta = document.querySelector('meta[name="theme-color"]');
        if (themeColorMeta) {
            themeColorMeta.setAttribute('content', theme === 'dark' ? '#0f172a' : '#ffffff');
        }
    }

    getTheme() {
        return this.currentTheme;
    }

    setTheme(theme) {
        if (['light', 'dark'].includes(theme)) {
            this.currentTheme = theme;
            this.applyTheme(theme);
            localStorage.setItem('theme', theme);
        }
    }
}

// Global Functions
window.toggleSearchModal = () => {
    if (!window.uiEnhancements) { return; }

    const searchManager = window.uiEnhancements.searchManager;
    const isOpen = searchManager.modal?.classList.contains('search-modal-open');

    if (isOpen) {
        searchManager.close();
    } else {
        searchManager.open();
    }
};

window.closeSearchModal = () => {
    if (window.uiEnhancements?.searchManager) {
        window.uiEnhancements.searchManager.close();
    }
};

window.clearRecentSearches = () => {
    if (window.uiEnhancements?.searchManager) {
        window.uiEnhancements.searchManager.clearRecentSearches();
    }
};

window.showToast = (message, type = 'info', options = {}) => {
    if (window.uiEnhancements?.toastManager) {
        return window.uiEnhancements.toastManager.show(message, type, options);
    }
};

// Initialize UI Enhancements
document.addEventListener('DOMContentLoaded', () => {
    window.uiEnhancements = new UIEnhancements();

    // Initialize search manager
    if (window.uiEnhancements.searchManager) {
        window.uiEnhancements.searchManager.initialize();
    }

    console.log('UI Enhancements initialized successfully');
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { UIEnhancements, ToastManager, ModalManager, ScrollManager, LoadingManager, SearchManager, AnimationManager, KeyboardManager, ThemeManager };
}
