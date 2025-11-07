/**
 * Example Unit Tests
 * Basic tests to verify testing infrastructure
 */

import { describe, it, expect, vi } from 'vitest';

describe('Testing Infrastructure', () => {
    it('should run basic assertions', () => {
        expect(true).toBe(true);
        expect(2 + 2).toBe(4);
        expect('hello').toBe('hello');
    });

    it('should mock functions', () => {
        const mockFn = vi.fn();
        mockFn('test');

        expect(mockFn).toHaveBeenCalledWith('test');
        expect(mockFn).toHaveBeenCalledTimes(1);
    });

    it('should have DOM APIs mocked', () => {
        expect(window.localStorage).toBeDefined();
        expect(window.navigator).toBeDefined();
        expect(window.matchMedia).toBeDefined();
        expect(global.IntersectionObserver).toBeDefined();
    });
});

describe('Utility Functions', () => {
    it('should validate email format', () => {
        const isValidEmail = email => {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            return emailRegex.test(email);
        };

        expect(isValidEmail('test@example.com')).toBe(true);
        expect(isValidEmail('invalid-email')).toBe(false);
        expect(isValidEmail('')).toBe(false);
    });

    it('should format performance metrics', () => {
        const formatMetric = (value, unit = 'ms') => {
            if (typeof value !== 'number') { return 'N/A'; }
            if (value < 1000) { return `${value.toFixed(0)}${unit}`; }
            return `${(value / 1000).toFixed(2)}s`;
        };

        expect(formatMetric(500)).toBe('500ms');
        expect(formatMetric(1500)).toBe('1.50s');
        expect(formatMetric('invalid')).toBe('N/A');
    });

    it('should handle localStorage operations safely', () => {
        const safeLocalStorage = {
            getItem: key => {
                try {
                    return window.localStorage.getItem(key);
                } catch {
                    return null;
                }
            },
            setItem: (key, value) => {
                try {
                    window.localStorage.setItem(key, value);
                    return true;
                } catch {
                    return false;
                }
            }
        };

        expect(safeLocalStorage.setItem('test', 'value')).toBe(true);
        expect(safeLocalStorage.getItem('test')).toBeDefined();
    });
});
