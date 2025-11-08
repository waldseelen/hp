/**
 * Service Worker for Portfolio PWA
 * Handles caching, offline functionality, and push notifications
 */

const CACHE_NAME = 'portfolio-cache-v1';
const STATIC_CACHE_NAME = 'static-v1';
const DYNAMIC_CACHE_NAME = 'dynamic-v1';

// Files to cache on installation
const STATIC_FILES = [
    '/',
    '/static/css/output.css',
    '/static/css/custom.min.css',
    '/static/css/inline-styles.css',
    '/static/css/cookie-consent.css',
    '/static/js/main.min.js',
    '/static/js/animations.js',
    '/static/js/cursor.js',
    '/static/js/cookie-consent.js',
    '/static/js/pwa.min.js',
    '/static/images/icon-base.svg',
    '/offline.html'
];

// Critical pages to warm cache on installation
const CRITICAL_PAGES = [
    '/',
    '/personal/',
    '/blog/',
    '/tools/',
    '/contact/',
    '/sitemap.xml',
    '/feed/rss/',
    '/feed/atom/'
];

// Cache strategies for different types of requests
const CACHE_STRATEGIES = {
    images: 'cache-first',
    static: 'cache-first',
    api: 'network-first',
    pages: 'network-first',
    documents: 'stale-while-revalidate', // For feeds and sitemaps
};

// Install event - cache static files
self.addEventListener('install', event => {
    console.log('Service Worker: Installing...');

    event.waitUntil(
        Promise.all([
            // Cache static files
            caches.open(STATIC_CACHE_NAME)
                .then(cache => {
                    console.log('Service Worker: Caching static files');
                    return cache.addAll(STATIC_FILES);
                }),

            // Warm cache for critical pages
            caches.open(DYNAMIC_CACHE_NAME)
                .then(cache => {
                    console.log('Service Worker: Warming cache for critical pages');
                    return Promise.all(
                        CRITICAL_PAGES.map(url => fetch(url, { mode: 'no-cors' })
                            .then(response => {
                                if (response.ok) {
                                    return cache.put(url, response);
                                }
                            })
                            .catch(error => {
                                console.log(`Failed to warm cache for ${url}:`, error);
                            }))
                    );
                })
        ])
            .then(() => {
                console.log('Service Worker: Installation and cache warming complete');
                return self.skipWaiting();
            })
            .catch(error => {
                console.error('Service Worker: Installation failed', error);
            })
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
    console.log('Service Worker: Activating...');

    event.waitUntil(
        caches.keys()
            .then(cacheNames => Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== STATIC_CACHE_NAME && cacheName !== DYNAMIC_CACHE_NAME) {
                        console.log('Service Worker: Deleting old cache', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            ))
            .then(() => {
                console.log('Service Worker: Activation complete');
                return self.clients.claim();
            })
    );
});

// Fetch event - handle requests with appropriate caching strategy
self.addEventListener('fetch', event => {
    const { request } = event;
    const url = new URL(request.url);

    // Skip non-GET requests
    if (request.method !== 'GET') {
        return;
    }

    // Skip external requests
    if (!url.origin === location.origin) {
        return;
    }

    // Determine cache strategy based on request type
    const strategy = getCacheStrategy(request);

    event.respondWith(
        handleRequest(request, strategy)
    );
});

// Determine appropriate cache strategy
function getCacheStrategy(request) {
    const url = new URL(request.url);

    // Static assets (CSS, JS, images)
    if (url.pathname.startsWith('/static/')) {
        if (url.pathname.match(/\.(png|jpg|jpeg|gif|svg|ico|webp)$/)) {
            return CACHE_STRATEGIES.images;
        }
        return CACHE_STRATEGIES.static;
    }

    // API requests
    if (url.pathname.startsWith('/api/')) {
        return CACHE_STRATEGIES.api;
    }

    // Document routes (feeds, sitemaps)
    if (url.pathname.startsWith('/feed/') ||
        url.pathname.endsWith('.xml') ||
        url.pathname.endsWith('.json')) {
        return CACHE_STRATEGIES.documents;
    }

    // HTML pages
    if (request.headers.get('Accept')?.includes('text/html')) {
        return CACHE_STRATEGIES.pages;
    }

    return 'network-first';
}

// Handle requests based on cache strategy
async function handleRequest(request, strategy) {
    switch (strategy) {
        case 'cache-first':
            return cacheFirst(request);
        case 'network-first':
            return networkFirst(request);
        case 'stale-while-revalidate':
            return staleWhileRevalidate(request);
        default:
            return networkFirst(request);
    }
}

// Cache first strategy - good for static assets
async function cacheFirst(request) {
    try {
        const cached = await caches.match(request);
        if (cached) {
            return cached;
        }

        const response = await fetch(request);
        await cacheResponse(request, response.clone());
        return response;
    } catch (error) {
        console.error('Cache first failed:', error);
        return getOfflineResponse(request);
    }
}

// Network first strategy - good for dynamic content
async function networkFirst(request) {
    try {
        const response = await fetch(request);
        await cacheResponse(request, response.clone());
        return response;
    } catch (error) {
        console.log('Network failed, trying cache:', error);
        const cached = await caches.match(request);
        if (cached) {
            return cached;
        }
        return getOfflineResponse(request);
    }
}

// Stale while revalidate - serve from cache, update in background
async function staleWhileRevalidate(request) {
    const cached = await caches.match(request);

    const networkResponse = fetch(request)
        .then(response => {
            cacheResponse(request, response.clone());
            return response;
        })
        .catch(() => cached);

    return cached || networkResponse;
}

// Cache a response
async function cacheResponse(request, response) {
    // Only cache successful responses
    if (!response || response.status !== 200 || response.type !== 'basic') {
        return;
    }

    const cache = await caches.open(DYNAMIC_CACHE_NAME);
    await cache.put(request, response);
}

// Get offline response for failed requests
async function getOfflineResponse(request) {
    // For HTML pages, return offline page
    if (request.headers.get('Accept')?.includes('text/html')) {
        const offlinePage = await caches.match('/offline.html');
        if (offlinePage) {
            return offlinePage;
        }
    }

    // For images, return placeholder
    if (request.url.match(/\.(png|jpg|jpeg|gif|svg|ico|webp)$/)) {
        return new Response(
            '<svg xmlns="http://www.w3.org/2000/svg" width="200" height="150" viewBox="0 0 200 150"><rect width="200" height="150" fill="#f0f0f0"/><text x="100" y="75" text-anchor="middle" fill="#999">Offline</text></svg>',
            { headers: { 'Content-Type': 'image/svg+xml' } }
        );
    }

    return new Response('Offline', {
        status: 503,
        statusText: 'Service Unavailable'
    });
}

// Push notification event
self.addEventListener('push', event => {
    console.log('Push notification received:', event);

    if (!event.data) {
        return;
    }

    try {
        const data = event.data.json();
        const options = {
            body: data.body || 'You have a new notification',
            icon: '/static/images/icon-192x192.png',
            badge: '/static/images/icon-badge.png',
            vibrate: [200, 100, 200],
            data: data.data || {},
            actions: data.actions || [
                {
                    action: 'view',
                    title: 'View',
                    icon: '/static/images/icon-view.png'
                },
                {
                    action: 'dismiss',
                    title: 'Dismiss',
                    icon: '/static/images/icon-dismiss.png'
                }
            ]
        };

        event.waitUntil(
            self.registration.showNotification(data.title || 'Portfolio Update', options)
        );
    } catch (error) {
        console.error('Error processing push notification:', error);
    }
});

// Notification click event
self.addEventListener('notificationclick', event => {
    console.log('Notification clicked:', event);

    event.notification.close();

    const action = event.action;
    const data = event.notification.data;

    if (action === 'dismiss') {
        return;
    }

    // Default action or 'view' action
    const urlToOpen = data.url || '/';

    event.waitUntil(
        clients.matchAll({ type: 'window' })
            .then(clientList => {
                // Check if app is already open
                for (const client of clientList) {
                    if (client.url === urlToOpen && 'focus' in client) {
                        return client.focus();
                    }
                }

                // Open new window
                if (clients.openWindow) {
                    return clients.openWindow(urlToOpen);
                }
            })
    );
});

// Background sync event
self.addEventListener('sync', event => {
    console.log('Background sync:', event.tag);

    if (event.tag === 'background-sync') {
        event.waitUntil(doBackgroundSync());
    }
});

async function doBackgroundSync() {
    // Handle background sync tasks
    console.log('Performing background sync...');

    try {
        // Example: Sync offline form submissions
        const offlineData = await getOfflineData();
        if (offlineData.length > 0) {
            await syncOfflineData(offlineData);
        }
    } catch (error) {
        console.error('Background sync failed:', error);
    }
}

async function getOfflineData() {
    // Retrieve offline data from IndexedDB or localStorage
    return [];
}

async function syncOfflineData(data) {
    // Sync data with server
    for (const item of data) {
        try {
            await fetch('/api/sync/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(item)
            });
        } catch (error) {
            console.error('Failed to sync item:', error);
        }
    }
}

// Message event - handle messages from main thread
self.addEventListener('message', event => {
    console.log('Service Worker received message:', event.data);

    if (event.data && event.data.type) {
        switch (event.data.type) {
            case 'SKIP_WAITING':
                self.skipWaiting();
                break;
            case 'GET_VERSION':
                event.ports[0].postMessage({ version: CACHE_NAME });
                break;
            case 'CLEAR_CACHE':
                clearCache();
                break;
        }
    }
});

async function clearCache() {
    const cacheNames = await caches.keys();
    await Promise.all(
        cacheNames.map(cacheName => caches.delete(cacheName))
    );
    console.log('All caches cleared');
}
