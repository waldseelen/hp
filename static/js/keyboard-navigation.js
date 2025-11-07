/**
 * Keyboard Navigation Enhancement
 * Improves keyboard accessibility throughout the site
 */

class KeyboardNavigationManager {
    constructor() {
        this.focusableElements = [
            'a[href]',
            'button:not([disabled])',
            'input:not([disabled])',
            'select:not([disabled])',
            'textarea:not([disabled])',
            '[tabindex]:not([tabindex="-1"])',
            'details',
            'summary'
        ];

        this.trapStack = [];
        this.init();
    }

    init() {
        this.addSkipNavigation();
        this.enhanceFocusManagement();
        this.setupKeyboardShortcuts();
        this.improveTabOrder();
        this.addAriaLabels();
        this.setupFocusTrap();

        console.log('⌨️ Keyboard navigation initialized');
    }

    addSkipNavigation() {
        // Check if skip nav already exists
        if (document.querySelector('.skip-nav')) {
            return;
        }

        const skipNav = document.createElement('a');
        skipNav.href = '#main-content';
        skipNav.className = 'skip-nav';
        skipNav.textContent = 'Skip to main content';
        skipNav.setAttribute('aria-label', 'Skip to main content');

        // Insert as first element in body
        document.body.insertBefore(skipNav, document.body.firstChild);

        // Ensure main content has id
        const mainContent = document.querySelector('main');
        if (mainContent && !mainContent.id) {
            mainContent.id = 'main-content';
            mainContent.setAttribute('tabindex', '-1');
        }

        // Handle skip link click
        skipNav.addEventListener('click', e => {
            e.preventDefault();
            const target = document.querySelector(skipNav.getAttribute('href'));
            if (target) {
                target.focus();
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    }

    enhanceFocusManagement() {
        // Track focus for debugging
        let lastFocused = null;

        document.addEventListener('focusin', e => {
            lastFocused = e.target;
            this.handleFocusIn(e.target);
        });

        document.addEventListener('focusout', e => {
            this.handleFocusOut(e.target);
        });

        // Handle focus restoration when modals close
        document.addEventListener('keydown', e => {
            if (e.key === 'Escape') {
                this.handleEscapeKey(e);
            }
        });

        // Improve focus visibility
        this.addFocusStyles();
    }

    handleFocusIn(element) {
        // Remove previous focus indicators
        document.querySelectorAll('.js-focus-active').forEach(el => {
            el.classList.remove('js-focus-active');
        });

        // Add focus indicator
        element.classList.add('js-focus-active');

        // Announce focus for screen readers if needed
        if (element.hasAttribute('aria-describedby')) {
            const descId = element.getAttribute('aria-describedby');
            const description = document.getElementById(descId);
            if (description && description.hasAttribute('data-announce-on-focus')) {
                this.announceToScreenReader(description.textContent);
            }
        }
    }

    handleFocusOut(element) {
        element.classList.remove('js-focus-active');
    }

    handleEscapeKey(e) {
        // Close any open modals or dropdowns
        const openModal = document.querySelector('[role="dialog"][aria-hidden="false"]');
        if (openModal) {
            this.closeModal(openModal);
            e.preventDefault();
            return;
        }

        const openDropdown = document.querySelector('[aria-expanded="true"]');
        if (openDropdown) {
            this.closeDropdown(openDropdown);
            e.preventDefault();
            return;
        }
    }

    setupKeyboardShortcuts() {
        document.addEventListener('keydown', e => {
            // Skip if user is typing in input
            if (this.isTyping(e.target)) {
                return;
            }

            // Global shortcuts
            switch (e.key) {
                case '/':
                    e.preventDefault();
                    this.focusSearch();
                    break;

                case 'h':
                    if (!e.ctrlKey && !e.metaKey) {
                        e.preventDefault();
                        this.goHome();
                    }
                    break;

                case '?':
                    e.preventDefault();
                    this.showKeyboardHelp();
                    break;
            }

            // Ctrl/Cmd shortcuts
            if (e.ctrlKey || e.metaKey) {
                switch (e.key) {
                    case 'k':
                        e.preventDefault();
                        this.focusSearch();
                        break;

                    case 'm':
                        e.preventDefault();
                        this.toggleMainNavigation();
                        break;
                }
            }
        });
    }

    improveTabOrder() {
        // Ensure logical tab order
        const allFocusable = document.querySelectorAll(this.focusableElements.join(','));

        allFocusable.forEach((element, index) => {
            // Add tab index if not present and element should be tabbable
            if (!element.hasAttribute('tabindex')) {
                // Most elements should be naturally tabbable (tabindex = 0)
                // Only set explicitly if needed
                if (this.shouldBeInTabOrder(element)) {
                    element.setAttribute('tabindex', '0');
                }
            }

            // Ensure proper ARIA labels
            this.ensureAccessibleLabel(element);
        });

        // Handle arrow key navigation in groups
        this.setupArrowKeyNavigation();
    }

    shouldBeInTabOrder(element) {
        // Check if element is visible and not disabled
        const rect = element.getBoundingClientRect();
        const isVisible = rect.width > 0 && rect.height > 0;
        const isEnabled = !element.disabled && !element.getAttribute('aria-disabled');

        return isVisible && isEnabled;
    }

    ensureAccessibleLabel(element) {
        const tagName = element.tagName.toLowerCase();

        // Skip if already has accessible label
        if (element.getAttribute('aria-label') ||
            element.getAttribute('aria-labelledby') ||
            element.querySelector('span.sr-only') ||
            (tagName === 'a' && element.textContent.trim()) ||
            (tagName === 'button' && element.textContent.trim())) {
            return;
        }

        // Add labels based on context
        if (tagName === 'button') {
            this.labelButton(element);
        } else if (tagName === 'a') {
            this.labelLink(element);
        } else if (['input', 'select', 'textarea'].includes(tagName)) {
            this.labelFormField(element);
        }
    }

    labelButton(button) {
        // Try to infer label from context
        const icon = button.querySelector('svg, i, .icon');
        const text = button.textContent.trim();

        if (!text && icon) {
            const parent = button.closest('[data-component]');
            const componentType = parent?.getAttribute('data-component');

            switch (componentType) {
                case 'search':
                    button.setAttribute('aria-label', 'Search');
                    break;
                case 'menu':
                    button.setAttribute('aria-label', 'Toggle menu');
                    break;
                case 'theme':
                    button.setAttribute('aria-label', 'Toggle theme');
                    break;
                default:
                    button.setAttribute('aria-label', 'Button');
            }
        }
    }

    labelLink(link) {
        const text = link.textContent.trim();

        if (!text) {
            const img = link.querySelector('img');
            if (img && img.alt) {
                link.setAttribute('aria-label', img.alt);
            } else {
                link.setAttribute('aria-label', 'Link');
            }
        }

        // Add context for external links
        if (link.hostname && link.hostname !== location.hostname) {
            const currentLabel = link.getAttribute('aria-label') || text;
            link.setAttribute('aria-label', `${currentLabel} (external link)`);
        }
    }

    labelFormField(field) {
        // Check for associated label
        const id = field.id;
        if (id) {
            const label = document.querySelector(`label[for="${id}"]`);
            if (label) {
                return; // Already has label
            }
        }

        // Try to find nearby label text
        const placeholder = field.placeholder;
        const parentText = field.parentElement?.textContent?.trim();

        if (placeholder) {
            field.setAttribute('aria-label', placeholder);
        } else if (parentText && parentText.length < 50) {
            field.setAttribute('aria-label', parentText);
        }
    }

    setupArrowKeyNavigation() {
        // Navigation for menu items
        document.querySelectorAll('[role="menu"], [role="menubar"]').forEach(menu => {
            this.setupMenuNavigation(menu);
        });

        // Navigation for tab lists
        document.querySelectorAll('[role="tablist"]').forEach(tablist => {
            this.setupTabNavigation(tablist);
        });
    }

    setupMenuNavigation(menu) {
        const items = menu.querySelectorAll('[role="menuitem"]');

        menu.addEventListener('keydown', e => {
            const currentIndex = Array.from(items).indexOf(e.target);

            switch (e.key) {
                case 'ArrowDown':
                case 'ArrowRight':
                    e.preventDefault();
                    const nextIndex = (currentIndex + 1) % items.length;
                    items[nextIndex].focus();
                    break;

                case 'ArrowUp':
                case 'ArrowLeft':
                    e.preventDefault();
                    const prevIndex = (currentIndex - 1 + items.length) % items.length;
                    items[prevIndex].focus();
                    break;

                case 'Home':
                    e.preventDefault();
                    items[0].focus();
                    break;

                case 'End':
                    e.preventDefault();
                    items[items.length - 1].focus();
                    break;
            }
        });
    }

    setupTabNavigation(tablist) {
        const tabs = tablist.querySelectorAll('[role="tab"]');

        tablist.addEventListener('keydown', e => {
            const currentIndex = Array.from(tabs).indexOf(e.target);

            switch (e.key) {
                case 'ArrowLeft':
                    e.preventDefault();
                    const prevIndex = (currentIndex - 1 + tabs.length) % tabs.length;
                    this.activateTab(tabs[prevIndex]);
                    break;

                case 'ArrowRight':
                    e.preventDefault();
                    const nextIndex = (currentIndex + 1) % tabs.length;
                    this.activateTab(tabs[nextIndex]);
                    break;

                case 'Home':
                    e.preventDefault();
                    this.activateTab(tabs[0]);
                    break;

                case 'End':
                    e.preventDefault();
                    this.activateTab(tabs[tabs.length - 1]);
                    break;
            }
        });
    }

    addAriaLabels() {
        // Add missing ARIA labels to common elements

        // Logo/brand links
        document.querySelectorAll('a[href="/"], a[href="#home"]').forEach(link => {
            if (!link.getAttribute('aria-label')) {
                link.setAttribute('aria-label', 'Go to homepage');
            }
        });

        // Social links
        document.querySelectorAll('a[href*="github"], a[href*="linkedin"], a[href*="twitter"]').forEach(link => {
            const url = link.href;
            let platform = 'social media';

            if (url.includes('github')) { platform = 'GitHub'; } else if (url.includes('linkedin')) { platform = 'LinkedIn'; } else if (url.includes('twitter')) { platform = 'Twitter'; }

            if (!link.getAttribute('aria-label')) {
                link.setAttribute('aria-label', `Visit ${platform} profile`);
            }
        });

        // Back to top buttons
        document.querySelectorAll('[href="#top"], .back-to-top').forEach(button => {
            if (!button.getAttribute('aria-label')) {
                button.setAttribute('aria-label', 'Back to top');
            }
        });
    }

    setupFocusTrap() {
        // Focus trap for modals and dialogs
        document.addEventListener('keydown', e => {
            if (e.key === 'Tab') {
                const modal = document.querySelector('[role="dialog"]:not([aria-hidden="true"])');
                if (modal) {
                    this.trapFocus(e, modal);
                }
            }
        });
    }

    trapFocus(e, container) {
        const focusableElements = container.querySelectorAll(this.focusableElements.join(','));
        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];

        if (e.shiftKey) {
            if (document.activeElement === firstElement) {
                e.preventDefault();
                lastElement.focus();
            }
        } else {
            if (document.activeElement === lastElement) {
                e.preventDefault();
                firstElement.focus();
            }
        }
    }

    addFocusStyles() {
        // Ensure focus is visible
        const style = document.createElement('style');
        style.textContent = `
            .js-focus-active {
                outline: 2px solid var(--color-focus-ring, #005fcc) !important;
                outline-offset: 2px !important;
                border-radius: 2px !important;
            }

            /* High contrast mode support */
            @media (prefers-contrast: high) {
                .js-focus-active {
                    outline-width: 3px !important;
                    outline-color: currentColor !important;
                }
            }

            /* Ensure skip nav is visible when focused */
            .skip-nav:focus {
                position: absolute !important;
                top: 0 !important;
                left: 6px !important;
                z-index: 9999 !important;
                clip: auto !important;
                width: auto !important;
                height: auto !important;
            }
        `;
        document.head.appendChild(style);
    }

    // Helper methods
    isTyping(element) {
        const typingElements = ['input', 'textarea', 'select'];
        const isContentEditable = element.contentEditable === 'true';
        return typingElements.includes(element.tagName.toLowerCase()) || isContentEditable;
    }

    focusSearch() {
        const searchInput = document.querySelector('input[type="search"], input[placeholder*="search" i], #search');
        if (searchInput) {
            searchInput.focus();
            searchInput.select();
        }
    }

    goHome() {
        window.location.href = '/';
    }

    toggleMainNavigation() {
        const navToggle = document.querySelector('[aria-controls="main-navigation"], .nav-toggle');
        if (navToggle) {
            navToggle.click();
            navToggle.focus();
        }
    }

    showKeyboardHelp() {
        this.announceToScreenReader('Keyboard shortcuts: / to search, h for home, ? for help, Ctrl+K to search, Ctrl+M for menu');
    }

    announceToScreenReader(message) {
        const announcement = document.createElement('div');
        announcement.setAttribute('aria-live', 'polite');
        announcement.setAttribute('aria-atomic', 'true');
        announcement.className = 'sr-only';
        announcement.textContent = message;

        document.body.appendChild(announcement);

        setTimeout(() => {
            document.body.removeChild(announcement);
        }, 1000);
    }

    activateTab(tab) {
        // Deactivate all tabs
        const tablist = tab.closest('[role="tablist"]');
        const allTabs = tablist.querySelectorAll('[role="tab"]');

        allTabs.forEach(t => {
            t.setAttribute('aria-selected', 'false');
            t.setAttribute('tabindex', '-1');
        });

        // Activate selected tab
        tab.setAttribute('aria-selected', 'true');
        tab.setAttribute('tabindex', '0');
        tab.focus();

        // Show associated panel
        const panelId = tab.getAttribute('aria-controls');
        if (panelId) {
            const panel = document.getElementById(panelId);
            if (panel) {
                document.querySelectorAll('[role="tabpanel"]').forEach(p => {
                    p.hidden = true;
                });
                panel.hidden = false;
            }
        }
    }

    closeModal(modal) {
        modal.setAttribute('aria-hidden', 'true');
        modal.style.display = 'none';

        // Restore focus to trigger element
        const trigger = document.querySelector(`[aria-controls="${modal.id}"]`);
        if (trigger) {
            trigger.focus();
        }
    }

    closeDropdown(dropdown) {
        dropdown.setAttribute('aria-expanded', 'false');

        // Hide dropdown content
        const contentId = dropdown.getAttribute('aria-controls');
        if (contentId) {
            const content = document.getElementById(contentId);
            if (content) {
                content.hidden = true;
            }
        }
    }

    // Public API for external use
    static getInstance() {
        if (!this.instance) {
            this.instance = new KeyboardNavigationManager();
        }
        return this.instance;
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        KeyboardNavigationManager.getInstance();
    });
} else {
    KeyboardNavigationManager.getInstance();
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = KeyboardNavigationManager;
}
