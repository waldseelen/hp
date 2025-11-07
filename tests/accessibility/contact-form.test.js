const puppeteer = require('puppeteer');
const { injectAxe, checkA11y } = require('axe-puppeteer');

describe('Contact Form Accessibility Tests', () => {
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

    beforeEach(async () => {
        await page.goto('http://localhost:8000/contact/', {
            waitUntil: 'networkidle0',
            timeout: 30000
        });
        await injectAxe(page);
    });

    test('should have no accessibility violations on contact form', async () => {
        const results = await checkA11y(page, null, {
            ...global.axeConfig,
            reporter: 'v2'
        });

        expect(results.violations).toHaveLength(0);

        if (results.violations.length > 0) {
            console.log('Contact form violations:',
                JSON.stringify(results.violations, null, 2));
        }
    });

    test('should have proper form labels and associations', async () => {
        const formInputs = await page.$$eval('form input, form textarea', inputs =>
            inputs.map(input => ({
                id: input.id,
                name: input.name,
                type: input.type,
                required: input.required,
                hasLabel: !!document.querySelector(`label[for="${input.id}"]`),
                ariaLabel: input.getAttribute('aria-label'),
                ariaLabelledBy: input.getAttribute('aria-labelledby'),
                ariaDescribedBy: input.getAttribute('aria-describedby'),
                autocomplete: input.getAttribute('autocomplete')
            }))
        );

        formInputs.forEach(input => {
            if (input.type !== 'hidden') {
                // Each visible input should have an accessible name
                const hasAccessibleName = input.hasLabel ||
                                 input.ariaLabel ||
                                 input.ariaLabelledBy;
                expect(hasAccessibleName).toBeTruthy();

                // Required fields should be properly marked
                if (input.required) {
                    expect(input.hasLabel || input.ariaLabel).toBeTruthy();
                }
            }
        });
    });

    test('should have proper form validation accessibility', async () => {
    // Try to submit empty form to trigger validation
        const submitButton = await page.$('button[type="submit"], input[type="submit"]');
        if (submitButton) {
            await submitButton.click();
            await page.waitForTimeout(1000);

            // Check for validation messages
            const validationMessages = await page.$$eval('[aria-live], .error-message, .invalid-feedback', msgs =>
                msgs.map(msg => ({
                    text: msg.textContent.trim(),
                    ariaLive: msg.getAttribute('aria-live'),
                    role: msg.getAttribute('role')
                }))
            );

            // If there are validation messages, they should be accessible
            validationMessages.forEach(msg => {
                expect(msg.ariaLive || msg.role).toBeTruthy();
            });
        }
    });

    test('should have keyboard navigation through form fields', async () => {
        const formFields = await page.$$('form input:not([type="hidden"]), form textarea, form select, form button');

        // Tab through all form fields
        for (let i = 0; i < formFields.length; i++) {
            await page.keyboard.press('Tab');

            const focusedElement = await page.evaluate(() => ({
                tag: document.activeElement.tagName.toLowerCase(),
                type: document.activeElement.type || '',
                id: document.activeElement.id || '',
                name: document.activeElement.name || ''
            }));

            // Focused element should be a form control
            expect(['input', 'textarea', 'select', 'button']).toContain(focusedElement.tag);
        }
    });

    test('should have proper ARIA attributes for form', async () => {
        const form = await page.$('form');
        if (form) {
            const formAttributes = await form.evaluate(el => ({
                role: el.getAttribute('role'),
                ariaLabel: el.getAttribute('aria-label'),
                ariaLabelledBy: el.getAttribute('aria-labelledby')
            }));

            // Form should have proper role or aria-label
            expect(formAttributes.role || formAttributes.ariaLabel || formAttributes.ariaLabelledBy).toBeTruthy();
        }
    });

    test('should handle honeypot field accessibility', async () => {
    // Check if honeypot field is properly hidden from assistive technology
        const honeypotField = await page.$('input[name="website"]');
        if (honeypotField) {
            const honeypotAttributes = await honeypotField.evaluate(el => ({
                ariaHidden: el.getAttribute('aria-hidden'),
                tabIndex: el.getAttribute('tabindex'),
                display: window.getComputedStyle(el).display,
                visibility: window.getComputedStyle(el).visibility
            }));

            // Honeypot should be hidden from assistive technology
            expect(
                honeypotAttributes.ariaHidden === 'true' ||
        honeypotAttributes.tabIndex === '-1' ||
        honeypotAttributes.display === 'none' ||
        honeypotAttributes.visibility === 'hidden'
            ).toBeTruthy();
        }
    });
});
