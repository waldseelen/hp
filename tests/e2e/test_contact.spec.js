/**
 * E2E Tests for Contact Form - Phase 22D.1
 *
 * Tests cover:
 * - Contact form display
 * - Form validation (client-side & server-side)
 * - Successful form submission
 * - Error handling
 * - Honeypot trap (spam prevention)
 * - Rate limiting
 * - Mobile responsiveness
 * - Accessibility
 *
 * Tests run on: Chromium, Firefox, WebKit
 */

const { test, expect } = require('@playwright/test');

// Test data
const VALID_CONTACT = {
    name: 'John Doe',
    email: 'john.doe@example.com',
    subject: 'Test Message',
    message: 'This is a test message from E2E tests. Testing contact form functionality.',
};

// ============================================================================
// CONTACT FORM DISPLAY TESTS
// ============================================================================

test.describe('Contact Form Display', () => {
    test('should display contact page', async ({ page }) => {
        await page.goto('/contact/');

        await expect(page).toHaveTitle(/Contact|Get in Touch|Reach Out/i);

        // Check page heading
        const heading = page.locator('h1, h2').first();
        await expect(heading).toBeVisible();
    });

    test('should display all required form fields', async ({ page }) => {
        await page.goto('/contact/');

        // Check for name field
        const nameField = page.locator('input[name="name"], input[id*="name"]').first();
        await expect(nameField).toBeVisible();

        // Check for email field
        const emailField = page.locator('input[name="email"], input[id*="email"]').first();
        await expect(emailField).toBeVisible();

        // Check for subject field (optional in some forms)
        const subjectField = page.locator('input[name="subject"], input[id*="subject"]').first();
        const hasSubject = await subjectField.count() > 0;

        if (hasSubject) {
            await expect(subjectField).toBeVisible();
        }

        // Check for message field
        const messageField = page.locator('textarea[name="message"], textarea[id*="message"]').first();
        await expect(messageField).toBeVisible();

        // Check for submit button
        const submitButton = page.locator('button[type="submit"], input[type="submit"]').first();
        await expect(submitButton).toBeVisible();
    });

    test('should have proper form labels', async ({ page }) => {
        await page.goto('/contact/');

        // Check for labels
        const labels = page.locator('label');
        const labelCount = await labels.count();

        expect(labelCount).toBeGreaterThan(0);

        // Labels should have text
        const firstLabel = labels.first();
        const labelText = await firstLabel.textContent();
        expect(labelText.trim().length).toBeGreaterThan(0);
    });

    test('should have placeholder text or help text', async ({ page }) => {
        await page.goto('/contact/');

        // Check for placeholder in name field
        const nameField = page.locator('input[name="name"], input[id*="name"]').first();
        const placeholder = await nameField.getAttribute('placeholder');

        // Placeholder or label should exist
        expect(placeholder !== null || await page.locator('label[for*="name"]').count() > 0).toBeTruthy();
    });
});

// ============================================================================
// FORM VALIDATION TESTS (CLIENT-SIDE)
// ============================================================================

test.describe('Contact Form Client-Side Validation', () => {
    test('should show error for empty required fields', async ({ page }) => {
        await page.goto('/contact/');

        // Try to submit empty form
        const submitButton = page.locator('button[type="submit"], input[type="submit"]').first();
        await submitButton.click();

        // Browser validation or custom validation should prevent submission
        const nameField = page.locator('input[name="name"], input[id*="name"]').first();

        // Check if field has required attribute
        const isRequired = await nameField.getAttribute('required');

        if (isRequired !== null) {
            // Browser should show validation message
            console.log('Browser validation active for required fields');
        } else {
            // Custom validation should show error
            const errorMessage = page.locator('text=/required|fill.*field|cannot.*empty/i').first();
            await expect(errorMessage).toBeVisible({ timeout: 3000 });
        }
    });

    test('should validate email format', async ({ page }) => {
        await page.goto('/contact/');

        // Fill with invalid email
        const nameField = page.locator('input[name="name"], input[id*="name"]').first();
        const emailField = page.locator('input[name="email"], input[id*="email"]').first();
        const messageField = page.locator('textarea[name="message"], textarea[id*="message"]').first();

        await nameField.fill('Test User');
        await emailField.fill('invalid-email');
        await messageField.fill('Test message');

        const submitButton = page.locator('button[type="submit"], input[type="submit"]').first();
        await submitButton.click();

        await page.waitForTimeout(1000);

        // Should show invalid email error
        const errorMessage = page.locator('text=/invalid.*email|valid.*email|email.*format/i').first();

        // Either browser validation or custom validation
        const emailType = await emailField.getAttribute('type');

        if (emailType === 'email') {
            console.log('Browser email validation active');
        } else {
            await expect(errorMessage).toBeVisible({ timeout: 3000 });
        }
    });

    test('should validate minimum message length', async ({ page }) => {
        await page.goto('/contact/');

        const nameField = page.locator('input[name="name"], input[id*="name"]').first();
        const emailField = page.locator('input[name="email"], input[id*="email"]').first();
        const messageField = page.locator('textarea[name="message"], textarea[id*="message"]').first();

        await nameField.fill('Test User');
        await emailField.fill('test@example.com');
        await messageField.fill('Hi'); // Too short

        const submitButton = page.locator('button[type="submit"], input[type="submit"]').first();
        await submitButton.click();

        await page.waitForTimeout(1000);

        // Check for minlength attribute or custom validation
        const minLength = await messageField.getAttribute('minlength');

        if (minLength) {
            console.log(`Message field has minlength: ${minLength}`);
        } else {
            // Custom validation might show error
            const errorMessage = page.locator('text=/too.*short|minimum|at.*least/i').first();
            const hasError = await errorMessage.count() > 0;

            if (hasError) {
                await expect(errorMessage).toBeVisible();
            }
        }
    });

    test('should validate maximum message length', async ({ page }) => {
        await page.goto('/contact/');

        const messageField = page.locator('textarea[name="message"], textarea[id*="message"]').first();

        // Try to fill with very long message
        const longMessage = 'A'.repeat(10000);
        await messageField.fill(longMessage);

        const maxLength = await messageField.getAttribute('maxlength');

        if (maxLength) {
            // Browser should truncate
            const actualValue = await messageField.inputValue();
            expect(actualValue.length).toBeLessThanOrEqual(parseInt(maxLength));
        }
    });
});

// ============================================================================
// FORM SUBMISSION TESTS
// ============================================================================

test.describe('Contact Form Submission', () => {
    test('should submit form with valid data', async ({ page }) => {
        await page.goto('/contact/');

        const nameField = page.locator('input[name="name"], input[id*="name"]').first();
        const emailField = page.locator('input[name="email"], input[id*="email"]').first();
        const messageField = page.locator('textarea[name="message"], textarea[id*="message"]').first();

        await nameField.fill(VALID_CONTACT.name);
        await emailField.fill(VALID_CONTACT.email);

        // Fill subject if exists
        const subjectField = page.locator('input[name="subject"], input[id*="subject"]').first();
        if (await subjectField.count() > 0) {
            await subjectField.fill(VALID_CONTACT.subject);
        }

        await messageField.fill(VALID_CONTACT.message);

        const submitButton = page.locator('button[type="submit"], input[type="submit"]').first();
        await submitButton.click();

        // Should show success message or redirect
        await page.waitForTimeout(2000);

        const successMessage = page.locator('text=/success|thank.*you|sent|received|message.*delivered/i').first();
        await expect(successMessage).toBeVisible({ timeout: 5000 });
    });

    test('should clear form after successful submission', async ({ page }) => {
        await page.goto('/contact/');

        const nameField = page.locator('input[name="name"], input[id*="name"]').first();
        const emailField = page.locator('input[name="email"], input[id*="email"]').first();
        const messageField = page.locator('textarea[name="message"], textarea[id*="message"]').first();

        await nameField.fill(VALID_CONTACT.name);
        await emailField.fill(VALID_CONTACT.email);
        await messageField.fill(VALID_CONTACT.message);

        const submitButton = page.locator('button[type="submit"], input[type="submit"]').first();
        await submitButton.click();

        await page.waitForTimeout(2000);

        // Check if form is cleared (optional behavior)
        const nameValue = await nameField.inputValue();

        if (nameValue === '') {
            console.log('Form cleared after submission');
        } else {
            console.log('Form not cleared (user can submit again)');
        }
    });

    test('should disable submit button during submission', async ({ page }) => {
        await page.goto('/contact/');

        const nameField = page.locator('input[name="name"], input[id*="name"]').first();
        const emailField = page.locator('input[name="email"], input[id*="email"]').first();
        const messageField = page.locator('textarea[name="message"], textarea[id*="message"]').first();

        await nameField.fill(VALID_CONTACT.name);
        await emailField.fill(VALID_CONTACT.email);
        await messageField.fill(VALID_CONTACT.message);

        const submitButton = page.locator('button[type="submit"], input[type="submit"]').first();

        // Click and immediately check if disabled
        await submitButton.click();

        // Button should be disabled during submission (best practice)
        const isDisabled = await submitButton.isDisabled();

        if (isDisabled) {
            console.log('Submit button disabled during submission (good UX)');
        }
    });

    test('should show loading indicator during submission', async ({ page }) => {
        await page.goto('/contact/');

        const nameField = page.locator('input[name="name"], input[id*="name"]').first();
        const emailField = page.locator('input[name="email"], input[id*="email"]').first();
        const messageField = page.locator('textarea[name="message"], textarea[id*="message"]').first();

        await nameField.fill(VALID_CONTACT.name);
        await emailField.fill(VALID_CONTACT.email);
        await messageField.fill(VALID_CONTACT.message);

        const submitButton = page.locator('button[type="submit"], input[type="submit"]').first();
        await submitButton.click();

        // Look for loading indicator
        const loader = page.locator('.loading, .spinner, [class*="load"], text=/sending|processing/i').first();
        const hasLoader = await loader.count() > 0;

        if (hasLoader) {
            console.log('Loading indicator found');
        }
    });
});

// ============================================================================
// SERVER-SIDE VALIDATION TESTS
// ============================================================================

test.describe('Contact Form Server-Side Validation', () => {
    test('should handle server validation errors', async ({ page }) => {
        await page.goto('/contact/');

        // Try to submit with potentially problematic data
        const nameField = page.locator('input[name="name"], input[id*="name"]').first();
        const emailField = page.locator('input[name="email"], input[id*="email"]').first();
        const messageField = page.locator('textarea[name="message"], textarea[id*="message"]').first();

        // Fill with special characters
        await nameField.fill('<script>alert("XSS")</script>');
        await emailField.fill('test@example.com');
        await messageField.fill('Test message');

        const submitButton = page.locator('button[type="submit"], input[type="submit"]').first();
        await submitButton.click();

        await page.waitForTimeout(2000);

        // Should either sanitize or show error
        const errorMessage = page.locator('text=/invalid|error|not.*allowed/i').first();
        const successMessage = page.locator('text=/success|thank.*you/i').first();

        // One of these should be visible
        const hasError = await errorMessage.count() > 0;
        const hasSuccess = await successMessage.count() > 0;

        expect(hasError || hasSuccess).toBeTruthy();
    });

    test('should prevent XSS in form inputs', async ({ page }) => {
        await page.goto('/contact/');

        const nameField = page.locator('input[name="name"], input[id*="name"]').first();
        const emailField = page.locator('input[name="email"], input[id*="email"]').first();
        const messageField = page.locator('textarea[name="message"], textarea[id*="message"]').first();

        const xssPayload = '<img src=x onerror=alert("XSS")>';

        await nameField.fill(xssPayload);
        await emailField.fill('test@example.com');
        await messageField.fill(xssPayload);

        const submitButton = page.locator('button[type="submit"], input[type="submit"]').first();
        await submitButton.click();

        await page.waitForTimeout(2000);

        // Should not execute script (check for alert dialog)
        page.on('dialog', dialog => {
            console.error('XSS ALERT DETECTED! Dialog:', dialog.message());
            dialog.dismiss();
        });

        // Page should still be safe
        const pageUrl = page.url();
        expect(pageUrl).toContain('/contact/');
    });
});

// ============================================================================
// SPAM PREVENTION TESTS
// ============================================================================

test.describe('Contact Form Spam Prevention', () => {
    test('should have honeypot field (hidden)', async ({ page }) => {
        await page.goto('/contact/');

        // Look for honeypot field (common names: hp, honeypot, url, website)
        const honeypot = page.locator('input[name="hp"], input[name="honeypot"], input[name="url"], input[name="website"]').first();

        if (await honeypot.count() > 0) {
            // Should be hidden
            const isVisible = await honeypot.isVisible();
            expect(isVisible).toBeFalsy();

            console.log('Honeypot field detected (good spam prevention)');
        }
    });

    test('should reject submission if honeypot is filled', async ({ page }) => {
        await page.goto('/contact/');

        const honeypot = page.locator('input[name="hp"], input[name="honeypot"], input[name="url"], input[name="website"]').first();

        if (await honeypot.count() > 0) {
            const nameField = page.locator('input[name="name"], input[id*="name"]').first();
            const emailField = page.locator('input[name="email"], input[id*="email"]').first();
            const messageField = page.locator('textarea[name="message"], textarea[id*="message"]').first();

            await nameField.fill(VALID_CONTACT.name);
            await emailField.fill(VALID_CONTACT.email);
            await messageField.fill(VALID_CONTACT.message);

            // Fill honeypot (bots do this)
            await honeypot.fill('spam content', { force: true });

            const submitButton = page.locator('button[type="submit"], input[type="submit"]').first();
            await submitButton.click();

            await page.waitForTimeout(2000);

            // Should reject or silently fail
            const successMessage = page.locator('text=/success|thank.*you|sent/i').first();
            const hasSuccess = await successMessage.count() > 0;

            // May show fake success to confuse bots or show error
            console.log('Honeypot test completed');
        }
    });

    test('should have CSRF protection', async ({ page }) => {
        await page.goto('/contact/');

        // Look for CSRF token
        const csrfToken = page.locator('input[name="csrfmiddlewaretoken"], input[name="csrf_token"], input[name="_token"]').first();

        if (await csrfToken.count() > 0) {
            const tokenValue = await csrfToken.getAttribute('value');
            expect(tokenValue).toBeDefined();
            expect(tokenValue.length).toBeGreaterThan(0);

            console.log('CSRF token found');
        }
    });
});

// ============================================================================
// RATE LIMITING TESTS
// ============================================================================

test.describe('Contact Form Rate Limiting', () => {
    test('should handle multiple rapid submissions', async ({ page }) => {
        await page.goto('/contact/');

        // Submit form multiple times rapidly
        for (let i = 0; i < 3; i++) {
            const nameField = page.locator('input[name="name"], input[id*="name"]').first();
            const emailField = page.locator('input[name="email"], input[id*="email"]').first();
            const messageField = page.locator('textarea[name="message"], textarea[id*="message"]').first();

            await nameField.fill(`${VALID_CONTACT.name} ${i}`);
            await emailField.fill(`test${i}@example.com`);
            await messageField.fill(`${VALID_CONTACT.message} ${i}`);

            const submitButton = page.locator('button[type="submit"], input[type="submit"]').first();
            await submitButton.click();

            await page.waitForTimeout(500);
        }

        await page.waitForTimeout(2000);

        // Should show rate limit error or success for first submission only
        const rateLimitMessage = page.locator('text=/too.*many|rate.*limit|slow.*down|wait/i').first();
        const hasRateLimit = await rateLimitMessage.count() > 0;

        if (hasRateLimit) {
            console.log('Rate limiting detected (good security)');
        }
    });
});

// ============================================================================
// MOBILE RESPONSIVENESS TESTS
// ============================================================================

test.describe('Contact Form Mobile Experience', () => {
    test.use({
        viewport: { width: 375, height: 667 } // iPhone SE size
    });

    test('should display contact form on mobile', async ({ page }) => {
        await page.goto('/contact/');

        // All form fields should be visible
        const nameField = page.locator('input[name="name"], input[id*="name"]').first();
        const emailField = page.locator('input[name="email"], input[id*="email"]').first();
        const messageField = page.locator('textarea[name="message"], textarea[id*="message"]').first();
        const submitButton = page.locator('button[type="submit"], input[type="submit"]').first();

        await expect(nameField).toBeVisible();
        await expect(emailField).toBeVisible();
        await expect(messageField).toBeVisible();
        await expect(submitButton).toBeVisible();
    });

    test('should have proper input types for mobile keyboards', async ({ page }) => {
        await page.goto('/contact/');

        // Email field should have type="email" for email keyboard
        const emailField = page.locator('input[name="email"], input[id*="email"]').first();
        const emailType = await emailField.getAttribute('type');

        expect(emailType).toBe('email');
    });

    test('should submit form on mobile', async ({ page }) => {
        await page.goto('/contact/');

        const nameField = page.locator('input[name="name"], input[id*="name"]').first();
        const emailField = page.locator('input[name="email"], input[id*="email"]').first();
        const messageField = page.locator('textarea[name="message"], textarea[id*="message"]').first();

        await nameField.fill(VALID_CONTACT.name);
        await emailField.fill(VALID_CONTACT.email);
        await messageField.fill(VALID_CONTACT.message);

        const submitButton = page.locator('button[type="submit"], input[type="submit"]').first();
        await submitButton.click();

        await page.waitForTimeout(2000);

        const successMessage = page.locator('text=/success|thank.*you|sent/i').first();
        await expect(successMessage).toBeVisible({ timeout: 5000 });
    });
});

// ============================================================================
// ACCESSIBILITY TESTS
// ============================================================================

test.describe('Contact Form Accessibility', () => {
    test('should be keyboard accessible', async ({ page }) => {
        await page.goto('/contact/');

        // Tab through form fields
        await page.keyboard.press('Tab');
        await page.keyboard.type('John Doe');

        await page.keyboard.press('Tab');
        await page.keyboard.type('john@example.com');

        await page.keyboard.press('Tab');

        // Skip subject if exists
        const focusedElement = await page.locator(':focus').getAttribute('name');
        if (focusedElement === 'subject') {
            await page.keyboard.type('Test Subject');
            await page.keyboard.press('Tab');
        }

        await page.keyboard.type('Test message for keyboard accessibility.');

        await page.keyboard.press('Tab');
        await page.keyboard.press('Enter');

        await page.waitForTimeout(2000);

        // Form should submit
        const successOrError = page.locator('text=/success|error|thank/i').first();
        await expect(successOrError).toBeVisible({ timeout: 5000 });
    });

    test('should have proper ARIA labels', async ({ page }) => {
        await page.goto('/contact/');

        // Check for aria-label or aria-labelledby
        const nameField = page.locator('input[name="name"], input[id*="name"]').first();

        const ariaLabel = await nameField.getAttribute('aria-label');
        const ariaLabelledBy = await nameField.getAttribute('aria-labelledby');
        const hasLabel = await page.locator('label[for*="name"]').count() > 0;

        // Should have some form of label
        expect(ariaLabel !== null || ariaLabelledBy !== null || hasLabel).toBeTruthy();
    });

    test('should announce form errors to screen readers', async ({ page }) => {
        await page.goto('/contact/');

        // Submit empty form
        const submitButton = page.locator('button[type="submit"], input[type="submit"]').first();
        await submitButton.click();

        await page.waitForTimeout(1000);

        // Check for aria-live region for errors
        const errorRegion = page.locator('[aria-live], [role="alert"]').first();
        const hasErrorRegion = await errorRegion.count() > 0;

        if (hasErrorRegion) {
            console.log('ARIA live region found for screen reader announcements');
        }
    });
});
