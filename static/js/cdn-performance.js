/**
 * CDN and Asset Performance Monitoring System
 * Tracks:
 * - Time to First Byte (TTFB) for assets
 * - CDN cache hit rates
 * - Asset load times and failures
 * - Network performance metrics
 */

class CDNPerformanceMonitor {
    constructor() {
        const globalConfig = window.CDN_MONITOR_CONFIG || {};
        this.config = {
            criticalAssets: Array.isArray(globalConfig.criticalAssets) && globalConfig.criticalAssets.length
                ? globalConfig.criticalAssets
                : ['/static/css/output.css', '/static/js/image-optimization.js'],
            performanceEndpoint: typeof globalConfig.performanceEndpoint === 'string' && globalConfig.performanceEndpoint.trim()
                ? globalConfig.performanceEndpoint
                : null
        };
        this.metrics = {
            ttfb: [],
            loadTimes: [],
            cacheHits: 0,
            cacheMisses: 0,
            failures: 0,
            totalRequests: 0,
            assetTypes: {}
        };

        this.observer = null;
        this.init();
    }

    /**
     * Initialize performance monitoring
     */
    init() {
        if ('PerformanceObserver' in window) {
            this.setupPerformanceObserver();
        }

        this.setupNetworkMonitoring();
        this.monitorCriticalAssets();

        // Report metrics periodically
        this.startPeriodicReporting();
    }

    /**
     * Setup Performance Observer for detailed metrics
     */
    setupPerformanceObserver() {
        // Monitor resource timing
        this.observer = new PerformanceObserver(list => {
            list.getEntries().forEach(entry => {
                if (this.isStaticAsset(entry.name)) {
                    this.processAssetMetrics(entry);
                }
            });
        });

        this.observer.observe({ entryTypes: ['resource'] });

        // Monitor navigation timing for TTFB
        const navObserver = new PerformanceObserver(list => {
            list.getEntries().forEach(entry => {
                this.processNavigationMetrics(entry);
            });
        });

        navObserver.observe({ entryTypes: ['navigation'] });
    }

    /**
     * Check if URL is a static asset
     */
    isStaticAsset(url) {
        const staticExtensions = ['.css', '.js', '.png', '.jpg', '.jpeg', '.svg', '.webp', '.avif', '.gif', '.woff', '.woff2', '.ttf'];
        return staticExtensions.some(ext => url.toLowerCase().includes(ext)) || url.includes('/static/');
    }

    /**
     * Process asset performance metrics
     */
    processAssetMetrics(entry) {
        this.metrics.totalRequests++;

        // Calculate TTFB
        const ttfb = entry.responseStart - entry.requestStart;
        if (ttfb > 0) {
            this.metrics.ttfb.push({
                url: entry.name,
                ttfb: ttfb,
                timestamp: Date.now()
            });
        }

        // Calculate total load time
        const loadTime = entry.responseEnd - entry.startTime;
        this.metrics.loadTimes.push({
            url: entry.name,
            loadTime: loadTime,
            size: entry.transferSize,
            timestamp: Date.now()
        });

        // Check if served from cache
        if (entry.transferSize === 0 && entry.decodedBodySize > 0) {
            this.metrics.cacheHits++;
        } else {
            this.metrics.cacheMisses++;
        }

        // Track by asset type
        const assetType = this.getAssetType(entry.name);
        if (!this.metrics.assetTypes[assetType]) {
            this.metrics.assetTypes[assetType] = {
                count: 0,
                totalSize: 0,
                totalTime: 0
            };
        }

        this.metrics.assetTypes[assetType].count++;
        this.metrics.assetTypes[assetType].totalSize += entry.transferSize;
        this.metrics.assetTypes[assetType].totalTime += loadTime;

        // Log slow assets
        if (loadTime > 2000) {
            console.warn(`Slow asset detected: ${entry.name} - ${loadTime.toFixed(2)}ms`);
        }

        // Check for CDN performance
        this.analyzeCDNPerformance(entry);
    }

    /**
     * Process navigation timing metrics
     */
    processNavigationMetrics(entry) {
        const ttfb = entry.responseStart - entry.requestStart;

        this.metrics.navigationTiming = {
            ttfb: ttfb,
            domContentLoaded: entry.domContentLoadedEventEnd - entry.domContentLoadedEventStart,
            loadComplete: entry.loadEventEnd - entry.loadEventStart,
            totalTime: entry.loadEventEnd - entry.navigationStart
        };

        // Log performance warnings
        if (ttfb > 200) {
            console.warn(`High TTFB detected: ${ttfb.toFixed(2)}ms`);
        }
    }

    /**
     * Get asset type from URL
     */
    getAssetType(url) {
        if (url.includes('.css')) { return 'CSS'; }
        if (url.includes('.js')) { return 'JavaScript'; }
        if (url.match(/\.(png|jpg|jpeg|gif|svg|webp|avif)$/i)) { return 'Image'; }
        if (url.match(/\.(woff|woff2|ttf|otf)$/i)) { return 'Font'; }
        return 'Other';
    }

    /**
     * Analyze CDN performance
     */
    analyzeCDNPerformance(entry) {
        const url = new URL(entry.name);
        const isCDN = this.isCDNAsset(url.hostname);

        if (isCDN) {
            const loadTime = entry.responseEnd - entry.startTime;
            const size = entry.transferSize;

            // Calculate CDN efficiency metrics
            const efficiency = size > 0 ? (loadTime / size) * 1000 : 0; // ms per KB

            if (efficiency > 50) { // More than 50ms per KB indicates slow CDN
                console.warn(`CDN performance issue: ${entry.name} - ${efficiency.toFixed(2)}ms/KB`);
            }

            // Track CDN cache headers
            if (entry.transferSize === 0) {
                console.log(`CDN cache hit: ${entry.name}`);
            }
        }
    }

    /**
     * Check if hostname is a CDN
     */
    isCDNAsset(hostname) {
        const cdnPatterns = [
            'cdn.', 'assets.', 'static.',
            'cloudflare', 'cloudfront', 'fastly',
            'jsdelivr', 'unpkg', 'cdnjs'
        ];

        return cdnPatterns.some(pattern => hostname.includes(pattern));
    }

    /**
     * Setup network condition monitoring
     */
    setupNetworkMonitoring() {
        if ('navigator' in window && 'connection' in navigator) {
            const connection = navigator.connection;

            const logNetworkChange = () => {
                console.log(`Network changed: ${connection.effectiveType}, ${connection.downlink}Mbps`);

                // Adjust image quality based on connection
                this.adjustAssetQuality(connection.effectiveType);
            };

            connection.addEventListener('change', logNetworkChange);
            logNetworkChange(); // Log initial state
        }
    }

    /**
     * Adjust asset loading strategy based on network conditions
     */
    adjustAssetQuality(connectionType) {
        const body = document.body;

        // Remove existing network classes
        body.classList.remove('slow-connection', 'fast-connection', '4g-connection');

        // Add appropriate class based on connection type
        switch (connectionType) {
            case 'slow-2g':
            case '2g':
                body.classList.add('slow-connection');
                break;
            case '3g':
                // Default quality
                break;
            case '4g':
            case '5g':
                body.classList.add('fast-connection');
                break;
        }
    }

    /**
     * Monitor critical assets loading
     */
    monitorCriticalAssets() {
        const assets = Array.isArray(this.config.criticalAssets) ? this.config.criticalAssets : [];
        if (!assets.length) {
            return;
        }

        assets.forEach(asset => {
            const startTime = performance.now();

            fetch(asset, { method: 'HEAD' })
                .then(response => {
                    const endTime = performance.now();
                    const loadTime = endTime - startTime;

                    console.log(`Critical asset ${asset}: ${loadTime.toFixed(2)}ms, Status: ${response.status}`);

                    if (loadTime > 1000) {
                        console.warn(`Critical asset is slow: ${asset}`);
                    }
                })
                .catch(error => {
                    console.error(`Critical asset failed: ${asset}`, error);
                    this.metrics.failures++;
                });
        });
    }

    /**
     * Calculate cache hit ratio
     */
    getCacheHitRatio() {
        const total = this.metrics.cacheHits + this.metrics.cacheMisses;
        return total > 0 ? (this.metrics.cacheHits / total) * 100 : 0;
    }

    /**
     * Get average TTFB
     */
    getAverageTTFB() {
        if (this.metrics.ttfb.length === 0) { return 0; }

        const total = this.metrics.ttfb.reduce((sum, entry) => sum + entry.ttfb, 0);
        return total / this.metrics.ttfb.length;
    }

    /**
     * Get performance summary
     */
    getPerformanceSummary() {
        const avgTTFB = this.getAverageTTFB();
        const cacheHitRatio = this.getCacheHitRatio();
        const totalLoadTime = this.metrics.loadTimes.reduce((sum, entry) => sum + entry.loadTime, 0);
        const avgLoadTime = this.metrics.loadTimes.length > 0 ? totalLoadTime / this.metrics.loadTimes.length : 0;

        return {
            averageTTFB: Math.round(avgTTFB),
            cacheHitRatio: Math.round(cacheHitRatio),
            averageLoadTime: Math.round(avgLoadTime),
            totalRequests: this.metrics.totalRequests,
            failures: this.metrics.failures,
            assetTypes: this.metrics.assetTypes,
            navigationTiming: this.metrics.navigationTiming
        };
    }

    /**
     * Send performance data to analytics endpoint
     */
    reportMetrics() {
        const summary = this.getPerformanceSummary();
        // Send to analytics endpoint if configured
        const endpoint = this.config.performanceEndpoint;

        if (endpoint) {
            const payload = JSON.stringify({
                type: 'cdn_performance',
                metrics: summary,
                timestamp: Date.now(),
                userAgent: navigator.userAgent,
                url: window.location.href
            });

            if ('navigator' in window && 'sendBeacon' in navigator) {
                const sent = navigator.sendBeacon(endpoint, payload);
                if (!sent && window.fetch) {
                    fetch(endpoint, { method: 'POST', body: payload, keepalive: true, headers: { 'Content-Type': 'application/json' } }).catch(() => { });
                }
            } else if (window.fetch) {
                fetch(endpoint, { method: 'POST', body: payload, keepalive: true, headers: { 'Content-Type': 'application/json' } }).catch(() => { });
            }
        } else {
            console.debug('CDN performance endpoint disabled; metrics logging only.');
        }
        console.log('CDN Performance Summary:', summary);
    }

    /**
     * Start periodic performance reporting
     */
    startPeriodicReporting() {
        // Report every 30 seconds during active usage
        setInterval(() => {
            if (document.visibilityState === 'visible') {
                this.reportMetrics();
            }
        }, 30000);

        // Report when page becomes hidden
        document.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'hidden') {
                this.reportMetrics();
            }
        });

        // Report before page unload
        window.addEventListener('beforeunload', () => {
            this.reportMetrics();
        });
    }

    /**
     * Get real-time CDN status
     */
    checkCDNStatus() {
        const cdnUrl = window.CDN_DOMAIN || null;

        if (!cdnUrl) { return Promise.resolve({ status: 'No CDN configured' }); }

        const startTime = performance.now();

        return fetch(`https://${cdnUrl}/static/css/output.css`, { method: 'HEAD' })
            .then(response => {
                const endTime = performance.now();
                const responseTime = endTime - startTime;

                return {
                    status: 'Online',
                    responseTime: Math.round(responseTime),
                    cacheStatus: response.headers.get('cf-cache-status') || 'Unknown'
                };
            })
            .catch(error => ({
                status: 'Offline',
                error: error.message
            }));
    }

    /**
     * Cleanup and destroy
     */
    destroy() {
        if (this.observer) {
            this.observer.disconnect();
            this.observer = null;
        }

        this.metrics = null;
    }
}

// Initialize CDN performance monitor
document.addEventListener('DOMContentLoaded', () => {
    window.cdnMonitor = new CDNPerformanceMonitor();

    // Expose global function for manual checks
    window.checkCDNPerformance = () => window.cdnMonitor.getPerformanceSummary();

    window.checkCDNStatus = () => window.cdnMonitor.checkCDNStatus();

    console.log('CDN Performance Monitor initialized');
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CDNPerformanceMonitor;
}
