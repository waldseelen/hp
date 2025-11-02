/**
 * Unit Test Setup for Vitest
 * Global configuration and mocks
 */

import { vi } from 'vitest';

// Mock DOM APIs that might not be available in test environment
Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: vi.fn().mockImplementation(query => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: vi.fn(), // deprecated
        removeListener: vi.fn(), // deprecated
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
    })),
});

// Mock IntersectionObserver
global.IntersectionObserver = vi.fn().mockImplementation(() => ({
    observe: vi.fn(),
    unobserve: vi.fn(),
    disconnect: vi.fn(),
    takeRecords: vi.fn().mockReturnValue([]),
}));

// Mock ResizeObserver
global.ResizeObserver = vi.fn().mockImplementation(() => ({
    observe: vi.fn(),
    unobserve: vi.fn(),
    disconnect: vi.fn(),
}));

// Mock fetch if not available
if (!global.fetch) {
    global.fetch = vi.fn();
}

// Mock localStorage
const localStorageMock = {
    getItem: vi.fn(),
    setItem: vi.fn(),
    removeItem: vi.fn(),
    clear: vi.fn(),
    length: 0,
    key: vi.fn(),
};

Object.defineProperty(window, 'localStorage', {
    value: localStorageMock,
});

// Mock sessionStorage
Object.defineProperty(window, 'sessionStorage', {
    value: localStorageMock,
});

// Mock navigator APIs
Object.defineProperty(window, 'navigator', {
    value: {
        userAgent: 'Mozilla/5.0 (Test Environment)',
        language: 'en-US',
        languages: ['en-US', 'en'],
        onLine: true,
        cookieEnabled: true,
        serviceWorker: {
            register: vi.fn().mockResolvedValue({}),
            ready: vi.fn().mockResolvedValue({}),
        },
        permissions: {
            query: vi.fn().mockResolvedValue({ state: 'granted' }),
        },
        clipboard: {
            writeText: vi.fn().mockResolvedValue(),
            readText: vi.fn().mockResolvedValue(''),
        },
    },
    writable: true,
});

// Mock window.location
Object.defineProperty(window, 'location', {
    value: {
        href: 'http://localhost:3000',
        protocol: 'http:',
        host: 'localhost:3000',
        hostname: 'localhost',
        port: '3000',
        pathname: '/',
        search: '',
        hash: '',
        origin: 'http://localhost:3000',
        assign: vi.fn(),
        replace: vi.fn(),
        reload: vi.fn(),
    },
    writable: true,
});

// Mock console methods for cleaner test output
global.console = {
    ...console,
    // Uncomment to suppress console.log in tests
    // log: vi.fn(),
    // warn: vi.fn(),
    // error: vi.fn(),
};

// Performance API mock
Object.defineProperty(window, 'performance', {
    value: {
        now: vi.fn(() => Date.now()),
        mark: vi.fn(),
        measure: vi.fn(),
        getEntriesByType: vi.fn(() => []),
        getEntriesByName: vi.fn(() => []),
        navigation: {
            type: 0,
        },
        timing: {
            navigationStart: Date.now() - 1000,
            loadEventEnd: Date.now(),
        },
    },
});

// Web APIs mocks
global.URL.createObjectURL = vi.fn(() => 'blob:mock-url');
global.URL.revokeObjectURL = vi.fn();

// WebSocket mock
global.WebSocket = vi.fn().mockImplementation(() => ({
    send: vi.fn(),
    close: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    readyState: 1, // OPEN
}));

// IndexedDB mock (basic)
global.indexedDB = {
    open: vi.fn().mockImplementation(() => ({
        onsuccess: null,
        onerror: null,
        result: {
            createObjectStore: vi.fn(),
            transaction: vi.fn(() => ({
                objectStore: vi.fn(() => ({
                    add: vi.fn(),
                    get: vi.fn(),
                    put: vi.fn(),
                    delete: vi.fn(),
                })),
            })),
        },
    })),
    deleteDatabase: vi.fn(),
};

export default {};
