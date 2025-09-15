/**
 * Performance Monitoring Module
 * Advanced performance optimization and monitoring for the portfolio site
 * 
 * Features:
 * - Core Web Vitals monitoring (LCP, FID, CLS)
 * - Resource loading optimization
 * - Image lazy loading with intersection observer
 * - Network connection monitoring
 * - Cache management and optimization
 * - Performance analytics and reporting
 * - Memory usage monitoring
 * - Bundle size analysis
 * - Service Worker integration
 */

class PerformanceMonitor {
    constructor() {
        this.metrics = {
            lcp: null,
            fid: null,
            cls: null,
            fcp: null,
            ttfb: null,
            domContentLoaded: null,
            loadComplete: null
        };
        
        this.observers = new Map();
        this.networkInfo = null;
        this.isRecording = true;
        this.reportingEndpoint = '/api/performance/';
        
        this.init();
    }
    
    init() {
        // Initialize performance monitoring
        this.setupCoreWebVitals();
        this.setupResourceMonitoring();
        this.setupNetworkMonitoring();
        this.setupMemoryMonitoring();
        this.setupServiceWorkerIntegration();
        
        // Start monitoring when page loads
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.onDOMReady());
        } else {
            this.onDOMReady();
        }
        
        // Setup reporting
        this.setupReporting();
        
        console.log('🚀 Performance Monitor initialized');
    }
    
    setupCoreWebVitals() {
        // Largest Contentful Paint (LCP)
        this.observeLCP();
        
        // First Input Delay (FID)
        this.observeFID();
        
        // Cumulative Layout Shift (CLS)
        this.observeCLS();
        
        // First Contentful Paint (FCP)
        this.observeFCP();
        
        // Time to First Byte (TTFB)
        this.measureTTFB();
    }
    
    observeLCP() {
        if ('PerformanceObserver' in window) {
            try {
                const observer = new PerformanceObserver((list) => {
                    const entries = list.getEntries();
                    const lastEntry = entries[entries.length - 1];
                    this.metrics.lcp = Math.round(lastEntry.startTime);
                    
                    // Report LCP if it's significant
                    if (this.metrics.lcp > 2500) {
                        this.reportMetric('lcp_slow', this.metrics.lcp);
                    }
                });
                
                observer.observe({ type: 'largest-contentful-paint', buffered: true });
                this.observers.set('lcp', observer);
            } catch (e) {
                console.warn('LCP measurement not supported:', e);
            }
        }
    }
    
    observeFID() {
        if ('PerformanceObserver' in window) {
            try {
                const observer = new PerformanceObserver((list) => {
                    const entries = list.getEntries();
                    entries.forEach((entry) => {
                        this.metrics.fid = Math.round(entry.processingStart - entry.startTime);
                        
                        // Report slow FID
                        if (this.metrics.fid > 100) {
                            this.reportMetric('fid_slow', this.metrics.fid);
                        }
                    });
                });
                
                observer.observe({ type: 'first-input', buffered: true });
                this.observers.set('fid', observer);
            } catch (e) {
                console.warn('FID measurement not supported:', e);
            }
        }
    }
    
    observeCLS() {
        if ('PerformanceObserver' in window) {
            try {
                let clsValue = 0;
                let clsEntries = [];
                
                const observer = new PerformanceObserver((list) => {
                    const entries = list.getEntries();
                    entries.forEach((entry) => {
                        if (!entry.hadRecentInput) {
                            clsEntries.push(entry);
                            clsValue += entry.value;
                        }
                    });
                    
                    this.metrics.cls = Math.round(clsValue * 1000) / 1000;
                    
                    // Report high CLS
                    if (this.metrics.cls > 0.1) {
                        this.reportMetric('cls_high', this.metrics.cls);
                        this.analyzeCLSCauses(clsEntries);
                    }
                });
                
                observer.observe({ type: 'layout-shift', buffered: true });
                this.observers.set('cls', observer);
            } catch (e) {
                console.warn('CLS measurement not supported:', e);
            }
        }
    }
    
    observeFCP() {
        if ('PerformanceObserver' in window) {
            try {
                const observer = new PerformanceObserver((list) => {
                    const entries = list.getEntries();
                    const lastEntry = entries[entries.length - 1];
                    this.metrics.fcp = Math.round(lastEntry.startTime);
                });
                
                observer.observe({ type: 'paint', buffered: true });
                this.observers.set('fcp', observer);
            } catch (e) {
                console.warn('FCP measurement not supported:', e);
            }
        }
    }
    
    measureTTFB() {
        if ('performance' in window && 'getEntriesByType' in performance) {
            const navigation = performance.getEntriesByType('navigation')[0];
            if (navigation) {
                this.metrics.ttfb = Math.round(navigation.responseStart - navigation.requestStart);
                
                // Report slow TTFB
                if (this.metrics.ttfb > 600) {
                    this.reportMetric('ttfb_slow', this.metrics.ttfb);
                }
            }
        }
    }
    
    setupResourceMonitoring() {
        if ('PerformanceObserver' in window) {
            try {
                const observer = new PerformanceObserver((list) => {
                    const entries = list.getEntries();
                    entries.forEach((entry) => {
                        this.analyzeResourcePerformance(entry);
                    });
                });
                
                observer.observe({ type: 'resource', buffered: true });
                this.observers.set('resource', observer);
            } catch (e) {
                console.warn('Resource monitoring not supported:', e);
            }
        }
    }
    
    analyzeResourcePerformance(entry) {
        const duration = entry.responseEnd - entry.requestStart;
        const size = entry.transferSize || entry.decodedBodySize || 0;
        
        // Analyze different resource types
        if (entry.initiatorType === 'img' && duration > 2000) {
            this.reportMetric('slow_image', {
                url: entry.name,
                duration: Math.round(duration),
                size: size
            });
        }
        
        if (entry.initiatorType === 'script' && duration > 3000) {
            this.reportMetric('slow_script', {
                url: entry.name,
                duration: Math.round(duration),
                size: size
            });
        }
        
        if (entry.initiatorType === 'link' && entry.name.includes('.css') && duration > 2000) {
            this.reportMetric('slow_css', {
                url: entry.name,
                duration: Math.round(duration),
                size: size
            });
        }
        
        // Monitor large resources
        if (size > 1024 * 1024) { // 1MB
            this.reportMetric('large_resource', {
                url: entry.name,
                size: size,
                type: entry.initiatorType
            });
        }
    }
    
    setupNetworkMonitoring() {
        // Monitor network connection
        if ('connection' in navigator) {
            this.networkInfo = {
                effectiveType: navigator.connection.effectiveType,
                downlink: navigator.connection.downlink,
                rtt: navigator.connection.rtt,
                saveData: navigator.connection.saveData
            };
            
            // Listen for network changes
            navigator.connection.addEventListener('change', () => {
                this.onNetworkChange();
            });
            
            // Adapt based on connection quality
            this.adaptToConnection();
        }
        
        // Monitor online/offline status
        window.addEventListener('online', () => this.onNetworkOnline());
        window.addEventListener('offline', () => this.onNetworkOffline());
    }
    
    onNetworkChange() {
        const newInfo = {
            effectiveType: navigator.connection.effectiveType,
            downlink: navigator.connection.downlink,
            rtt: navigator.connection.rtt,
            saveData: navigator.connection.saveData
        };
        
        // Report significant connection changes
        if (this.networkInfo.effectiveType !== newInfo.effectiveType) {
            this.reportMetric('network_change', {
                from: this.networkInfo.effectiveType,
                to: newInfo.effectiveType
            });
        }
        
        this.networkInfo = newInfo;
        this.adaptToConnection();
    }
    
    adaptToConnection() {
        if (!this.networkInfo) return;
        
        const { effectiveType, saveData } = this.networkInfo;
        
        // Reduce quality for slow connections
        if (effectiveType === '2g' || effectiveType === 'slow-2g' || saveData) {
            this.enableDataSaverMode();
        } else if (effectiveType === '4g') {
            this.enableHighQualityMode();
        }
    }
    
    enableDataSaverMode() {
        // Disable non-essential animations
        document.body.classList.add('reduce-motion');
        
        // Reduce image quality
        const images = document.querySelectorAll('img[data-src]');
        images.forEach(img => {
            if (img.dataset.srcLow) {
                img.dataset.src = img.dataset.srcLow;
            }
        });
        
        // Disable auto-playing content
        const videos = document.querySelectorAll('video[autoplay]');
        videos.forEach(video => {
            video.removeAttribute('autoplay');
            video.pause();
        });
        
        this.reportMetric('data_saver_enabled', true);
    }
    
    enableHighQualityMode() {
        // Enable high quality features
        document.body.classList.remove('reduce-motion');
        
        // Use high quality images
        const images = document.querySelectorAll('img[data-src]');
        images.forEach(img => {
            if (img.dataset.srcHigh) {
                img.dataset.src = img.dataset.srcHigh;
            }
        });
        
        // Enable enhanced animations
        document.body.classList.add('enhanced-animations');
    }
    
    onNetworkOnline() {
        this.reportMetric('network_online', Date.now());
        
        // Sync any pending data
        if ('serviceWorker' in navigator && navigator.serviceWorker.controller) {
            navigator.serviceWorker.controller.postMessage({
                type: 'SYNC_WHEN_ONLINE'
            });
        }
    }
    
    onNetworkOffline() {
        this.reportMetric('network_offline', Date.now());
        
        // Show offline indicator
        this.showOfflineIndicator();
    }
    
    setupMemoryMonitoring() {
        if ('memory' in performance) {
            // Monitor memory usage periodically
            setInterval(() => {
                const memory = performance.memory;
                const memoryInfo = {
                    used: Math.round(memory.usedJSHeapSize / 1024 / 1024),
                    total: Math.round(memory.totalJSHeapSize / 1024 / 1024),
                    limit: Math.round(memory.jsHeapSizeLimit / 1024 / 1024)
                };
                
                // Warn about high memory usage
                const usage = memoryInfo.used / memoryInfo.limit;
                if (usage > 0.8) {
                    this.reportMetric('high_memory_usage', memoryInfo);
                    this.triggerMemoryCleanup();
                }
            }, 30000); // Check every 30 seconds
        }
    }
    
    triggerMemoryCleanup() {
        // Clear unnecessary observers
        this.observers.forEach((observer, key) => {
            if (key !== 'lcp' && key !== 'fid' && key !== 'cls') {
                observer.disconnect();
                this.observers.delete(key);
            }
        });
        
        // Clear caches if possible
        if ('caches' in window) {
            caches.keys().then(cacheNames => {
                cacheNames.forEach(cacheName => {
                    if (cacheName.includes('old') || cacheName.includes('temp')) {
                        caches.delete(cacheName);
                    }
                });
            });
        }
        
        // Force garbage collection if available
        if (window.gc) {
            window.gc();
        }
    }
    
    setupServiceWorkerIntegration() {
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.addEventListener('message', (event) => {
                const { type, data } = event.data;
                
                switch (type) {
                    case 'CACHE_PERFORMANCE':
                        this.reportMetric('cache_hit_rate', data);
                        break;
                    case 'OFFLINE_FALLBACK':
                        this.reportMetric('offline_fallback_used', data);
                        break;
                    case 'UPDATE_AVAILABLE':
                        this.handleServiceWorkerUpdate();
                        break;
                }
            });
        }
    }
    
    handleServiceWorkerUpdate() {
        // Show update notification
        if (window.showToast) {
            window.showToast(
                'A new version is available',
                'info',
                {
                    autoDismiss: false,
                    actions: [{
                        text: 'Reload',
                        handler: () => window.location.reload()
                    }, {
                        text: 'Later',
                        handler: () => {}
                    }]
                }
            );
        }
    }
    
    onDOMReady() {
        // Measure DOM metrics
        this.metrics.domContentLoaded = performance.now();
        
        // Setup intersection observers for lazy loading
        this.setupLazyLoading();
        
        // Initialize critical performance optimizations
        this.optimizeCriticalResources();
        
        // Start monitoring user interactions
        this.setupInteractionMonitoring();
    }
    
    setupLazyLoading() {
        // Global guard to prevent duplicate lazy loading initialization
        if (window.__imgLazyOwner) return;
        window.__imgLazyOwner = 'performance';
        
        if ('IntersectionObserver' in window) {
            // Lazy load images
            const imageObserver = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        this.loadImage(img);
                        observer.unobserve(img);
                    }
                });
            }, {
                rootMargin: '50px 0px',
                threshold: 0.1
            });
            
            // Observe all images with data-src
            document.querySelectorAll('img[data-src]').forEach(img => {
                img.classList.add('lazy');
                imageObserver.observe(img);
            });
            
            // Lazy load other content
            const contentObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const element = entry.target;
                        this.loadDeferredContent(element);
                        contentObserver.unobserve(element);
                    }
                });
            }, {
                rootMargin: '100px 0px',
                threshold: 0.1
            });
            
            document.querySelectorAll('[data-lazy-content]').forEach(element => {
                contentObserver.observe(element);
            });
        }
    }
    
    loadImage(img) {
        const startTime = performance.now();
        
        // Choose appropriate image source based on device capabilities
        let src = img.dataset.src;
        
        if (this.networkInfo?.saveData || this.networkInfo?.effectiveType === '2g') {
            src = img.dataset.srcLow || src;
        } else if (window.devicePixelRatio > 2) {
            src = img.dataset.srcHigh || src;
        }
        
        // Create a new image element to preload
        const newImg = new Image();
        
        newImg.onload = () => {
            const loadTime = performance.now() - startTime;
            
            img.src = src;
            img.classList.remove('lazy');
            img.classList.add('loaded');
            
            // Store original HTML for consistency with main.js loading functions
            if (!img.getAttribute('data-original-html')) {
                img.setAttribute('data-original-html', img.outerHTML);
            }
            
            // Report image load performance
            if (loadTime > 2000) {
                this.reportMetric('slow_image_load', {
                    src: src,
                    loadTime: Math.round(loadTime)
                });
            }
        };
        
        newImg.onerror = () => {
            img.classList.add('error');
            img.src = img.dataset.fallback || '/static/images/placeholder.svg';
            
            this.reportMetric('image_load_error', {
                src: src,
                fallback: img.dataset.fallback
            });
        };
        
        newImg.src = src;
    }
    
    loadDeferredContent(element) {
        const contentType = element.dataset.lazyContent;
        
        switch (contentType) {
            case 'widget':
                this.loadWidget(element);
                break;
            case 'chart':
                this.loadChart(element);
                break;
            case 'social':
                this.loadSocialEmbed(element);
                break;
            default:
                this.loadGenericContent(element);
        }
    }
    
    optimizeCriticalResources() {
        // Preload critical resources
        this.preloadCriticalResources();
        
        // Optimize font loading
        this.optimizeFonts();
        
        // Optimize third-party scripts
        this.optimizeThirdPartyScripts();
    }
    
    preloadCriticalResources() {
        const criticalResources = [
            { href: '/static/css/components.css', as: 'style' },
            { href: '/static/js/ui-enhancements.js', as: 'script' },
            // Add more critical resources as needed
        ];
        
        criticalResources.forEach(resource => {
            const link = document.createElement('link');
            link.rel = 'preload';
            link.href = resource.href;
            link.as = resource.as;
            
            if (resource.as === 'script') {
                link.crossOrigin = 'anonymous';
            }
            
            document.head.appendChild(link);
        });
    }
    
    optimizeFonts() {
        // Use font-display: swap for web fonts
        const fontFaces = document.querySelectorAll('@font-face, link[rel="stylesheet"][href*="fonts"]');
        
        // Preload critical fonts
        const criticalFonts = [
            '/static/fonts/primary-font.woff2',
            // Add other critical fonts
        ];
        
        criticalFonts.forEach(fontUrl => {
            const link = document.createElement('link');
            link.rel = 'preload';
            link.href = fontUrl;
            link.as = 'font';
            link.type = 'font/woff2';
            link.crossOrigin = 'anonymous';
            document.head.appendChild(link);
        });
    }
    
    optimizeThirdPartyScripts() {
        // Load third-party scripts with optimal timing
        const thirdPartyScripts = document.querySelectorAll('script[data-defer]');
        
        thirdPartyScripts.forEach(script => {
            if (script.dataset.defer === 'interaction') {
                this.loadOnInteraction(script);
            } else if (script.dataset.defer === 'idle') {
                this.loadOnIdle(script);
            }
        });
    }
    
    loadOnInteraction(script) {
        const events = ['mousedown', 'touchstart', 'keydown', 'scroll'];
        
        const loadScript = () => {
            script.src = script.dataset.src;
            events.forEach(event => {
                document.removeEventListener(event, loadScript, { passive: true });
            });
        };
        
        events.forEach(event => {
            document.addEventListener(event, loadScript, { passive: true });
        });
    }
    
    loadOnIdle(script) {
        if ('requestIdleCallback' in window) {
            requestIdleCallback(() => {
                script.src = script.dataset.src;
            });
        } else {
            setTimeout(() => {
                script.src = script.dataset.src;
            }, 2000);
        }
    }
    
    setupInteractionMonitoring() {
        // Monitor user interactions for performance impact
        const interactionEvents = ['click', 'scroll', 'keydown', 'mousemove'];
        
        interactionEvents.forEach(eventType => {
            document.addEventListener(eventType, (event) => {
                this.measureInteractionPerformance(event);
            }, { passive: true });
        });
    }
    
    measureInteractionPerformance(event) {
        const startTime = performance.now();
        
        // Measure interaction response time
        requestAnimationFrame(() => {
            const responseTime = performance.now() - startTime;
            
            if (responseTime > 100) {
                this.reportMetric('slow_interaction', {
                    type: event.type,
                    responseTime: Math.round(responseTime),
                    target: event.target.tagName.toLowerCase()
                });
            }
        });
    }
    
    setupReporting() {
        // Report metrics periodically
        setInterval(() => {
            this.reportCurrentMetrics();
        }, 30000);
        
        // Report on page unload
        window.addEventListener('beforeunload', () => {
            this.reportFinalMetrics();
        });
        
        // Report on visibility change
        document.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'hidden') {
                this.reportFinalMetrics();
            }
        });
    }
    
    reportMetric(name, value) {
        if (!this.isRecording) return;
        
        const metric = {
            name: name,
            value: value,
            timestamp: Date.now(),
            url: window.location.href,
            userAgent: navigator.userAgent,
            networkInfo: this.networkInfo,
            viewport: {
                width: window.innerWidth,
                height: window.innerHeight
            }
        };
        
        // Send to analytics endpoint (implement based on your needs)
        this.sendMetric(metric);
        
        // Log to console in development
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            console.log('📊 Performance Metric:', metric);
        }
    }
    
    sendMetric(metric) {
        // Get CSRF token from cookie or meta tag
        const csrfToken = this.getCSRFToken();

        // Use sendBeacon for reliable delivery
        if (navigator.sendBeacon && csrfToken) {
            const formData = new FormData();
            formData.append('csrfmiddlewaretoken', csrfToken);
            formData.append('data', JSON.stringify(metric));
            navigator.sendBeacon(this.reportingEndpoint, formData);
        } else {
            // Fallback to fetch with proper CSRF handling
            fetch(this.reportingEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken || '',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify(metric)
            }).catch(error => {
                console.warn('Failed to send performance metric:', error);
            });
        }
    }

    getCSRFToken() {
        // Try to get CSRF token from meta tag first
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        if (metaTag) {
            return metaTag.getAttribute('content');
        }

        // Fallback to cookie
        const cookieMatch = document.cookie.match(/csrftoken=([^;]+)/);
        if (cookieMatch) {
            return cookieMatch[1];
        }

        // Last resort: try to get from form
        const csrfInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
        if (csrfInput) {
            return csrfInput.value;
        }

        return null;
    }
    
    reportCurrentMetrics() {
        if (Object.values(this.metrics).some(v => v !== null)) {
            this.reportMetric('core_vitals', { ...this.metrics });
        }
    }
    
    reportFinalMetrics() {
        // Calculate final load time
        this.metrics.loadComplete = performance.now();
        
        // Report final metrics
        this.reportMetric('page_complete', {
            metrics: this.metrics,
            timing: this.getNavigationTiming(),
            resources: this.getResourceSummary()
        });
    }
    
    getNavigationTiming() {
        if ('performance' in window && 'getEntriesByType' in performance) {
            const navigation = performance.getEntriesByType('navigation')[0];
            if (navigation) {
                return {
                    dns: Math.round(navigation.domainLookupEnd - navigation.domainLookupStart),
                    connection: Math.round(navigation.connectEnd - navigation.connectStart),
                    request: Math.round(navigation.responseStart - navigation.requestStart),
                    response: Math.round(navigation.responseEnd - navigation.responseStart),
                    dom: Math.round(navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart),
                    load: Math.round(navigation.loadEventEnd - navigation.loadEventStart)
                };
            }
        }
        return null;
    }
    
    getResourceSummary() {
        if ('performance' in window && 'getEntriesByType' in performance) {
            const resources = performance.getEntriesByType('resource');
            const summary = {
                total: resources.length,
                scripts: 0,
                styles: 0,
                images: 0,
                fonts: 0,
                other: 0,
                totalSize: 0
            };
            
            resources.forEach(resource => {
                const size = resource.transferSize || resource.decodedBodySize || 0;
                summary.totalSize += size;
                
                switch (resource.initiatorType) {
                    case 'script':
                        summary.scripts++;
                        break;
                    case 'link':
                        if (resource.name.includes('.css')) {
                            summary.styles++;
                        } else {
                            summary.other++;
                        }
                        break;
                    case 'img':
                        summary.images++;
                        break;
                    default:
                        if (resource.name.includes('font') || resource.name.includes('.woff')) {
                            summary.fonts++;
                        } else {
                            summary.other++;
                        }
                }
            });
            
            return summary;
        }
        return null;
    }
    
    analyzeCLSCauses(entries) {
        // Analyze what's causing layout shifts
        entries.forEach(entry => {
            entry.sources.forEach(source => {
                this.reportMetric('cls_source', {
                    element: source.node?.tagName || 'unknown',
                    previousRect: source.previousRect,
                    currentRect: source.currentRect
                });
            });
        });
    }
    
    showOfflineIndicator() {
        // Show offline status to user
        if (window.showToast) {
            window.showToast('You are currently offline', 'warning', {
                duration: 0,
                actions: [{
                    text: 'Dismiss',
                    handler: () => {}
                }]
            });
        }
    }
    
    // Public API methods
    getMetrics() {
        return { ...this.metrics };
    }
    
    getNetworkInfo() {
        return { ...this.networkInfo };
    }
    
    startRecording() {
        this.isRecording = true;
    }
    
    stopRecording() {
        this.isRecording = false;
    }
    
    clearMetrics() {
        Object.keys(this.metrics).forEach(key => {
            this.metrics[key] = null;
        });
    }
    
    disconnect() {
        // Clean up all observers
        this.observers.forEach(observer => {
            observer.disconnect();
        });
        this.observers.clear();
        
        this.isRecording = false;
        console.log('📊 Performance Monitor disconnected');
    }
}

// Initialize performance monitor
const performanceMonitor = new PerformanceMonitor();

// Export for global access
window.performanceMonitor = performanceMonitor;

// Expose utilities
window.performanceUtils = {
    // Measure function execution time
    measure: (fn, name = 'function') => {
        const start = performance.now();
        const result = fn();
        const end = performance.now();
        
        console.log(`⏱️ ${name} took ${Math.round(end - start)}ms`);
        performanceMonitor.reportMetric('function_timing', {
            name: name,
            duration: Math.round(end - start)
        });
        
        return result;
    },
    
    // Measure async function execution time
    measureAsync: async (fn, name = 'async function') => {
        const start = performance.now();
        const result = await fn();
        const end = performance.now();
        
        console.log(`⏱️ ${name} took ${Math.round(end - start)}ms`);
        performanceMonitor.reportMetric('async_function_timing', {
            name: name,
            duration: Math.round(end - start)
        });
        
        return result;
    },
    
    // Get current performance state
    getPerformanceState: () => {
        return {
            metrics: performanceMonitor.getMetrics(),
            network: performanceMonitor.getNetworkInfo(),
            memory: performance.memory ? {
                used: Math.round(performance.memory.usedJSHeapSize / 1024 / 1024),
                total: Math.round(performance.memory.totalJSHeapSize / 1024 / 1024),
                limit: Math.round(performance.memory.jsHeapSizeLimit / 1024 / 1024)
            } : null
        };
    }
};

