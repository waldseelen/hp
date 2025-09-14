/**
 * COMPREHENSIVE PERFORMANCE MONITORING
 * Monitors Core Web Vitals, CSS load times, and render performance
 */

class PerformanceMonitor {
    constructor() {
        // Existing FPS monitoring
        this.frameCount = 0;
        this.fps = 60;
        this.lastTime = 0;
        
        // Core Web Vitals
        this.metrics = {};
        this.observers = [];
        this.isEnabled = true;
        
        // Initialize comprehensive monitoring
        this.initCoreWebVitals();
        this.frameDropThreshold = 55; // Below 55fps, consider optimization
        this.isMonitoring = false;
        this.animationElements = [];
        
        this.init();
    }

    init() {
        this.collectAnimatedElements();
        this.setupIntersectionObserver();
        this.monitorPerformance();
        this.bindEvents();
    }

    collectAnimatedElements() {
        // Collect all elements with animation classes
        const selectors = [
            '[class*="animate-"]',
            '.starfield',
            '.loading-spinner',
            '.btn:hover',
            '.card:hover',
            '.float-animation'
        ];
        
        this.animationElements = document.querySelectorAll(selectors.join(', '));
        
        // Apply GPU acceleration to all animated elements
        this.animationElements.forEach(element => {
            element.style.willChange = 'transform, opacity';
            element.style.transform = 'translate3d(0, 0, 0)';
            element.style.backfaceVisibility = 'hidden';
        });
    }

    monitorPerformance() {
        if (!this.isMonitoring) {
            this.isMonitoring = true;
            this.measureFPS();
        }
    }

    measureFPS() {
        const measure = (currentTime) => {
            if (this.lastTime) {
                const delta = currentTime - this.lastTime;
                this.fps = Math.round(1000 / delta);
                this.frameCount++;
                
                // Check every 60 frames (roughly 1 second at 60fps)
                if (this.frameCount % 60 === 0) {
                    this.checkPerformanceThreshold();
                }
            }
            
            this.lastTime = currentTime;
            
            if (this.isMonitoring) {
                requestAnimationFrame(measure);
            }
        };
        
        requestAnimationFrame(measure);
    }

    checkPerformanceThreshold() {
        if (this.fps < this.frameDropThreshold) {
            console.warn(`Performance drop detected: ${this.fps}fps`);
            this.optimizeAnimations();
        }
    }

    optimizeAnimations() {
        // Pause non-critical animations during performance drops
        const nonCritical = document.querySelectorAll('.animate-float, .animate-pulse-slow, .starfield');
        
        nonCritical.forEach(element => {
            if (element.style.animationPlayState !== 'paused') {
                element.style.animationPlayState = 'paused';
                
                // Resume after a delay
                setTimeout(() => {
                    element.style.animationPlayState = 'running';
                }, 2000);
            }
        });
    }

    setupIntersectionObserver() {
        if (!('IntersectionObserver' in window)) return;

        const options = {
            root: null,
            rootMargin: '10px',
            threshold: 0.1
        };

        this.observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                const element = entry.target;
                
                if (entry.isIntersecting) {
                    // Element is visible, allow animations
                    element.style.willChange = 'transform, opacity';
                    element.classList.remove('animations-paused');
                } else {
                    // Element not visible, pause animations to save resources
                    element.style.willChange = 'auto';
                    element.classList.add('animations-paused');
                }
            });
        }, options);

        // Observe animated elements
        this.animationElements.forEach(element => {
            this.observer.observe(element);
        });
    }

    bindEvents() {
        // Reduce animations when battery is low
        if ('getBattery' in navigator) {
            navigator.getBattery().then(battery => {
                const handleBatteryChange = () => {
                    if (battery.level < 0.2) { // Below 20%
                        document.body.classList.add('low-battery');
                        this.reduceMotionForBattery();
                    } else {
                        document.body.classList.remove('low-battery');
                    }
                };
                
                battery.addEventListener('levelchange', handleBatteryChange);
                handleBatteryChange();
            });
        }

        // Pause animations during page visibility changes
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.pauseAllAnimations();
            } else {
                this.resumeAllAnimations();
            }
        });

        // Monitor CPU intensive operations
        this.detectHighCPUUsage();
    }

    reduceMotionForBattery() {
        // Reduce to essential animations only
        const nonEssential = document.querySelectorAll(
            '.animate-float, .animate-pulse-slow, .animate-heartbeat, .starfield'
        );
        
        nonEssential.forEach(element => {
            element.style.animationDuration = '0.01ms';
        });
    }

    pauseAllAnimations() {
        this.animationElements.forEach(element => {
            element.style.animationPlayState = 'paused';
        });
    }

    resumeAllAnimations() {
        this.animationElements.forEach(element => {
            element.style.animationPlayState = 'running';
        });
    }

    detectHighCPUUsage() {
        let highCPUCounter = 0;
        
        const checkCPU = () => {
            const start = performance.now();
            
            // Simulate work to detect blocking
            setTimeout(() => {
                const end = performance.now();
                const delay = end - start;
                
                // If setTimeout is delayed by more than 50ms, CPU might be busy
                if (delay > 50) {
                    highCPUCounter++;
                    
                    if (highCPUCounter > 3) {
                        this.optimizeForHighCPU();
                        highCPUCounter = 0;
                    }
                } else {
                    highCPUCounter = Math.max(0, highCPUCounter - 1);
                }
                
                setTimeout(checkCPU, 1000);
            }, 16); // ~60fps check
        };
        
        checkCPU();
    }

    optimizeForHighCPU() {
        console.info('High CPU usage detected, optimizing animations...');
        
        // Simplify complex animations
        const complex = document.querySelectorAll('.starfield, .glow-on-hover');
        complex.forEach(element => {
            element.classList.add('reduced-motion');
        });
    }

    // Public API
    getFPS() {
        return this.fps;
    }

    stopMonitoring() {
        this.isMonitoring = false;
        if (this.observer) {
            this.observer.disconnect();
        }
    }
}

// CSS classes for performance optimization
const performanceCSS = `
    .animations-paused * {
        animation-play-state: paused !important;
    }
    
    .low-battery .animate-float,
    .low-battery .animate-pulse-slow,
    .low-battery .starfield {
        animation: none !important;
    }
    
    .reduced-motion .starfield {
        animation-duration: 60s !important;
        opacity: 0.3 !important;
    }
    
    .reduced-motion .glow-on-hover::before {
        animation: none !important;
    }
    
    /* Performance-critical optimizations */
    @media (max-width: 768px) {
        .starfield {
            display: none; /* Hide complex animations on mobile */
        }
        
        .animate-float,
        .animate-pulse-slow {
            animation: none !important;
        }
    }
    
    /* High refresh rate support */
    @media (min-resolution: 120dpi) {
        .animate-slide-up,
        .animate-fade-in {
            animation-duration: 0.4s !important;
        }
    }
`;

// Inject performance CSS
const styleSheet = document.createElement('style');
styleSheet.textContent = performanceCSS;
document.head.appendChild(styleSheet);

// Initialize performance monitoring when DOM is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.performanceMonitor = new PerformanceMonitor();
    });
} else {
    window.performanceMonitor = new PerformanceMonitor();
}

    // ====================================
    // CORE WEB VITALS MONITORING
    // ====================================
    
    initCoreWebVitals() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.startCoreWebVitalsMonitoring());
        } else {
            this.startCoreWebVitalsMonitoring();
        }
    }
    
    startCoreWebVitalsMonitoring() {
        console.log('🚀 Core Web Vitals monitoring started');
        
        // Largest Contentful Paint (LCP)
        this.observeLCP();
        
        // First Input Delay (FID)
        this.observeFID();
        
        // Cumulative Layout Shift (CLS)
        this.observeCLS();
        
        // First Contentful Paint (FCP)
        this.observeFCP();
        
        // Time to First Byte (TTFB)
        this.observeTTFB();
        
        // CSS Load Time Monitoring
        this.monitorCSSLoadTimes();
        
        // Schedule comprehensive report
        this.scheduleMetricsReport();
    }
    
    observeLCP() {
        if ('PerformanceObserver' in window) {
            const observer = new PerformanceObserver((entryList) => {
                const entries = entryList.getEntries();
                const lastEntry = entries[entries.length - 1];
                
                this.metrics.lcp = {
                    value: lastEntry.startTime,
                    rating: this.getLCPRating(lastEntry.startTime),
                    element: lastEntry.element?.tagName || 'unknown',
                    timestamp: Date.now()
                };
                
                console.log(`📊 LCP: ${lastEntry.startTime.toFixed(2)}ms (${this.metrics.lcp.rating})`);
                this.reportMetric('lcp', this.metrics.lcp);
            });
            
            observer.observe({ type: 'largest-contentful-paint', buffered: true });
            this.observers.push(observer);
        }
    }
    
    observeFID() {
        if ('PerformanceObserver' in window) {
            const observer = new PerformanceObserver((entryList) => {
                const firstEntry = entryList.getEntries()[0];
                const fidValue = firstEntry.processingStart - firstEntry.startTime;
                
                this.metrics.fid = {
                    value: fidValue,
                    rating: this.getFIDRating(fidValue),
                    timestamp: Date.now()
                };
                
                console.log(`📊 FID: ${fidValue.toFixed(2)}ms (${this.metrics.fid.rating})`);
                this.reportMetric('fid', this.metrics.fid);
            });
            
            observer.observe({ type: 'first-input', buffered: true });
            this.observers.push(observer);
        }
    }
    
    observeCLS() {
        if ('PerformanceObserver' in window) {
            let clsValue = 0;
            
            const observer = new PerformanceObserver((entryList) => {
                for (const entry of entryList.getEntries()) {
                    if (!entry.hadRecentInput) {
                        clsValue += entry.value;
                    }
                }
                
                this.metrics.cls = {
                    value: clsValue,
                    rating: this.getCLSRating(clsValue),
                    timestamp: Date.now()
                };
                
                console.log(`📊 CLS: ${clsValue.toFixed(4)} (${this.metrics.cls.rating})`);
                this.reportMetric('cls', this.metrics.cls);
            });
            
            observer.observe({ type: 'layout-shift', buffered: true });
            this.observers.push(observer);
        }
    }
    
    observeFCP() {
        if ('PerformanceObserver' in window) {
            const observer = new PerformanceObserver((entryList) => {
                const entries = entryList.getEntries();
                const fcpEntry = entries.find(entry => entry.name === 'first-contentful-paint');
                
                if (fcpEntry) {
                    this.metrics.fcp = {
                        value: fcpEntry.startTime,
                        rating: this.getFCPRating(fcpEntry.startTime),
                        timestamp: Date.now()
                    };
                    
                    console.log(`📊 FCP: ${fcpEntry.startTime.toFixed(2)}ms (${this.metrics.fcp.rating})`);
                    this.reportMetric('fcp', this.metrics.fcp);
                }
            });
            
            observer.observe({ type: 'paint', buffered: true });
            this.observers.push(observer);
        }
    }
    
    observeTTFB() {
        const navigation = performance.getEntriesByType('navigation')[0];
        if (navigation) {
            const ttfb = navigation.responseStart - navigation.requestStart;
            
            this.metrics.ttfb = {
                value: ttfb,
                rating: this.getTTFBRating(ttfb),
                timestamp: Date.now()
            };
            
            console.log(`📊 TTFB: ${ttfb.toFixed(2)}ms (${this.metrics.ttfb.rating})`);
            this.reportMetric('ttfb', this.metrics.ttfb);
        }
    }
    
    monitorCSSLoadTimes() {
        const resourceObserver = new PerformanceObserver((entryList) => {
            const cssResources = entryList.getEntries().filter(entry => 
                entry.initiatorType === 'link' && 
                entry.name.includes('.css')
            );
            
            cssResources.forEach(resource => {
                const loadTime = resource.responseEnd - resource.startTime;
                const fileName = resource.name.split('/').pop();
                
                this.metrics.css = this.metrics.css || {};
                this.metrics.css[fileName] = {
                    loadTime: loadTime,
                    size: resource.transferSize || 0,
                    cached: resource.transferSize === 0,
                    timestamp: Date.now()
                };
                
                console.log(`🎨 CSS Load: ${fileName} - ${loadTime.toFixed(2)}ms (${this.formatBytes(resource.transferSize || 0)})`);
                this.reportMetric('css-load', { file: fileName, ...this.metrics.css[fileName] });
            });
        });
        
        resourceObserver.observe({ type: 'resource', buffered: true });
        this.observers.push(resourceObserver);
    }
    
    // Rating functions for Web Vitals
    getLCPRating(value) {
        if (value <= 2500) return 'good';
        if (value <= 4000) return 'needs-improvement';
        return 'poor';
    }
    
    getFIDRating(value) {
        if (value <= 100) return 'good';
        if (value <= 300) return 'needs-improvement';
        return 'poor';
    }
    
    getCLSRating(value) {
        if (value <= 0.1) return 'good';
        if (value <= 0.25) return 'needs-improvement';
        return 'poor';
    }
    
    getFCPRating(value) {
        if (value <= 1800) return 'good';
        if (value <= 3000) return 'needs-improvement';
        return 'poor';
    }
    
    getTTFBRating(value) {
        if (value <= 800) return 'good';
        if (value <= 1800) return 'needs-improvement';
        return 'poor';
    }
    
    formatBytes(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    reportMetric(name, data) {
        // Send to console in development
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            console.log(`📊 ${name}:`, data);
        }
        
        // Send to Google Analytics if available
        if (window.gtag) {
            window.gtag('event', 'web_vital', {
                custom_parameter: name,
                value: data.value || data,
                event_category: 'Performance'
            });
        }
        
        // Trigger custom event
        document.dispatchEvent(new CustomEvent('performance-metric', {
            detail: { name, data }
        }));
    }
    
    scheduleMetricsReport() {
        // Send comprehensive report after page load
        setTimeout(() => {
            const report = {
                coreWebVitals: {
                    lcp: this.metrics.lcp,
                    fid: this.metrics.fid,
                    cls: this.metrics.cls,
                    fcp: this.metrics.fcp,
                    ttfb: this.metrics.ttfb
                },
                cssPerformance: this.metrics.css,
                timestamp: Date.now(),
                url: window.location.href
            };
            
            console.log('📊 Performance Report:', report);
            this.reportMetric('performance-report', report);
        }, 10000); // 10 seconds after load
    }
    
    getMetrics() {
        return this.metrics;
    }
}

// Export for debugging
window.PerformanceMonitor = PerformanceMonitor;