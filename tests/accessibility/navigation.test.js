const puppeteer = require('puppeteer');
const { injectAxe, checkA11y } = require('axe-puppeteer');

describe('Navigation Accessibility Tests', () => {
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
        await page.goto('http://localhost:8000/', {
            waitUntil: 'networkidle0',
            timeout: 30000
        });
        await injectAxe(page);
    });

    test('should have accessible navigation structure', async () => {
        const navigation = await page.$('nav');
        expect(navigation).toBeTruthy();

        const navAttributes = await navigation.evaluate(el => ({
            role: el.getAttribute('role'),
            ariaLabel: el.getAttribute('aria-label'),
            id: el.id
        }));

        // Navigation should have proper role and aria-label
        expect(navAttributes.role === 'navigation' || navAttributes.ariaLabel).toBeTruthy();
    });

    test('should have accessible mobile menu toggle', async () => {
    // Test mobile menu button
        const mobileMenuButton = await page.$('button[aria-expanded]');
        if (mobileMenuButton) {
            const buttonAttributes = await mobileMenuButton.evaluate(el => ({
                ariaExpanded: el.getAttribute('aria-expanded'),
                ariaLabel: el.getAttribute('aria-label'),
                ariaControls: el.getAttribute('aria-controls')
            }));

            expect(buttonAttributes.ariaExpanded).toBeTruthy();
            expect(buttonAttributes.ariaLabel).toBeTruthy();

            // Test toggle functionality
            await mobileMenuButton.click();
            await page.waitForTimeout(500);

            const expandedState = await mobileMenuButton.evaluate(el =>
                el.getAttribute('aria-expanded')
            );
            expect(expandedState).toBe('true');

            // Close menu
            await mobileMenuButton.click();
            await page.waitForTimeout(500);

            const collapsedState = await mobileMenuButton.evaluate(el =>
                el.getAttribute('aria-expanded')
            );
            expect(collapsedState).toBe('false');
        }
    });

    test('should have keyboard accessible navigation links', async () => {
        const navLinks = await page.$$('nav a, nav button');

        for (const link of navLinks.slice(0, 5)) { // Test first 5 links
            const linkData = await link.evaluate(el => ({
                href: el.href || '',
                text: el.textContent.trim(),
                ariaLabel: el.getAttribute('aria-label'),
                role: el.getAttribute('role')
            }));

            // Each link should have accessible text
            expect(linkData.text || linkData.ariaLabel).toBeTruthy();

            // Focus should be visible
            await link.focus();
            const isFocused = await page.evaluate(() =>
                document.activeElement === arguments[0], link
            );
            expect(isFocused).toBeTruthy();
        }
    });

    test('should have proper current page indication', async () => {
    // Check for aria-current or visual indicators
        const currentPageLinks = await page.$$eval('nav a', links =>
            links.map(link => ({
                href: link.href,
                ariaCurrent: link.getAttribute('aria-current'),
                classes: link.className,
                text: link.textContent.trim()
            }))
        );

        // At least one link should indicate current page
        const hasCurrentPageIndicator = currentPageLinks.some(link =>
            link.ariaCurrent === 'page' ||
      link.classes.includes('active') ||
      link.classes.includes('current')
        );

        expect(hasCurrentPageIndicator).toBeTruthy();
    });

    test('should handle escape key to close mobile menu', async () => {
    // Test mobile viewport
        await page.setViewport({ width: 768, height: 1024 });
        await page.reload({ waitUntil: 'networkidle0' });

        const mobileMenuButton = await page.$('button[aria-expanded]');
        if (mobileMenuButton) {
            // Open menu
            await mobileMenuButton.click();
            await page.waitForTimeout(500);

            // Press Escape key
            await page.keyboard.press('Escape');
            await page.waitForTimeout(500);

            const menuState = await mobileMenuButton.evaluate(el =>
                el.getAttribute('aria-expanded')
            );
            expect(menuState).toBe('false');
        }

        // Reset viewport
        await page.setViewport({ width: 1280, height: 720 });
    });

    test('should have accessible breadcrumb navigation', async () => {
    // Navigate to a page that might have breadcrumbs
        await page.goto('http://localhost:8000/contact/', {
            waitUntil: 'networkidle0'
        });

        const breadcrumbs = await page.$('nav[aria-label*="breadcrumb"], ol, .breadcrumb');
        if (breadcrumbs) {
            const breadcrumbData = await breadcrumbs.evaluate(el => ({
                role: el.getAttribute('role'),
                ariaLabel: el.getAttribute('aria-label'),
                tag: el.tagName.toLowerCase()
            }));

            // Breadcrumbs should be properly labeled
            expect(
                breadcrumbData.ariaLabel?.includes('breadcrumb') ||
        breadcrumbData.role === 'navigation' ||
        breadcrumbData.tag === 'ol'
            ).toBeTruthy();
        }
    });

    test('should have accessible footer navigation', async () => {
        const footer = await page.$('footer');
        if (footer) {
            const footerLinks = await footer.$$('a');

            for (const link of footerLinks.slice(0, 3)) { // Test first 3 footer links
                const linkData = await link.evaluate(el => ({
                    text: el.textContent.trim(),
                    href: el.href,
                    ariaLabel: el.getAttribute('aria-label'),
                    title: el.title
                }));

                // Footer links should have accessible names
                expect(linkData.text || linkData.ariaLabel || linkData.title).toBeTruthy();

                // External links should be properly indicated
                if (linkData.href && !linkData.href.includes('localhost')) {
                    const hasExternalIndicator = await link.evaluate(el =>
                        el.getAttribute('target') === '_blank' &&
            el.getAttribute('rel')?.includes('noopener')
                    );
                    expect(hasExternalIndicator).toBeTruthy();
                }
            }
        }
    });
});
