/**
 * Accessibility Enhancement Module
 * Provides comprehensive accessibility features and WCAG 2.1 AA compliance monitoring
 * Features:
 * - Screen reader support and announcements
 * - Keyboard navigation management
 * - Focus management and trap
 * - Color contrast monitoring
 * - Text scaling and readability
 * - Motion and animation preferences
 * - Accessibility violation detection
 * - ARIA live regions management
 */

class AccessibilityManager {
    constructor() {
        this.focusStack = [];
        this.liveRegions = new Map();
        this.keyboardListeners = new Map();
        this.contrastRatio = { normal: 4.5, large: 3.0 };
        this.motionPreference = window.matchMedia('(prefers-reduced-motion: reduce)');
        this.contrastPreference = window.matchMedia('(prefers-contrast: high)');
        this.preferences = this.loadPreferences();
        
        this.init();
    }

    init() {
        this.setupLiveRegions();
        this.setupKeyboardNavigation();
        this.setupFocusManagement();
        this.setupMotionPreferences();
        this.setupContrastMonitoring();
        this.setupTextScaling();
        this.setupScreenReaderSupport();
        this.monitorAccessibilityViolations();
        this.addAccessibilityControls();
    }

    // Live Regions Management
    setupLiveRegions() {
        // Create main announcement region
        const announcer = document.createElement('div');
        announcer.setAttribute('aria-live', 'polite');
        announcer.setAttribute('aria-atomic', 'true');
        announcer.className = 'sr-only';
        announcer.id = 'accessibility-announcer';
        document.body.appendChild(announcer);
        this.liveRegions.set('announcer', announcer);

        // Create urgent announcement region
        const urgentAnnouncer = document.createElement('div');
        urgentAnnouncer.setAttribute('aria-live', 'assertive');
        urgentAnnouncer.setAttribute('aria-atomic', 'true');
        urgentAnnouncer.className = 'sr-only';
        urgentAnnouncer.id = 'accessibility-urgent-announcer';
        document.body.appendChild(urgentAnnouncer);
        this.liveRegions.set('urgent', urgentAnnouncer);

        // Create status region
        const statusRegion = document.createElement('div');
        statusRegion.setAttribute('aria-live', 'polite');
        statusRegion.setAttribute('aria-atomic', 'false');
        statusRegion.className = 'sr-only';
        statusRegion.id = 'accessibility-status';
        document.body.appendChild(statusRegion);
        this.liveRegions.set('status', statusRegion);
    }

    announce(message, priority = 'polite') {
        const region = priority === 'assertive' ? 
            this.liveRegions.get('urgent') : 
            this.liveRegions.get('announcer');
        
        if (region) {
            // Clear previous message
            region.textContent = '';
            
            // Add new message after a brief delay to ensure screen readers pick it up
            setTimeout(() => {
                region.textContent = message;
            }, 10);
            
            // Clear message after 5 seconds
            setTimeout(() => {
                if (region.textContent === message) {
                    region.textContent = '';
                }
            }, 5000);
        }
    }

    updateStatus(message) {
        const statusRegion = this.liveRegions.get('status');
        if (statusRegion) {
            statusRegion.textContent = message;
        }
    }

    // Keyboard Navigation
    setupKeyboardNavigation() {
        // Global keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            this.handleGlobalKeyboard(e);
        });

        // Skip links
        this.createSkipLinks();
        
        // Roving tabindex for complex widgets
        this.setupRovingTabindex();
        
        // Modal and dropdown keyboard handling
        this.setupModalKeyboardHandling();
    }

    createSkipLinks() {
        const skipLinks = document.createElement('div');
        skipLinks.className = 'skip-links';
        skipLinks.innerHTML = `
            <a href="#main-content" class="skip-link">Skip to main content</a>
            <a href="#navigation" class="skip-link">Skip to navigation</a>
            <a href="#search" class="skip-link">Skip to search</a>
        `;
        document.body.insertBefore(skipLinks, document.body.firstChild);
    }

    setupRovingTabindex() {
        // Find all roving tabindex containers
        const containers = document.querySelectorAll('[role="tablist"], [role="menubar"], [role="toolbar"]');
        
        containers.forEach(container => {
            this.initializeRovingTabindex(container);
        });
    }

    initializeRovingTabindex(container) {
        const items = container.querySelectorAll('[role="tab"], [role="menuitem"], [role="button"]');
        if (items.length === 0) return;

        // Set initial focus
        items[0].tabIndex = 0;
        for (let i = 1; i < items.length; i++) {
            items[i].tabIndex = -1;
        }

        container.addEventListener('keydown', (e) => {
            const currentIndex = Array.from(items).indexOf(e.target);
            let nextIndex = currentIndex;

            switch (e.key) {
                case 'ArrowRight':
                case 'ArrowDown':
                    e.preventDefault();
                    nextIndex = (currentIndex + 1) % items.length;
                    break;
                case 'ArrowLeft':
                case 'ArrowUp':
                    e.preventDefault();
                    nextIndex = currentIndex > 0 ? currentIndex - 1 : items.length - 1;
                    break;
                case 'Home':
                    e.preventDefault();
                    nextIndex = 0;
                    break;
                case 'End':
                    e.preventDefault();
                    nextIndex = items.length - 1;
                    break;
            }

            if (nextIndex !== currentIndex) {
                items[currentIndex].tabIndex = -1;
                items[nextIndex].tabIndex = 0;
                items[nextIndex].focus();
            }
        });
    }

    handleGlobalKeyboard(e) {
        // Alt + 1: Go to main content
        if (e.altKey && e.key === '1') {
            e.preventDefault();
            const main = document.getElementById('main-content') || document.querySelector('main');
            if (main) {
                main.focus();
                this.announce('Jumped to main content');
            }
        }

        // Alt + 2: Go to navigation
        if (e.altKey && e.key === '2') {
            e.preventDefault();
            const nav = document.getElementById('navigation') || document.querySelector('nav');
            if (nav) {
                nav.focus();
                this.announce('Jumped to navigation');
            }
        }

        // Alt + S: Go to search
        if (e.altKey && e.key.toLowerCase() === 's') {
            e.preventDefault();
            const search = document.getElementById('search') || document.querySelector('[role="search"] input');
            if (search) {
                search.focus();
                this.announce('Jumped to search');
            }
        }

        // Escape: Close modals/dropdowns
        if (e.key === 'Escape') {
            this.closeActiveModals();
        }
    }

    setupModalKeyboardHandling() {
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                const modal = document.querySelector('[role="dialog"]:not([aria-hidden="true"])');
                if (modal) {
                    this.trapFocus(e, modal);
                }
            }
        });
    }

    // Focus Management
    setupFocusManagement() {
        // Track focus for restoration
        document.addEventListener('focusin', (e) => {
            this.lastFocusedElement = e.target;
        });

        // Enhance focus visibility
        this.enhanceFocusVisibility();
        
        // Auto-focus management for dynamic content
        this.setupAutoFocus();
    }

    trapFocus(e, container) {
        const focusableElements = container.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        
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

    pushFocus(element) {
        if (this.lastFocusedElement) {
            this.focusStack.push(this.lastFocusedElement);
        }
        if (element) {
            element.focus();
        }
    }

    popFocus() {
        const element = this.focusStack.pop();
        if (element && document.contains(element)) {
            element.focus();
        }
    }

    enhanceFocusVisibility() {
        // Add enhanced focus styles for better visibility
        const style = document.createElement('style');
        style.textContent = `
            .a11y-focus-enhanced *:focus {
                outline: 3px solid #4A90E2 !important;
                outline-offset: 2px !important;
                box-shadow: 0 0 0 1px #ffffff !important;
            }
            
            .a11y-high-contrast *:focus {
                outline: 4px solid #FFFF00 !important;
                outline-offset: 2px !important;
                background-color: #000000 !important;
                color: #FFFFFF !important;
            }
        `;
        document.head.appendChild(style);
    }

    setupAutoFocus() {
        // Auto-focus first form element in new content
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        const firstInput = node.querySelector('input, select, textarea, button');
                        if (firstInput && node.getAttribute('data-auto-focus') === 'true') {
                            setTimeout(() => firstInput.focus(), 100);
                        }
                    }
                });
            });
        });

        observer.observe(document.body, { childList: true, subtree: true });
    }

    // Motion Preferences
    setupMotionPreferences() {
        this.motionPreference.addEventListener('change', () => {
            this.updateMotionPreferences();
        });
        
        this.updateMotionPreferences();
    }

    updateMotionPreferences() {
        if (this.motionPreference.matches) {
            document.body.classList.add('reduce-motion');
            this.announce('Reduced motion enabled');
        } else {
            document.body.classList.remove('reduce-motion');
        }
    }

    // Contrast Monitoring
    setupContrastMonitoring() {
        this.contrastPreference.addEventListener('change', () => {
            this.updateContrastPreferences();
        });
        
        this.updateContrastPreferences();
        this.auditContrast();
    }

    updateContrastPreferences() {
        if (this.contrastPreference.matches) {
            document.body.classList.add('high-contrast');
            this.announce('High contrast mode enabled');
        } else {
            document.body.classList.remove('high-contrast');
        }
    }

    auditContrast() {
        // Simple contrast ratio calculation
        const elements = document.querySelectorAll('*');
        const violations = [];

        elements.forEach((element) => {
            const styles = window.getComputedStyle(element);
            const bgColor = styles.backgroundColor;
            const color = styles.color;
            
            if (bgColor !== 'rgba(0, 0, 0, 0)' && color !== 'rgba(0, 0, 0, 0)') {
                const ratio = this.calculateContrastRatio(color, bgColor);
                const fontSize = parseFloat(styles.fontSize);
                const fontWeight = styles.fontWeight;
                
                const isLargeText = fontSize >= 18 || (fontSize >= 14 && (fontWeight === 'bold' || parseInt(fontWeight) >= 700));
                const requiredRatio = isLargeText ? this.contrastRatio.large : this.contrastRatio.normal;
                
                if (ratio < requiredRatio) {
                    violations.push({
                        element,
                        ratio: ratio.toFixed(2),
                        required: requiredRatio,
                        colors: { foreground: color, background: bgColor }
                    });
                }
            }
        });

        if (violations.length > 0 && this.preferences.showContrastWarnings) {
            console.group('Accessibility: Contrast Violations');
            violations.forEach(violation => {
                console.warn('Contrast ratio too low:', violation);
            });
            console.groupEnd();
        }
    }

    calculateContrastRatio(foreground, background) {
        // Simplified contrast calculation
        // In a real implementation, you'd want a more robust color parsing library
        const getLuminance = (color) => {
            // This is a simplified version
            const rgb = color.match(/\d+/g);
            if (!rgb) return 0;
            
            const [r, g, b] = rgb.map(val => {
                const normalized = parseInt(val) / 255;
                return normalized <= 0.03928 ? 
                    normalized / 12.92 : 
                    Math.pow((normalized + 0.055) / 1.055, 2.4);
            });
            
            return 0.2126 * r + 0.7152 * g + 0.0722 * b;
        };

        const l1 = getLuminance(foreground);
        const l2 = getLuminance(background);
        
        return (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
    }

    // Text Scaling
    setupTextScaling() {
        this.textScale = this.preferences.textScale || 1;
        this.applyTextScaling();
        
        // Listen for browser zoom changes
        window.addEventListener('resize', () => {
            this.detectZoomChange();
        });
    }

    applyTextScaling() {
        document.documentElement.style.setProperty('--text-scale', this.textScale);
        document.body.style.fontSize = `${this.textScale}rem`;
    }

    changeTextScale(scale) {
        this.textScale = Math.max(0.8, Math.min(2, scale));
        this.applyTextScaling();
        this.savePreferences();
        this.announce(`Text size changed to ${Math.round(this.textScale * 100)}%`);
    }

    detectZoomChange() {
        const currentZoom = Math.round(window.devicePixelRatio * 100);
        if (currentZoom !== this.lastZoom) {
            this.lastZoom = currentZoom;
            if (currentZoom > 150) {
                this.announce(`Browser zoom is at ${currentZoom}%. Consider using our built-in text scaling for better accessibility.`);
            }
        }
    }

    // Screen Reader Support
    setupScreenReaderSupport() {
        this.addAriaLabels();
        this.enhanceFormLabels();
        this.addLandmarkRoles();
        this.improveTableAccessibility();
    }

    addAriaLabels() {
        // Add missing aria-labels to interactive elements
        const interactiveElements = document.querySelectorAll('button, a, input, select, textarea');
        
        interactiveElements.forEach(element => {
            if (!element.getAttribute('aria-label') && !element.getAttribute('aria-labelledby')) {
                let label = '';
                
                if (element.textContent.trim()) {
                    label = element.textContent.trim();
                } else if (element.getAttribute('title')) {
                    label = element.getAttribute('title');
                } else if (element.getAttribute('placeholder')) {
                    label = element.getAttribute('placeholder');
                }
                
                if (label) {
                    element.setAttribute('aria-label', label);
                }
            }
        });
    }

    enhanceFormLabels() {
        const inputs = document.querySelectorAll('input, select, textarea');
        
        inputs.forEach(input => {
            if (!input.getAttribute('aria-labelledby') && !input.getAttribute('aria-label')) {
                const label = document.querySelector(`label[for="${input.id}"]`);
                if (label) {
                    input.setAttribute('aria-labelledby', label.id || this.generateId('label'));
                    if (!label.id) {
                        label.id = input.getAttribute('aria-labelledby');
                    }
                }
            }
            
            // Add required indicators
            if (input.required && !input.getAttribute('aria-required')) {
                input.setAttribute('aria-required', 'true');
            }
            
            // Add invalid state
            input.addEventListener('invalid', () => {
                input.setAttribute('aria-invalid', 'true');
            });
            
            input.addEventListener('input', () => {
                if (input.checkValidity()) {
                    input.removeAttribute('aria-invalid');
                }
            });
        });
    }

    addLandmarkRoles() {
        // Add landmark roles to semantic elements
        const landmarks = [
            { selector: 'header', role: 'banner' },
            { selector: 'nav', role: 'navigation' },
            { selector: 'main', role: 'main' },
            { selector: 'aside', role: 'complementary' },
            { selector: 'footer', role: 'contentinfo' }
        ];
        
        landmarks.forEach(landmark => {
            const elements = document.querySelectorAll(landmark.selector);
            elements.forEach(element => {
                if (!element.getAttribute('role')) {
                    element.setAttribute('role', landmark.role);
                }
            });
        });
    }

    improveTableAccessibility() {
        const tables = document.querySelectorAll('table');
        
        tables.forEach(table => {
            // Add table caption if missing
            if (!table.querySelector('caption') && !table.getAttribute('aria-label')) {
                const caption = document.createElement('caption');
                caption.textContent = 'Data table';
                caption.className = 'sr-only';
                table.insertBefore(caption, table.firstChild);
            }
            
            // Add scope to headers
            const headers = table.querySelectorAll('th');
            headers.forEach(header => {
                if (!header.getAttribute('scope')) {
                    const isRowHeader = header.parentElement.querySelector('th') === header;
                    header.setAttribute('scope', isRowHeader ? 'row' : 'col');
                }
            });
        });
    }

    // Accessibility Controls
    addAccessibilityControls() {
        const controlsPanel = document.createElement('div');
        controlsPanel.className = 'accessibility-controls';
        controlsPanel.setAttribute('role', 'region');
        controlsPanel.setAttribute('aria-label', 'Accessibility controls');
        
        controlsPanel.innerHTML = `
            <button id="a11y-toggle" class="a11y-control-btn" aria-expanded="false" aria-controls="a11y-panel">
                <span class="sr-only">Accessibility Options</span>
                ♿
            </button>
            <div id="a11y-panel" class="a11y-panel" aria-hidden="true">
                <h3>Accessibility Options</h3>
                <div class="a11y-option">
                    <label for="text-scale-range">Text Size:</label>
                    <input type="range" id="text-scale-range" min="0.8" max="2" step="0.1" value="${this.textScale}">
                    <span id="text-scale-value">${Math.round(this.textScale * 100)}%</span>
                </div>
                <div class="a11y-option">
                    <label>
                        <input type="checkbox" id="high-contrast-toggle" ${this.preferences.highContrast ? 'checked' : ''}>
                        High Contrast
                    </label>
                </div>
                <div class="a11y-option">
                    <label>
                        <input type="checkbox" id="reduce-motion-toggle" ${this.preferences.reduceMotion ? 'checked' : ''}>
                        Reduce Motion
                    </label>
                </div>
                <div class="a11y-option">
                    <label>
                        <input type="checkbox" id="focus-enhancement-toggle" ${this.preferences.focusEnhancement ? 'checked' : ''}>
                        Enhanced Focus
                    </label>
                </div>
            </div>
        `;
        
        document.body.appendChild(controlsPanel);
        this.setupControlsEventListeners();
    }

    setupControlsEventListeners() {
        const toggle = document.getElementById('a11y-toggle');
        const panel = document.getElementById('a11y-panel');
        const textScaleRange = document.getElementById('text-scale-range');
        const textScaleValue = document.getElementById('text-scale-value');
        const highContrastToggle = document.getElementById('high-contrast-toggle');
        const reduceMotionToggle = document.getElementById('reduce-motion-toggle');
        const focusEnhancementToggle = document.getElementById('focus-enhancement-toggle');

        toggle.addEventListener('click', () => {
            const isExpanded = toggle.getAttribute('aria-expanded') === 'true';
            toggle.setAttribute('aria-expanded', !isExpanded);
            panel.setAttribute('aria-hidden', isExpanded);
            panel.classList.toggle('open');
        });

        textScaleRange.addEventListener('input', () => {
            const scale = parseFloat(textScaleRange.value);
            this.changeTextScale(scale);
            textScaleValue.textContent = `${Math.round(scale * 100)}%`;
        });

        highContrastToggle.addEventListener('change', () => {
            this.preferences.highContrast = highContrastToggle.checked;
            document.body.classList.toggle('a11y-high-contrast', highContrastToggle.checked);
            this.savePreferences();
            this.announce(highContrastToggle.checked ? 'High contrast enabled' : 'High contrast disabled');
        });

        reduceMotionToggle.addEventListener('change', () => {
            this.preferences.reduceMotion = reduceMotionToggle.checked;
            document.body.classList.toggle('reduce-motion', reduceMotionToggle.checked);
            this.savePreferences();
            this.announce(reduceMotionToggle.checked ? 'Reduced motion enabled' : 'Reduced motion disabled');
        });

        focusEnhancementToggle.addEventListener('change', () => {
            this.preferences.focusEnhancement = focusEnhancementToggle.checked;
            document.body.classList.toggle('a11y-focus-enhanced', focusEnhancementToggle.checked);
            this.savePreferences();
            this.announce(focusEnhancementToggle.checked ? 'Focus enhancement enabled' : 'Focus enhancement disabled');
        });
    }

    // Accessibility Violation Detection
    monitorAccessibilityViolations() {
        if (!this.preferences.showViolationWarnings) return;

        // Monitor for missing alt text
        this.checkImages();
        
        // Monitor for missing form labels
        this.checkFormLabels();
        
        // Monitor for heading hierarchy
        this.checkHeadingHierarchy();
        
        // Monitor for color-only information
        this.checkColorOnlyInformation();
    }

    checkImages() {
        const images = document.querySelectorAll('img');
        const violations = [];
        
        images.forEach(img => {
            if (!img.getAttribute('alt') && !img.getAttribute('aria-label')) {
                violations.push(img);
            }
        });
        
        if (violations.length > 0) {
            console.group('Accessibility: Missing Alt Text');
            violations.forEach(img => {
                console.warn('Image missing alt text:', img);
                // Auto-fix: add empty alt for decorative images
                if (img.getAttribute('data-decorative') === 'true') {
                    img.setAttribute('alt', '');
                }
            });
            console.groupEnd();
        }
    }

    checkFormLabels() {
        const inputs = document.querySelectorAll('input, select, textarea');
        const violations = [];
        
        inputs.forEach(input => {
            if (input.type !== 'hidden' && 
                !input.getAttribute('aria-label') && 
                !input.getAttribute('aria-labelledby') &&
                !document.querySelector(`label[for="${input.id}"]`)) {
                violations.push(input);
            }
        });
        
        if (violations.length > 0) {
            console.group('Accessibility: Missing Form Labels');
            violations.forEach(input => {
                console.warn('Form input missing label:', input);
            });
            console.groupEnd();
        }
    }

    checkHeadingHierarchy() {
        const headings = Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, h6'));
        const violations = [];
        
        let lastLevel = 0;
        headings.forEach(heading => {
            const currentLevel = parseInt(heading.tagName.substring(1));
            
            if (currentLevel - lastLevel > 1) {
                violations.push({
                    element: heading,
                    issue: `Heading level jumps from h${lastLevel} to h${currentLevel}`
                });
            }
            
            lastLevel = currentLevel;
        });
        
        if (violations.length > 0) {
            console.group('Accessibility: Heading Hierarchy Issues');
            violations.forEach(violation => {
                console.warn(violation.issue, violation.element);
            });
            console.groupEnd();
        }
    }

    checkColorOnlyInformation() {
        // This is a simplified check - in practice, you'd want more sophisticated detection
        const colorOnlyElements = document.querySelectorAll('[style*="color:"], .text-red, .text-green, .text-blue');
        
        colorOnlyElements.forEach(element => {
            if (element.textContent.match(/error|warning|success|required/i)) {
                if (!element.getAttribute('aria-label') && !element.querySelector('.sr-only')) {
                    console.warn('Accessibility: Possible color-only information', element);
                }
            }
        });
    }

    // Utility Methods
    generateId(prefix = 'a11y') {
        return `${prefix}-${Math.random().toString(36).substr(2, 9)}`;
    }

    closeActiveModals() {
        const modals = document.querySelectorAll('[role="dialog"]:not([aria-hidden="true"])');
        modals.forEach(modal => {
            const closeBtn = modal.querySelector('.close, [aria-label*="close"], [data-dismiss]');
            if (closeBtn) {
                closeBtn.click();
            } else {
                modal.setAttribute('aria-hidden', 'true');
                this.popFocus();
            }
        });
    }

    // Preferences Management
    loadPreferences() {
        try {
            const saved = localStorage.getItem('accessibilityPreferences');
            return saved ? JSON.parse(saved) : {
                textScale: 1,
                highContrast: false,
                reduceMotion: false,
                focusEnhancement: false,
                showViolationWarnings: true,
                showContrastWarnings: false
            };
        } catch (e) {
            return {
                textScale: 1,
                highContrast: false,
                reduceMotion: false,
                focusEnhancement: false,
                showViolationWarnings: true,
                showContrastWarnings: false
            };
        }
    }

    savePreferences() {
        try {
            localStorage.setItem('accessibilityPreferences', JSON.stringify(this.preferences));
        } catch (e) {
            console.warn('Unable to save accessibility preferences');
        }
    }

    // Public API
    enable() {
        document.body.classList.add('accessibility-enabled');
        this.announce('Accessibility features enabled');
    }

    disable() {
        document.body.classList.remove('accessibility-enabled');
        this.announce('Accessibility features disabled');
    }

    getViolations() {
        // Return current accessibility violations
        return {
            images: this.checkImages(),
            forms: this.checkFormLabels(),
            headings: this.checkHeadingHierarchy(),
            contrast: this.auditContrast()
        };
    }
}

// Initialize accessibility manager
const accessibilityManager = new AccessibilityManager();

// Export for global access
window.AccessibilityManager = accessibilityManager;

// Auto-enable on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        accessibilityManager.enable();
    });
} else {
    accessibilityManager.enable();
}