const puppeteer = require('puppeteer');
const { injectAxe, checkA11y, getViolations } = require('axe-puppeteer');

describe('Home Page Accessibility Tests', () => {
    let browser;
    let page;

    beforeAll(async () => {
        browser = await puppeteer.launch({
            headless: true,
            args: ['--no-sandbox', '--disable-setuid-sandbox']
        });
        page = await browser.newPage();

        // Set viewport for consistent testing
        await page.setViewport({ width: 1280, height: 720 });
    });

    afterAll(async () => {
        if (browser) {
            await browser.close();
        }
    });

    beforeEach(async () => {
    // Navigate to home page
        await page.goto('http://localhost:8000/', {
            waitUntil: 'networkidle0',
            timeout: 30000
        });

        // Inject axe-core
        await injectAxe(page);
    });

    test('should have no accessibility violations on home page', async () => {
        const results = await checkA11y(page, null, {
            ...global.axeConfig,
            reporter: 'v2'
        });

        // Should have no violations
        expect(results.violations).toHaveLength(0);

        // Log any violations for debugging
        if (results.violations.length > 0) {
            console.log('Accessibility violations found:',
                JSON.stringify(results.violations, null, 2));
        }
    });

    test('should have proper heading hierarchy', async () => {
        const headings = await page.$$eval('h1, h2, h3, h4, h5, h6', elements =>
            elements.map(el => ({
                tag: el.tagName.toLowerCase(),
                text: el.textContent.trim(),
                level: parseInt(el.tagName.charAt(1))
            }))
        );

        // Should have exactly one h1
        const h1Count = headings.filter(h => h.tag === 'h1').length;
        expect(h1Count).toBe(1);

        // Check heading hierarchy (no skipped levels)
        const levels = headings.map(h => h.level).sort((a, b) => a - b);
        for (let i = 1; i < levels.length; i++) {
            expect(levels[i] - levels[i - 1]).toBeLessThanOrEqual(1);
        }
    });

    test('should have skip navigation links', async () => {
    // Check if skip links exist
        const skipLinks = await page.$$('[href="#main-content"], [href="#navigation"]');
        expect(skipLinks.length).toBeGreaterThan(0);

        // Test skip link functionality
        await page.keyboard.press('Tab');
        const focusedElement = await page.evaluate(() => document.activeElement.textContent);
        expect(focusedElement).toMatch(/skip to/i);
    });

    test('should have proper ARIA landmarks', async () => {
    // Check for main landmark
        const main = await page.$('main[role="main"], main');
        expect(main).toBeTruthy();

        // Check for navigation landmark
        const nav = await page.$('nav[role="navigation"], nav');
        expect(nav).toBeTruthy();

        // Check for contentinfo landmark (footer)
        const footer = await page.$('footer[role="contentinfo"], footer');
        expect(footer).toBeTruthy();
    });

    test('should have keyboard navigation working', async () => {
    // Test tab navigation through interactive elements
        const interactiveElements = await page.$$('a, button, input, textarea, select, [tabindex]:not([tabindex="-1"])');

        let tabCount = 0;
        const focusedElements = [];

        // Tab through first 10 elements to test navigation
        for (let i = 0; i < Math.min(10, interactiveElements.length); i++) {
            await page.keyboard.press('Tab');
            tabCount++;

            const focusedElement = await page.evaluate(() => ({
                tag: document.activeElement.tagName.toLowerCase(),
                text: document.activeElement.textContent?.trim() || '',
                id: document.activeElement.id || '',
                ariaLabel: document.activeElement.getAttribute('aria-label') || ''
            }));

            focusedElements.push(focusedElement);
        }

        // Should have navigated through elements
        expect(tabCount).toBeGreaterThan(0);
        expect(focusedElements.length).toBeGreaterThan(0);
    });

    test('should have proper form labels and accessibility', async () => {
    // Check if any forms exist on the page
        const forms = await page.$$('form');

        for (const form of forms) {
            const inputs = await form.$$('input, textarea, select');

            for (const input of inputs) {
                const inputData = await input.evaluate(el => ({
                    id: el.id,
                    type: el.type,
                    hasLabel: !!document.querySelector(`label[for="${el.id}"]`),
                    ariaLabel: el.getAttribute('aria-label'),
                    ariaLabelledBy: el.getAttribute('aria-labelledby'),
                    ariaDescribedBy: el.getAttribute('aria-describedby')
                }));

                // Each input should have some form of label
                const hasAccessibleName = inputData.hasLabel ||
                                 inputData.ariaLabel ||
                                 inputData.ariaLabelledBy;

                if (inputData.type !== 'hidden') {
                    expect(hasAccessibleName).toBeTruthy();
                }
            }
        }
    });

    test('should have proper color contrast ratios', async () => {
        const results = await checkA11y(page, null, {
            rules: {
                'color-contrast': { enabled: true }
            }
        });

        const contrastViolations = results.violations.filter(
            violation => violation.id === 'color-contrast'
        );

        expect(contrastViolations).toHaveLength(0);
    });

    test('should have images with alt text or aria-hidden', async () => {
        const images = await page.$$eval('img', images =>
            images.map(img => ({
                src: img.src,
                alt: img.alt,
                ariaHidden: img.getAttribute('aria-hidden'),
                role: img.getAttribute('role')
            }))
        );

        images.forEach(img => {
            // Images should either have alt text or be marked as decorative
            const hasAltText = img.alt && img.alt.trim() !== '';
            const isDecorative = img.ariaHidden === 'true' || img.role === 'presentation';

            expect(hasAltText || isDecorative).toBeTruthy();
        });
    });

    test('should handle dark/light theme toggle accessibility', async () => {
    // Find theme toggle button
        const themeToggle = await page.$('button[aria-label*="mode"], button[aria-label*="theme"]');

        if (themeToggle) {
            // Check initial state
            const initialLabel = await themeToggle.evaluate(el => el.getAttribute('aria-label'));
            expect(initialLabel).toBeTruthy();

            // Toggle theme
            await themeToggle.click();
            await page.waitForTimeout(500); // Wait for theme change

            // Check if label updated
            const newLabel = await themeToggle.evaluate(el => el.getAttribute('aria-label'));
            expect(newLabel).toBeTruthy();
        }
    });
});
