/**
 * Privacy-Compliant Analytics Tracker
 * Tracks user behavior without collecting personal data
 */

class AnalyticsTracker {
    constructor() {
        this.journeyId = null;
        this.abTests = {};
        this.funnelData = {};
        this.initialized = false;
        this.csrfToken = this.getCsrfToken();
        this.init();
    }

    init() {
        if (this.initialized) return;
        
        // Track page view on load
        this.trackPageView();
        
        // Track user journey
        this.trackJourneyStep(this.getPageName());
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Load A/B test variants
        this.loadAbTests();
        
        this.initialized = true;
    }

    getCsrfToken() {
        // First try to get from meta tag (most reliable)
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        if (metaTag) {
            return metaTag.getAttribute('content');
        }
        
        // Then try to get from form input
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        if (token) return token.value;
        
        // Finally try to get from cookie
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return decodeURIComponent(value);
            }
        }
        return null;
    }

    async sendRequest(url, data = null, method = 'POST') {
        const options = {
            method: method,
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'same-origin'
        };

        if (this.csrfToken && method !== 'GET') {
            options.headers['X-CSRFToken'] = this.csrfToken;
        }

        if (data && method !== 'GET') {
            options.body = JSON.stringify(data);
        }

        try {
            const response = await fetch(url, options);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('Analytics request failed:', error);
            return null;
        }
    }

    trackPageView() {
        // Already handled by backend middleware, but can be called manually
        const pageData = {
            page_path: window.location.pathname,
            page_title: document.title,
            referrer: document.referrer
        };
        
        this.sendRequest('/api/analytics/event/', {
            event_name: 'page_view',
            event_data: pageData
        });
    }

    trackEvent(eventName, eventData = {}) {
        this.sendRequest('/api/analytics/event/', {
            event_name: eventName,
            event_data: eventData
        });
    }

    trackConversion(conversionType, conversionValue = null) {
        this.sendRequest('/api/analytics/conversion/', {
            conversion_type: conversionType,
            conversion_value: conversionValue
        });
        
        // Also track for A/B tests if applicable
        Object.keys(this.abTests).forEach(testName => {
            this.trackAbConversion(testName, conversionType);
        });
    }

    async trackJourneyStep(stepName) {
        const response = await this.sendRequest('/api/analytics/journey/', {
            step_name: stepName,
            journey_id: this.journeyId
        });
        
        if (response && response.journey_id) {
            this.journeyId = response.journey_id;
        }
    }

    async trackFunnelStep(funnelName, stepName, stepOrder) {
        await this.sendRequest('/api/analytics/funnel/', {
            funnel_name: funnelName,
            step_name: stepName,
            step_order: stepOrder
        });
        
        // Store funnel progress
        this.funnelData[funnelName] = {
            current_step: stepName,
            step_order: stepOrder
        };
    }

    async getAbVariant(testName, variants = null) {
        const params = new URLSearchParams({
            test_name: testName
        });
        
        if (variants) {
            variants.forEach(v => params.append('variants', v));
        }
        
        const response = await this.sendRequest(
            `/api/analytics/ab/variant/?${params.toString()}`,
            null,
            'GET'
        );
        
        if (response && response.variant) {
            this.abTests[testName] = response.variant;
            return response.variant;
        }
        
        return 'A'; // Default variant
    }

    async trackAbConversion(testName, conversionType = 'conversion') {
        if (!this.abTests[testName]) return;
        
        await this.sendRequest('/api/analytics/ab/conversion/', {
            test_name: testName,
            conversion_type: conversionType
        });
    }

    setupEventListeners() {
        // Track clicks on important elements
        document.addEventListener('click', (e) => {
            const target = e.target.closest('[data-track-click]');
            if (target) {
                const eventName = target.dataset.trackClick;
                const eventData = this.getDataAttributes(target, 'track');
                this.trackEvent(`click_${eventName}`, eventData);
            }
            
            // Track conversions
            const conversionTarget = e.target.closest('[data-track-conversion]');
            if (conversionTarget) {
                const conversionType = conversionTarget.dataset.trackConversion;
                const conversionValue = conversionTarget.dataset.conversionValue;
                this.trackConversion(conversionType, conversionValue);
            }
        });
        
        // Track form submissions
        document.addEventListener('submit', (e) => {
            const form = e.target;
            if (form.dataset.trackSubmit) {
                const eventName = form.dataset.trackSubmit;
                const eventData = this.getDataAttributes(form, 'track');
                this.trackEvent(`submit_${eventName}`, eventData);
            }
            
            // Track funnel progression
            if (form.dataset.funnel) {
                const funnelName = form.dataset.funnel;
                const stepName = form.dataset.funnelStep;
                const stepOrder = parseInt(form.dataset.funnelOrder || '1');
                this.trackFunnelStep(funnelName, stepName, stepOrder);
            }
        });
        
        // Track scroll depth
        let maxScrollDepth = 0;
        let scrollTimer = null;
        
        window.addEventListener('scroll', () => {
            clearTimeout(scrollTimer);
            scrollTimer = setTimeout(() => {
                const scrollPercent = Math.round(
                    (window.scrollY + window.innerHeight) / 
                    document.documentElement.scrollHeight * 100
                );
                
                if (scrollPercent > maxScrollDepth) {
                    maxScrollDepth = scrollPercent;
                    
                    // Track milestones
                    if (scrollPercent >= 25 && maxScrollDepth < 25) {
                        this.trackEvent('scroll_depth', { depth: 25 });
                    } else if (scrollPercent >= 50 && maxScrollDepth < 50) {
                        this.trackEvent('scroll_depth', { depth: 50 });
                    } else if (scrollPercent >= 75 && maxScrollDepth < 75) {
                        this.trackEvent('scroll_depth', { depth: 75 });
                    } else if (scrollPercent >= 90 && maxScrollDepth < 90) {
                        this.trackEvent('scroll_depth', { depth: 90 });
                    }
                }
            }, 500);
        });
        
        // Track time on page
        let startTime = Date.now();
        window.addEventListener('beforeunload', () => {
            const timeOnPage = Math.round((Date.now() - startTime) / 1000);
            if (timeOnPage > 3) { // Only track if more than 3 seconds
                // Use FormData to send CSRF token with sendBeacon
                const formData = new FormData();
                formData.append('csrfmiddlewaretoken', this.csrfToken);
                formData.append('data', JSON.stringify({
                    event_name: 'time_on_page',
                    event_data: { 
                        seconds: timeOnPage,
                        page: window.location.pathname
                    }
                }));
                navigator.sendBeacon('/api/analytics/event/', formData);
            }
        });
    }

    getDataAttributes(element, prefix) {
        const data = {};
        for (let attr of element.attributes) {
            if (attr.name.startsWith(`data-${prefix}-`) && 
                !attr.name.endsWith('-click') && 
                !attr.name.endsWith('-submit') &&
                !attr.name.endsWith('-conversion')) {
                const key = attr.name.replace(`data-${prefix}-`, '').replace(/-/g, '_');
                data[key] = attr.value;
            }
        }
        return data;
    }

    getPageName() {
        const path = window.location.pathname;
        if (path === '/') return 'home';
        
        const segments = path.split('/').filter(s => s);
        return segments.join('_') || 'unknown';
    }

    async loadAbTests() {
        // Load any A/B tests defined in the page
        const testElements = document.querySelectorAll('[data-ab-test]');
        for (let element of testElements) {
            const testName = element.dataset.abTest;
            const variants = element.dataset.abVariants ? 
                element.dataset.abVariants.split(',') : null;
            
            const variant = await this.getAbVariant(testName, variants);
            
            // Apply variant
            element.classList.add(`variant-${variant.toLowerCase()}`);
            element.dataset.abVariant = variant;
            
            // Show/hide elements based on variant
            document.querySelectorAll(`[data-ab-show="${testName}"]`).forEach(el => {
                if (el.dataset.abVariant === variant) {
                    el.style.display = '';
                } else {
                    el.style.display = 'none';
                }
            });
        }
    }

    // Funnel tracking helpers
    startSignupFunnel() {
        this.trackFunnelStep('signup', 'view_form', 1);
    }

    continueSignupFunnel(step) {
        const steps = {
            'email_entered': 2,
            'details_filled': 3,
            'submitted': 4
        };
        
        if (steps[step]) {
            this.trackFunnelStep('signup', step, steps[step]);
        }
    }

    startContactFunnel() {
        this.trackFunnelStep('contact', 'view_form', 1);
    }

    continueContactFunnel(step) {
        const steps = {
            'form_started': 2,
            'form_filled': 3,
            'submitted': 4
        };
        
        if (steps[step]) {
            this.trackFunnelStep('contact', step, steps[step]);
        }
    }
}

// Initialize tracker
let analyticsTracker;
document.addEventListener('DOMContentLoaded', () => {
    // Only initialize if user has consented to analytics
    if (!document.cookie.includes('analytics_opt_out=true')) {
        analyticsTracker = new AnalyticsTracker();
        
        // Expose to global scope for manual tracking
        window.analyticsTracker = analyticsTracker;
    }
});

// Privacy-compliant opt-out
function optOutAnalytics() {
    document.cookie = 'analytics_opt_out=true; max-age=31536000; path=/';
    if (window.analyticsTracker) {
        window.analyticsTracker = null;
    }
    console.log('Analytics tracking disabled');
}

function optInAnalytics() {
    document.cookie = 'analytics_opt_out=; max-age=0; path=/';
    if (!window.analyticsTracker) {
        window.analyticsTracker = new AnalyticsTracker();
    }
    console.log('Analytics tracking enabled');
}