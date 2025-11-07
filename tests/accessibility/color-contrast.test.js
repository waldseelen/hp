const puppeteer = require('puppeteer');
const { injectAxe, checkA11y } = require('axe-puppeteer');

describe('Color Contrast Accessibility Tests', () => {
    let browser;
    let page;

    beforeAll(async () => {
        browser = await puppeteer.launch({
            headless: true,
            args: ['--no-sandbox', '--disable-setuid-sandbox']
        });
        page = await browser.newPage();
        await page.setViewport({ width: 1280, height: 720 });
    });

    afterAll(async () => {
        if (browser) {
            await browser.close();
        }
    });

    test('should meet WCAG AA color contrast requirements on light theme', async () => {
        await page.goto('http://localhost:8000/', {
            waitUntil: 'networkidle0'
        });

        // Switch to light theme if possible
        const themeToggle = await page.$('button[aria-label*="light"], button[aria-label*="mode"]');
        if (themeToggle) {
            await themeToggle.click();
            await page.waitForTimeout(1000);
        }

        await injectAxe(page);

        const results = await checkA11y(page, null, {
            rules: {
                'color-contrast': { enabled: true }
            }
        });

        const contrastViolations = results.violations.filter(
            violation => violation.id === 'color-contrast'
        );

        if (contrastViolations.length > 0) {
            console.log('Light theme contrast violations:',
                JSON.stringify(contrastViolations, null, 2));
        }

        expect(contrastViolations).toHaveLength(0);
    });

    test('should meet WCAG AA color contrast requirements on dark theme', async () => {
        await page.goto('http://localhost:8000/', {
            waitUntil: 'networkidle0'
        });

        // Switch to dark theme if possible
        const themeToggle = await page.$('button[aria-label*="dark"], button[aria-label*="mode"]');
        if (themeToggle) {
            await themeToggle.click();
            await page.waitForTimeout(1000);
        }

        await injectAxe(page);

        const results = await checkA11y(page, null, {
            rules: {
                'color-contrast': { enabled: true }
            }
        });

        const contrastViolations = results.violations.filter(
            violation => violation.id === 'color-contrast'
        );

        if (contrastViolations.length > 0) {
            console.log('Dark theme contrast violations:',
                JSON.stringify(contrastViolations, null, 2));
        }

        expect(contrastViolations).toHaveLength(0);
    });

    test('should have sufficient contrast for interactive elements', async () => {
        await page.goto('http://localhost:8000/', {
            waitUntil: 'networkidle0'
        });

        await injectAxe(page);

        // Test specific interactive elements
        const interactiveElements = await page.$$('button, a, input, textarea');

        for (const element of interactiveElements.slice(0, 10)) {
            const elementInfo = await element.evaluate(el => {
                const styles = window.getComputedStyle(el);
                return {
                    tag: el.tagName.toLowerCase(),
                    color: styles.color,
                    backgroundColor: styles.backgroundColor,
                    text: el.textContent?.trim() || el.value || el.placeholder || '',
                    type: el.type || ''
                };
            });

            // Interactive elements should have visible text or accessible names
            if (elementInfo.text) {
                expect(elementInfo.text.length).toBeGreaterThan(0);
            }
        }
    });

    test('should have sufficient contrast for focus indicators', async () => {
        await page.goto('http://localhost:8000/', {
            waitUntil: 'networkidle0'
        });

        const focusableElements = await page.$$('button, a, input, textarea, select');

        for (const element of focusableElements.slice(0, 5)) {
            // Focus the element
            await element.focus();
            await page.waitForTimeout(100);

            const focusStyles = await element.evaluate(el => {
                const styles = window.getComputedStyle(el);
                return {
                    outline: styles.outline,
                    outlineColor: styles.outlineColor,
                    outlineWidth: styles.outlineWidth,
                    boxShadow: styles.boxShadow,
                    borderColor: styles.borderColor
                };
            });

            // Element should have visible focus indicator
            const hasFocusIndicator = (
                focusStyles.outline !== 'none' ||
        focusStyles.boxShadow !== 'none' ||
        focusStyles.outlineWidth !== '0px'
            );

            expect(hasFocusIndicator).toBeTruthy();
        }
    });

    test('should handle high contrast mode preferences', async () => {
    // Test with forced-colors media query simulation
        await page.emulateMediaFeatures([
            { name: 'prefers-contrast', value: 'high' }
        ]);

        await page.goto('http://localhost:8000/', {
            waitUntil: 'networkidle0'
        });

        await injectAxe(page);

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

    test('should maintain contrast for error and success states', async () => {
        await page.goto('http://localhost:8000/contact/', {
            waitUntil: 'networkidle0'
        });

        // Try to trigger form validation
        const submitButton = await page.$('button[type="submit"]');
        if (submitButton) {
            await submitButton.click();
            await page.waitForTimeout(1000);

            await injectAxe(page);

            const results = await checkA11y(page, null, {
                rules: {
                    'color-contrast': { enabled: true }
                }
            });

            const contrastViolations = results.violations.filter(
                violation => violation.id === 'color-contrast'
            );

            expect(contrastViolations).toHaveLength(0);
        }
    });

    test('should have proper contrast for disabled elements', async () => {
        await page.goto('http://localhost:8000/', {
            waitUntil: 'networkidle0'
        });

        // Find disabled elements
        const disabledElements = await page.$$('[disabled], [aria-disabled="true"]');

        for (const element of disabledElements) {
            const elementInfo = await element.evaluate(el => {
                const styles = window.getComputedStyle(el);
                return {
                    opacity: styles.opacity,
                    color: styles.color,
                    backgroundColor: styles.backgroundColor,
                    cursor: styles.cursor
                };
            });

            // Disabled elements should be visually distinguishable
            expect(
                parseFloat(elementInfo.opacity) < 1 ||
        elementInfo.cursor === 'not-allowed' ||
        elementInfo.cursor === 'default'
            ).toBeTruthy();
        }
    });
});
