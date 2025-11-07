/**
 * Privacy-Compliant Analytics System
 * ====================================
 *
 * GDPR/KVKK compliant frontend analytics tracking
 * Features:
 * - No personal data collection
 * - Session-based anonymous tracking
 * - User journey tracking
 * - Conversion funnel analysis
 * - A/B testing support
 * - Opt-out capability
 */

class PrivacyAnalytics {
    constructor() {
        this.isOptedOut = localStorage.getItem('analytics_opt_out') === 'true';
        this.sessionId = this.getOrCreateSessionId();
        this.currentJourneyId = null;
        this.currentTest = {};

        // GDPR consent status
        this.gdprConsent = localStorage.getItem('gdpr_consent') === 'true';

        // Initialize if user hasn't opted out
        if (!this.isOptedOut) {
            this.init();
        }
    }

    init() {
        console.log('PrivacyAnalytics initialized');

        // Track page view automatically
        this.trackPageView();

        // Set up event listeners
        this.setupEventListeners();

        // Initialize journey tracking
        this.startJourney('site_visit');

        // Track performance metrics
        this.trackPerformanceMetrics();
    }

    getOrCreateSessionId() {
        let sessionId = sessionStorage.getItem('analytics_session_id');

        if (!sessionId) {
            // Generate anonymous session ID
            sessionId = `anon_${this.generateRandomId()}`;
            sessionStorage.setItem('analytics_session_id', sessionId);
        }

        return sessionId;
    }

    generateRandomId() {
        return Math.random().toString(36).substr(2, 16) + Date.now().toString(36);
    }

    // GDPR Compliance Methods
    // ======================

    optOut() {
        localStorage.setItem('analytics_opt_out', 'true');
        this.isOptedOut = true;
        console.log('Analytics tracking opted out');
    }

    optIn() {
        localStorage.removeItem('analytics_opt_out');
        this.isOptedOut = false;
        console.log('Analytics tracking opted in');
        this.init();
    }

    setGDPRConsent(consent) {
        this.gdprConsent = consent;
        localStorage.setItem('gdpr_consent', consent.toString());

        // Send consent status to backend
        this.sendEvent('gdpr_consent', {
            consent: consent,
            timestamp: new Date().toISOString()
        });
    }

    getPrivacyInfo() {
        return {
            isOptedOut: this.isOptedOut,
            gdprConsent: this.gdprConsent,
            sessionId: this.sessionId,
            dataCollected: [
                'Anonymous session identifiers',
                'Page paths and titles',
                'Click events and interactions',
                'Performance timing data',
                'Device type (mobile/desktop)',
                'Browser family (aggregated)'
            ],
            dataNotCollected: [
                'Personal identification',
                'Email addresses',
                'Precise location',
                'Cross-site tracking',
                'Sensitive categories'
            ]
        };
    }

    // Core Tracking Methods
    // ====================

    trackPageView(path = null, title = null) {
        if (this.isOptedOut) { return; }

        const data = {
            path: path || window.location.pathname,
            title: title || document.title,
            referrer: this.getSanitizedReferrer(),
            timestamp: new Date().toISOString()
        };

        this.sendToAPI('/api/analytics/track-event/', {
            event_name: 'page_view',
            event_data: data
        });
    }

    trackEvent(eventName, eventData = {}) {
        if (this.isOptedOut) { return; }

        // Sanitize event data
        const sanitizedData = this.sanitizeEventData(eventData);

        this.sendToAPI('/api/analytics/track-event/', {
            event_name: eventName,
            event_data: {
                ...sanitizedData,
                timestamp: new Date().toISOString(),
                page_path: window.location.pathname
            }
        });
    }

    trackConversion(conversionType, conversionValue = null) {
        if (this.isOptedOut) { return; }

        this.sendToAPI('/api/analytics/track-conversion/', {
            conversion_type: conversionType,
            conversion_value: conversionValue
        });
    }

    // User Journey Tracking
    // ====================

    startJourney(journeyType) {
        if (this.isOptedOut) { return; }

        this.sendToAPI('/api/analytics/track-journey/', {
            step_name: `journey_start_${journeyType}`,
            journey_id: this.currentJourneyId
        }).then(response => {
            if (response.success) {
                this.currentJourneyId = response.journey_id;
            }
        });
    }

    trackJourneyStep(stepName) {
        if (this.isOptedOut) { return; }

        this.sendToAPI('/api/analytics/track-journey/', {
            step_name: stepName,
            journey_id: this.currentJourneyId
        });
    }

    // Conversion Funnel Tracking
    // =========================

    trackFunnelStep(funnelName, stepName, stepOrder) {
        if (this.isOptedOut) { return; }

        this.sendToAPI('/api/analytics/track-funnel/', {
            funnel_name: funnelName,
            step_name: stepName,
            step_order: stepOrder
        });

        // Also track as journey step
        this.trackJourneyStep(`${funnelName}_${stepName}`);
    }

    // Contact Form Funnel (4-step implementation)
    trackContactFunnel(step) {
        const funnelSteps = {
            'view_contact': { name: 'View Contact Page', order: 1 },
            'start_form': { name: 'Start Filling Form', order: 2 },
            'complete_form': { name: 'Complete Form', order: 3 },
            'submit_form': { name: 'Submit Form', order: 4 }
        };

        if (funnelSteps[step]) {
            this.trackFunnelStep('contact', funnelSteps[step].name, funnelSteps[step].order);

            // Track conversion on final step
            if (step === 'submit_form') {
                this.trackConversion('contact_form_submission');
            }
        }
    }

    // A/B Testing
    // ===========

    getABTestVariant(testName, variants = ['A', 'B']) {
        if (this.isOptedOut) {
            return variants[0]; // Return default variant
        }

        // Check if already assigned
        if (this.currentTest[testName]) {
            return this.currentTest[testName];
        }

        return this.sendToAPI('/api/analytics/get-ab-variant/', {
            test_name: testName,
            variants: variants
        }, 'GET').then(response => {
            if (response.success) {
                this.currentTest[testName] = response.variant;
                return response.variant;
            }
            return variants[0];
        });
    }

    trackABTestConversion(testName, conversionType = 'conversion') {
        if (this.isOptedOut) { return; }

        this.sendToAPI('/api/analytics/track-ab-conversion/', {
            test_name: testName,
            conversion_type: conversionType
        });
    }

    // CTA Button A/B Test Implementation
    async runCTAButtonTest() {
        try {
            const variant = await this.getABTestVariant('cta_button_style', ['default', 'bright', 'minimal']);

            // Apply variant styling
            const ctaButtons = document.querySelectorAll('.cta-button, .btn-primary');

            ctaButtons.forEach(button => {
                switch (variant) {
                    case 'bright':
                        button.classList.add('cta-variant-bright');
                        break;
                    case 'minimal':
                        button.classList.add('cta-variant-minimal');
                        break;
                    default:
                        button.classList.add('cta-variant-default');
                }

                // Track clicks on CTA buttons
                button.addEventListener('click', () => {
                    this.trackABTestConversion('cta_button_style', 'click');
                    this.trackEvent('cta_click', {
                        variant: variant,
                        button_text: button.textContent.trim(),
                        button_location: this.getElementLocation(button)
                    });
                });
            });

            return variant;

        } catch (error) {
            console.error('A/B test error:', error);
            return 'default';
        }
    }

    // Event Listeners Setup
    // ====================

    setupEventListeners() {
        // Track form interactions
        document.addEventListener('focusin', e => {
            if (e.target.matches('input, textarea, select')) {
                this.trackEvent('form_field_focus', {
                    field_type: e.target.type || e.target.tagName.toLowerCase(),
                    field_name: e.target.name || 'unnamed',
                    form_id: e.target.closest('form')?.id || 'no_form'
                });
            }
        });

        // Track form submissions
        document.addEventListener('submit', e => {
            const form = e.target;
            if (form.tagName === 'FORM') {
                this.trackEvent('form_submission', {
                    form_id: form.id || 'unnamed_form',
                    form_action: form.action || 'no_action',
                    field_count: form.querySelectorAll('input, textarea, select').length
                });

                // Contact form specific tracking
                if (form.id === 'contact-form' || form.classList.contains('contact-form')) {
                    this.trackContactFunnel('submit_form');
                }
            }
        });

        // Track important link clicks
        document.addEventListener('click', e => {
            const link = e.target.closest('a');
            if (link) {
                this.trackEvent('link_click', {
                    link_text: link.textContent.trim(),
                    link_href: link.href,
                    link_target: link.target || '_self',
                    is_external: !link.href.startsWith(window.location.origin)
                });
            }
        });

        // Track scroll depth
        let maxScroll = 0;
        window.addEventListener('scroll', this.throttle(() => {
            const scrollPercentage = Math.round((window.scrollY / (document.body.scrollHeight - window.innerHeight)) * 100);

            if (scrollPercentage > maxScroll && scrollPercentage % 25 === 0) {
                maxScroll = scrollPercentage;
                this.trackEvent('scroll_depth', {
                    percentage: scrollPercentage,
                    page_height: document.body.scrollHeight,
                    viewport_height: window.innerHeight
                });
            }
        }, 1000));

        // Track page visibility
        document.addEventListener('visibilitychange', () => {
            this.trackEvent('page_visibility', {
                visibility_state: document.visibilityState,
                hidden: document.hidden
            });
        });
    }

    // Performance Tracking
    // ===================

    trackPerformanceMetrics() {
        // Track Core Web Vitals using existing performance.min.js
        if (window.performanceTracker) {
            // Performance tracking is handled by the existing system
            return;
        }

        // Fallback performance tracking
        window.addEventListener('load', () => {
            setTimeout(() => {
                const navigation = performance.getEntriesByType('navigation')[0];

                if (navigation) {
                    this.trackEvent('performance_metrics', {
                        load_time: Math.round(navigation.loadEventEnd - navigation.fetchStart),
                        dom_content_loaded: Math.round(navigation.domContentLoadedEventEnd - navigation.fetchStart),
                        first_byte: Math.round(navigation.responseStart - navigation.fetchStart)
                    });
                }
            }, 1000);
        });
    }

    // Utility Methods
    // ==============

    getSanitizedReferrer() {
        const referrer = document.referrer;

        if (!referrer) { return 'direct'; }

        if (referrer.includes('google.com')) { return 'search'; }
        if (referrer.includes('facebook.com') || referrer.includes('twitter.com')) { return 'social'; }
        if (referrer.startsWith(window.location.origin)) { return 'internal'; }

        return 'external';
    }

    sanitizeEventData(data) {
        const sanitized = {};
        const sensitiveKeys = ['password', 'email', 'phone', 'credit', 'ssn'];

        for (const [key, value] of Object.entries(data)) {
            // Skip sensitive data
            if (sensitiveKeys.some(sensitive => key.toLowerCase().includes(sensitive))) {
                continue;
            }

            // Truncate long strings
            if (typeof value === 'string' && value.length > 200) {
                sanitized[key] = `${value.substring(0, 200)}...`;
            } else {
                sanitized[key] = value;
            }
        }

        return sanitized;
    }

    getElementLocation(element) {
        const rect = element.getBoundingClientRect();
        return {
            x: Math.round(rect.left),
            y: Math.round(rect.top),
            width: Math.round(rect.width),
            height: Math.round(rect.height)
        };
    }

    throttle(func, limit) {
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

    async sendToAPI(endpoint, data, method = 'POST') {
        try {
            const response = await fetch(endpoint, {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: method === 'POST' ? JSON.stringify(data) : null
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();

        } catch (error) {
            console.error('Analytics API error:', error);
            return { success: false, error: error.message };
        }
    }

    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
               document.querySelector('meta[name=csrf-token]')?.getAttribute('content') ||
               '';
    }

    // Public API for manual tracking
    // =============================

    // Contact form specific methods
    startContactForm() {
        this.trackContactFunnel('start_form');
    }

    completeContactForm() {
        this.trackContactFunnel('complete_form');
    }

    // Manual event tracking
    track(eventName, eventData = {}) {
        return this.trackEvent(eventName, eventData);
    }

    // Manual conversion tracking
    convert(conversionType, value = null) {
        return this.trackConversion(conversionType, value);
    }
}

// Global instance
window.privacyAnalytics = new PrivacyAnalytics();

// Expose GDPR compliance methods globally
window.analyticsOptOut = () => window.privacyAnalytics.optOut();
window.analyticsOptIn = () => window.privacyAnalytics.optIn();
window.setAnalyticsGDPRConsent = consent => window.privacyAnalytics.setGDPRConsent(consent);
window.getAnalyticsPrivacyInfo = () => window.privacyAnalytics.getPrivacyInfo();

// Initialize A/B tests
document.addEventListener('DOMContentLoaded', () => {
    // Run CTA button A/B test
    window.privacyAnalytics.runCTAButtonTest();

    // Track contact page visit
    if (window.location.pathname.includes('/contact')) {
        window.privacyAnalytics.trackContactFunnel('view_contact');
    }
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PrivacyAnalytics;
}
