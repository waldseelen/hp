const { configureAxe } = require('@axe-core/playwright');

// Global accessibility test configuration
global.axeConfig = {
    rules: {
    // Enable all WCAG 2.1 AA rules
        'color-contrast': { enabled: true },
        'keyboard-navigation': { enabled: true },
        'focus-order-semantics': { enabled: true },
        'aria-label': { enabled: true },
        'landmark-no-duplicate-banner': { enabled: true },
        'landmark-no-duplicate-contentinfo': { enabled: true },
        'landmark-one-main': { enabled: true },
        'page-has-heading-one': { enabled: true },
        'region': { enabled: true },
        'skip-link': { enabled: true },
        'tabindex': { enabled: true },
        'form-field-multiple-labels': { enabled: true },
        'label': { enabled: true },
        'input-button-name': { enabled: true },
        'button-name': { enabled: true },
        'link-name': { enabled: true }
    },
    tags: ['wcag2a', 'wcag2aa', 'wcag21aa', 'best-practice']
};

// Global test timeout
jest.setTimeout(30000);

// Setup function to be called before each test
beforeEach(() => {
    // Reset any global state if needed
    console.log('Setting up accessibility test environment...');
});

afterEach(() => {
    // Cleanup after each test
    console.log('Cleaning up accessibility test environment...');
});
