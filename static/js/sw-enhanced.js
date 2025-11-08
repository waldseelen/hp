/**
 * Enhanced Service Worker for Portfolio PWA
 * Advanced caching strategies, background sync, and offline support
 */

const CACHE_VERSION = '2.1.0';
const STATIC_CACHE_NAME = `static-v${CACHE_VERSION}`;
const DYNAMIC_CACHE_NAME = `dynamic-v${CACHE_VERSION}`;
const FONTS_CACHE_NAME = `fonts-v${CACHE_VERSION}`;
const IMAGES_CACHE_NAME = `images-v${CACHE_VERSION}`;
const API_CACHE_NAME = `api-v${CACHE_VERSION}`;

// Enhanced static files list with optimized assets
const STATIC_FILES = [
    '/',
    '/offline/',
    '/static/css/output.css',
    '/static/css/fonts-optimized.css',
    '/static/css/custom.css',
    '/static/js/dist/core.high.bundle.js',
    '/static/js/dist/main.medium.bundle.js',
    '/static/js/font-loader.js',
    '/static/icons/sprites/icons.svg',
    '/static/favicon.ico'
];

// Critical pages for offline access
const CRITICAL_PAGES = [
    '/',
    '/blog/',
    '/tools/',
    '/contact/',
    '/offline/'
];

// Cache expiration policies
const CACHE_EXPIRY = {
    static: 30 * 24 * 60 * 60 * 1000, // 30 days
    dynamic: 7 * 24 * 60 * 60 * 1000, // 7 days
    images: 30 * 24 * 60 * 60 * 1000, // 30 days
    fonts: 365 * 24 * 60 * 60 * 1000, // 1 year
    api: 5 * 60 * 1000 // 5 minutes
};

// Install event - precache critical assets
self.addEventListener('install', event => {
    console.log(`🔧 Service Worker: Installing v${CACHE_VERSION}`);

    event.waitUntil(
        Promise.all([
            precacheStaticAssets(),
            precacheCriticalPages()
        ]).then(() => {
            console.log('✅ Service Worker: Installation complete');
            return self.skipWaiting();
        }).catch(error => {
            console.error('❌ Service Worker: Installation failed', error);
        })
    );
});

async function precacheStaticAssets() {
    const cache = await caches.open(STATIC_CACHE_NAME);
    return cache.addAll(STATIC_FILES.map(url => new Request(url, { cache: 'reload' })));
}

async function precacheCriticalPages() {
    const cache = await caches.open(DYNAMIC_CACHE_NAME);

    for (const url of CRITICAL_PAGES) {
        try {
            const response = await fetch(url, { cache: 'reload' });
            if (response.ok) {
                await cache.put(url, response);
            }
        } catch (error) {
            console.warn(`Failed to precache ${url}:`, error);
        }
    }
}

// Activate event - cleanup old caches and take control
self.addEventListener('activate', event => {
    console.log(`🚀 Service Worker: Activating v${CACHE_VERSION}`);

    event.waitUntil(
        Promise.all([
            cleanupOldCaches(),
            setupPeriodicSync()
        ]).then(() => {
            console.log('✅ Service Worker: Activation complete');
            return self.clients.claim();
        })
    );
});

async function cleanupOldCaches() {
    const cacheNames = await caches.keys();
    const validCacheNames = [
        STATIC_CACHE_NAME,
        DYNAMIC_CACHE_NAME,
        FONTS_CACHE_NAME,
        IMAGES_CACHE_NAME,
        API_CACHE_NAME
    ];

    return Promise.all(
        cacheNames.map(cacheName => {
            if (!validCacheNames.includes(cacheName)) {
                console.log('🗑️ Service Worker: Deleting old cache', cacheName);
                return caches.delete(cacheName);
            }
        })
    );
}

async function setupPeriodicSync() {
    // Register periodic background sync (if supported)
    if ('periodicSync' in self.registration) {
        try {
            await self.registration.periodicSync.register('cache-cleanup', {
                minInterval: 24 * 60 * 60 * 1000 // Daily
            });
        } catch (error) {
            console.log('Periodic sync not available:', error);
        }
    }
}

// Enhanced fetch handler with intelligent routing
self.addEventListener('fetch', event => {
    const { request } = event;
    const url = new URL(request.url);

    // Skip non-GET requests except for background sync POST
    if (request.method !== 'GET' && !shouldHandleNonGet(request)) {
        return;
    }

    // Skip external requests
    if (url.origin !== location.origin) {
        return;
    }

    event.respondWith(handleFetchRequest(request));
});

function shouldHandleNonGet(request) {
    // Handle POST requests for background sync
    return request.method === 'POST' &&
        (request.url.includes('/api/') || request.url.includes('/contact/'));
}

async function handleFetchRequest(request) {
    const url = new URL(request.url);
    const requestType = getRequestType(request);

    try {
        switch (requestType) {
            case 'static':
                return await cacheFirst(request, STATIC_CACHE_NAME);

            case 'image':
                return await cacheFirst(request, IMAGES_CACHE_NAME);

            case 'font':
                return await cacheFirst(request, FONTS_CACHE_NAME);

            case 'api':
                return await networkFirst(request, API_CACHE_NAME, CACHE_EXPIRY.api);

            case 'page':
                return await staleWhileRevalidate(request, DYNAMIC_CACHE_NAME);

            case 'form-post':
                return await handleFormSubmission(request);

            default:
                return await networkFirst(request, DYNAMIC_CACHE_NAME);
        }
    } catch (error) {
        console.error('Fetch error:', error);
        return getOfflineResponse(request);
    }
}

function getRequestType(request) {
    const url = new URL(request.url);
    const pathname = url.pathname;

    if (request.method === 'POST') {
        return 'form-post';
    }

    if (pathname.startsWith('/static/css/') || pathname.startsWith('/static/js/')) {
        return 'static';
    }

    if (pathname.match(/\.(woff2?|ttf|otf|eot)$/)) {
        return 'font';
    }

    if (pathname.match(/\.(png|jpg|jpeg|gif|svg|ico|webp|avif)$/)) {
        return 'image';
    }

    if (pathname.startsWith('/api/')) {
        return 'api';
    }

    if (request.headers.get('Accept')?.includes('text/html')) {
        return 'page';
    }

    return 'other';
}

// Cache-first strategy for static assets
async function cacheFirst(request, cacheName) {
    const cache = await caches.open(cacheName);
    const cached = await cache.match(request);

    // Check if cached version is still valid
    if (cached && !isCacheExpired(cached, CACHE_EXPIRY.static)) {
        return cached;
    }

    try {
        const response = await fetch(request);
        if (response.ok) {
            await cache.put(request, response.clone());
        }
        return response;
    } catch (error) {
        if (cached) {
            return cached; // Return expired cache as fallback
        }
        throw error;
    }
}

// Network-first strategy for dynamic content
async function networkFirst(request, cacheName, ttl = CACHE_EXPIRY.dynamic) {
    const cache = await caches.open(cacheName);

    try {
        const response = await fetch(request);
        if (response.ok) {
            const responseWithTimestamp = new Response(response.body, {
                status: response.status,
                statusText: response.statusText,
                headers: {
                    ...response.headers,
                    'sw-cached': Date.now().toString()
                }
            });
            await cache.put(request, responseWithTimestamp.clone());
        }
        return response;
    } catch (error) {
        const cached = await cache.match(request);
        if (cached && !isCacheExpired(cached, ttl)) {
            return cached;
        }
        throw error;
    }
}

// Stale-while-revalidate for pages
async function staleWhileRevalidate(request, cacheName) {
    const cache = await caches.open(cacheName);
    const cached = await cache.match(request);

    const networkPromise = fetch(request)
        .then(response => {
            if (response.ok) {
                cache.put(request, response.clone());
            }
            return response;
        })
        .catch(() => null);

    return cached || await networkPromise || getOfflineResponse(request);
}

// Handle form submissions with background sync
async function handleFormSubmission(request) {
    if (!navigator.onLine) {
        await storeOfflineRequest(request);
        return new Response(JSON.stringify({
            success: true,
            message: 'Form submitted offline. Will sync when connection is restored.',
            offline: true
        }), {
            headers: { 'Content-Type': 'application/json' }
        });
    }

    try {
        return await fetch(request);
    } catch (error) {
        await storeOfflineRequest(request);
        throw error;
    }
}

async function storeOfflineRequest(request) {
    const requestData = {
        url: request.url,
        method: request.method,
        headers: [...request.headers.entries()],
        body: await request.text(),
        timestamp: Date.now()
    };

    const cache = await caches.open(DYNAMIC_CACHE_NAME);
    await cache.put(`offline-request-${Date.now()}`, new Response(JSON.stringify(requestData)));

    // Register background sync
    if ('sync' in self.registration) {
        await self.registration.sync.register('offline-requests');
    }
}

function isCacheExpired(response, maxAge) {
    const cachedTime = response.headers.get('sw-cached');
    if (!cachedTime) { return false; }

    return Date.now() - parseInt(cachedTime, 10) > maxAge;
}

// Enhanced offline response
async function getOfflineResponse(request) {
    const url = new URL(request.url);

    // For HTML pages, return offline page
    if (request.headers.get('Accept')?.includes('text/html')) {
        const offlinePage = await caches.match('/offline/');
        if (offlinePage) {
            return offlinePage;
        }

        // Fallback offline page
        return new Response(`
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Offline - Portfolio</title>
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <style>
                    body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; text-align: center; padding: 50px; }
                    .offline-icon { font-size: 64px; margin-bottom: 20px; }
                </style>
            </head>
            <body>
                <div class="offline-icon">📱</div>
                <h1>You're Offline</h1>
                <p>Please check your internet connection and try again.</p>
                <button onclick="location.reload()">Retry</button>
            </body>
            </html>
        `, {
            headers: { 'Content-Type': 'text/html' }
        });
    }

    // For images, return SVG placeholder
    if (url.pathname.match(/\.(png|jpg|jpeg|gif|svg|ico|webp|avif)$/)) {
        return new Response(`
            <svg xmlns="http://www.w3.org/2000/svg" width="300" height="200" viewBox="0 0 300 200">
                <rect width="300" height="200" fill="#f8f9fa" stroke="#dee2e6" stroke-width="2"/>
                <text x="150" y="100" text-anchor="middle" fill="#6c757d" font-family="sans-serif">
                    Image Unavailable
                </text>
                <text x="150" y="120" text-anchor="middle" fill="#6c757d" font-family="sans-serif" font-size="12">
                    (Offline)
                </text>
            </svg>
        `, {
            headers: { 'Content-Type': 'image/svg+xml' }
        });
    }

    return new Response('Service Unavailable', {
        status: 503,
        statusText: 'Service Unavailable'
    });
}

// Background sync for offline requests
self.addEventListener('sync', event => {
    console.log('🔄 Background sync:', event.tag);

    if (event.tag === 'offline-requests') {
        event.waitUntil(syncOfflineRequests());
    } else if (event.tag === 'cache-cleanup') {
        event.waitUntil(performCacheCleanup());
    }
});

async function syncOfflineRequests() {
    const cache = await caches.open(DYNAMIC_CACHE_NAME);
    const keys = await cache.keys();

    for (const request of keys) {
        if (request.url.includes('offline-request-')) {
            try {
                const response = await cache.match(request);
                const requestData = await response.json();

                // Replay the request
                const replayResponse = await fetch(requestData.url, {
                    method: requestData.method,
                    headers: requestData.headers,
                    body: requestData.body
                });

                if (replayResponse.ok) {
                    await cache.delete(request);
                    console.log('✅ Synced offline request:', requestData.url);
                }
            } catch (error) {
                console.error('❌ Failed to sync request:', error);
            }
        }
    }
}

async function performCacheCleanup() {
    const cacheNames = [DYNAMIC_CACHE_NAME, IMAGES_CACHE_NAME, API_CACHE_NAME];

    for (const cacheName of cacheNames) {
        try {
            const cache = await caches.open(cacheName);
            const keys = await cache.keys();

            for (const request of keys) {
                const response = await cache.match(request);
                if (response && isCacheExpired(response, CACHE_EXPIRY.dynamic)) {
                    await cache.delete(request);
                }
            }
        } catch (error) {
            console.error('Cache cleanup error:', error);
        }
    }
}

// Enhanced push notifications
self.addEventListener('push', event => {
    console.log('📱 Push notification received');

    const data = event.data ? event.data.json() : {};
    const options = {
        body: data.body || 'New update available',
        icon: '/static/favicon.ico',
        badge: '/static/images/badge.png',
        tag: data.tag || 'general',
        requireInteraction: data.persistent || false,
        vibrate: data.vibrate || [200, 100, 200],
        data: {
            url: data.url || '/',
            timestamp: Date.now(),
            ...data.data
        },
        actions: data.actions || [
            { action: 'view', title: 'View', icon: '/static/icons/optimized/view.svg' },
            { action: 'dismiss', title: 'Dismiss', icon: '/static/icons/optimized/close.svg' }
        ]
    };

    event.waitUntil(
        self.registration.showNotification(data.title || 'Portfolio Update', options)
    );
});

// Enhanced notification handling
self.addEventListener('notificationclick', event => {
    console.log('👆 Notification clicked:', event.action);

    event.notification.close();

    if (event.action === 'dismiss') {
        return;
    }

    const url = event.notification.data.url || '/';

    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true })
            .then(clientList => {
                // Focus existing window if available
                for (const client of clientList) {
                    if (client.url.includes(url.split('/')[1]) && 'focus' in client) {
                        return client.focus();
                    }
                }

                // Open new window
                if (clients.openWindow) {
                    return clients.openWindow(url);
                }
            })
    );
});

// Message handling for updates and control
self.addEventListener('message', event => {
    const { data } = event;

    switch (data?.type) {
        case 'SKIP_WAITING':
            self.skipWaiting();
            break;

        case 'CHECK_UPDATE':
            checkForUpdates().then(hasUpdate => {
                event.ports[0]?.postMessage({ hasUpdate });
            });
            break;

        case 'CLEAR_CACHE':
            clearAllCaches().then(() => {
                event.ports[0]?.postMessage({ cleared: true });
            });
            break;

        case 'GET_CACHE_INFO':
            getCacheInfo().then(info => {
                event.ports[0]?.postMessage({ cacheInfo: info });
            });
            break;
    }
});

async function checkForUpdates() {
    try {
        const response = await fetch('/sw-version.json', { cache: 'no-cache' });
        const { version } = await response.json();
        return version !== CACHE_VERSION;
    } catch (error) {
        return false;
    }
}

async function clearAllCaches() {
    const cacheNames = await caches.keys();
    await Promise.all(cacheNames.map(name => caches.delete(name)));
    console.log('🗑️ All caches cleared');
}

async function getCacheInfo() {
    const cacheNames = await caches.keys();
    const info = {};

    for (const name of cacheNames) {
        const cache = await caches.open(name);
        const keys = await cache.keys();
        info[name] = keys.length;
    }

    return {
        version: CACHE_VERSION,
        caches: info,
        totalCaches: cacheNames.length
    };
}
