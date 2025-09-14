// Service Worker for PWA
const CACHE_NAME = 'portfolio-v1.0.0';
const urlsToCache = [
    '/',
    '/offline/',
    '/static/css/custom.css',
    '/static/js/main.js',
    '/static/js/pwa.js',
    '/blog/',
    '/tools/',
    '/contact/',
    // Add more static assets as needed
];

// Install event
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('Opened cache');
                return cache.addAll(urlsToCache);
            })
    );
    self.skipWaiting();
});

// Fetch event
self.addEventListener('fetch', (event) => {
    event.respondWith(
        caches.match(event.request)
            .then((response) => {
                // Return cached version or fetch from network
                if (response) {
                    return response;
                }
                
                return fetch(event.request).then(
                    (response) => {
                        // Check if we received a valid response
                        if (!response || response.status !== 200 || response.type !== 'basic') {
                            return response;
                        }

                        // Clone the response
                        const responseToCache = response.clone();

                        caches.open(CACHE_NAME)
                            .then((cache) => {
                                cache.put(event.request, responseToCache);
                            });

                        return response;
                    }
                );
            })
            .catch(() => {
                // Return offline page for navigation requests
                if (event.request.destination === 'document') {
                    return caches.match('/offline/') || caches.match('/');
                }
            })
    );
});

// Activate event
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheName !== CACHE_NAME) {
                        console.log('Deleting old cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
    self.clients.claim();
});

// Background sync for offline form submissions
self.addEventListener('sync', (event) => {
    if (event.tag === 'contact-form') {
        event.waitUntil(syncContactForm());
    }
});

async function syncContactForm() {
    // Handle offline form submissions when back online
    try {
        const db = await openIndexedDB();
        const forms = await getOfflineForms(db);
        
        for (const form of forms) {
            try {
                const response = await fetch('/contact/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(form.data)
                });
                
                if (response.ok) {
                    await deleteOfflineForm(db, form.id);
                    console.log('Offline form synced successfully');
                }
            } catch (error) {
                console.error('Failed to sync form:', error);
            }
        }
    } catch (error) {
        console.error('Background sync failed:', error);
    }
}

function openIndexedDB() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open('PortfolioOfflineDB', 1);
        
        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve(request.result);
        
        request.onupgradeneeded = (event) => {
            const db = event.target.result;
            if (!db.objectStoreNames.contains('forms')) {
                db.createObjectStore('forms', { keyPath: 'id', autoIncrement: true });
            }
        };
    });
}

function getOfflineForms(db) {
    return new Promise((resolve, reject) => {
        const transaction = db.transaction(['forms'], 'readonly');
        const store = transaction.objectStore('forms');
        const request = store.getAll();
        
        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve(request.result);
    });
}

function deleteOfflineForm(db, id) {
    return new Promise((resolve, reject) => {
        const transaction = db.transaction(['forms'], 'readwrite');
        const store = transaction.objectStore('forms');
        const request = store.delete(id);
        
        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve();
    });
}