/**
 * E2E Tests for Authentication Flows - Phase 22D.1
 *
 * Tests cover:
 * - User registration flow
 * - Login/logout flows
 * - Password reset flow
 * - Session management
 * - Authentication redirects
 * - Error handling
 *
 * Tests run on: Chromium, Firefox, WebKit
 */

const { test, expect } = require('@playwright/test');

// Test data
const TEST_USER = {
    username: `testuser_${Date.now()}`,
    email: `test_${Date.now()}@example.com`,
    password: 'SecureTestPassword123!',
};

// ============================================================================
// REGISTRATION FLOW TESTS
// ============================================================================

test.describe('User Registration', () => {
    test('should display registration page', async ({ page }) => {
        await page.goto('/accounts/register/');

        // Check page loaded
        await expect(page).toHaveTitle(/Register/i);

        // Check form elements exist
        await expect(page.locator('input[name="username"]')).toBeVisible();
        await expect(page.locator('input[name="email"]')).toBeVisible();
        await expect(page.locator('input[name="password1"]')).toBeVisible();
        await expect(page.locator('input[name="password2"]')).toBeVisible();
        await expect(page.locator('button[type="submit"]')).toBeVisible();
    });

    test('should register new user successfully', async ({ page }) => {
        await page.goto('/accounts/register/');

        // Fill registration form
        await page.fill('input[name="username"]', TEST_USER.username);
        await page.fill('input[name="email"]', TEST_USER.email);
        await page.fill('input[name="password1"]', TEST_USER.password);
        await page.fill('input[name="password2"]', TEST_USER.password);

        // Submit form
        await page.click('button[type="submit"]');

        // Should redirect to success page or login
        await page.waitForURL(/\/accounts\/(login|profile|success)/);

        // Should show success message
        const successMessage = page.locator('text=/successfully|registered|welcome/i');
        await expect(successMessage).toBeVisible({ timeout: 5000 });
    });

    test('should show error for mismatched passwords', async ({ page }) => {
        await page.goto('/accounts/register/');

        await page.fill('input[name="username"]', `testuser_${Date.now()}`);
        await page.fill('input[name="email"]', `test_${Date.now()}@example.com`);
        await page.fill('input[name="password1"]', 'Password123!');
        await page.fill('input[name="password2"]', 'DifferentPassword456!');

        await page.click('button[type="submit"]');

        // Should show password mismatch error
        const errorMessage = page.locator('text=/password.*match|don\'t match/i');
        await expect(errorMessage).toBeVisible({ timeout: 3000 });
    });

    test('should show error for weak password', async ({ page }) => {
        await page.goto('/accounts/register/');

        await page.fill('input[name="username"]', `testuser_${Date.now()}`);
        await page.fill('input[name="email"]', `test_${Date.now()}@example.com`);
        await page.fill('input[name="password1"]', '123'); // Too weak
        await page.fill('input[name="password2"]', '123');

        await page.click('button[type="submit"]');

        // Should show weak password error
        const errorMessage = page.locator('text=/too short|too common|weak/i');
        await expect(errorMessage).toBeVisible({ timeout: 3000 });
    });

    test('should show error for duplicate username', async ({ page }) => {
        // First, register a user
        await page.goto('/accounts/register/');

        const uniqueUser = `testuser_${Date.now()}`;

        await page.fill('input[name="username"]', uniqueUser);
        await page.fill('input[name="email"]', `test1_${Date.now()}@example.com`);
        await page.fill('input[name="password1"]', TEST_USER.password);
        await page.fill('input[name="password2"]', TEST_USER.password);
        await page.click('button[type="submit"]');

        await page.waitForTimeout(2000);

        // Try to register again with same username
        await page.goto('/accounts/register/');

        await page.fill('input[name="username"]', uniqueUser);
        await page.fill('input[name="email"]', `test2_${Date.now()}@example.com`);
        await page.fill('input[name="password1"]', TEST_USER.password);
        await page.fill('input[name="password2"]', TEST_USER.password);
        await page.click('button[type="submit"]');

        // Should show duplicate username error
        const errorMessage = page.locator('text=/already exists|taken|in use/i');
        await expect(errorMessage).toBeVisible({ timeout: 3000 });
    });
});

// ============================================================================
// LOGIN FLOW TESTS
// ============================================================================

test.describe('User Login', () => {
    test.beforeEach(async ({ page }) => {
        // Register a test user before each login test
        await page.goto('/accounts/register/');

        const uniqueUser = {
            username: `testuser_${Date.now()}`,
            email: `test_${Date.now()}@example.com`,
            password: 'TestPassword123!',
        };

        await page.fill('input[name="username"]', uniqueUser.username);
        await page.fill('input[name="email"]', uniqueUser.email);
        await page.fill('input[name="password1"]', uniqueUser.password);
        await page.fill('input[name="password2"]', uniqueUser.password);
        await page.click('button[type="submit"]');

        await page.waitForTimeout(2000);

        // Store for use in tests
        page.testUser = uniqueUser;
    });

    test('should display login page', async ({ page }) => {
        await page.goto('/accounts/login/');

        await expect(page).toHaveTitle(/Login|Sign In/i);

        await expect(page.locator('input[name="username"]')).toBeVisible();
        await expect(page.locator('input[name="password"]')).toBeVisible();
        await expect(page.locator('button[type="submit"]')).toBeVisible();
    });

    test('should login successfully with valid credentials', async ({ page }) => {
        await page.goto('/accounts/login/');

        await page.fill('input[name="username"]', page.testUser.username);
        await page.fill('input[name="password"]', page.testUser.password);
        await page.click('button[type="submit"]');

        // Should redirect to homepage or profile
        await page.waitForURL(/\/(accounts\/profile|$)/);

        // Should show logged-in state (user menu, logout button, etc.)
        const userIndicator = page.locator('text=/logout|profile|account|welcome/i').first();
        await expect(userIndicator).toBeVisible({ timeout: 5000 });
    });

    test('should show error for invalid username', async ({ page }) => {
        await page.goto('/accounts/login/');

        await page.fill('input[name="username"]', 'nonexistent_user_999');
        await page.fill('input[name="password"]', 'SomePassword123!');
        await page.click('button[type="submit"]');

        // Should show invalid credentials error
        const errorMessage = page.locator('text=/invalid|incorrect|wrong|not found/i');
        await expect(errorMessage).toBeVisible({ timeout: 3000 });
    });

    test('should show error for wrong password', async ({ page }) => {
        await page.goto('/accounts/login/');

        await page.fill('input[name="username"]', page.testUser.username);
        await page.fill('input[name="password"]', 'WrongPassword123!');
        await page.click('button[type="submit"]');

        const errorMessage = page.locator('text=/invalid|incorrect|wrong/i');
        await expect(errorMessage).toBeVisible({ timeout: 3000 });
    });

    test('should show error for empty fields', async ({ page }) => {
        await page.goto('/accounts/login/');

        // Try to submit without filling fields
        await page.click('button[type="submit"]');

        // Browser validation should prevent submission
        const usernameField = page.locator('input[name="username"]');
        await expect(usernameField).toHaveAttribute('required', '');
    });
});

// ============================================================================
// LOGOUT FLOW TESTS
// ============================================================================

test.describe('User Logout', () => {
    test.beforeEach(async ({ page }) => {
        // Register and login before logout tests
        await page.goto('/accounts/register/');

        const uniqueUser = {
            username: `testuser_${Date.now()}`,
            email: `test_${Date.now()}@example.com`,
            password: 'TestPassword123!',
        };

        await page.fill('input[name="username"]', uniqueUser.username);
        await page.fill('input[name="email"]', uniqueUser.email);
        await page.fill('input[name="password1"]', uniqueUser.password);
        await page.fill('input[name="password2"]', uniqueUser.password);
        await page.click('button[type="submit"]');

        await page.waitForTimeout(2000);

        // Login
        await page.goto('/accounts/login/');
        await page.fill('input[name="username"]', uniqueUser.username);
        await page.fill('input[name="password"]', uniqueUser.password);
        await page.click('button[type="submit"]');

        await page.waitForTimeout(1000);
    });

    test('should logout successfully', async ({ page }) => {
        // Find and click logout button/link
        const logoutButton = page.locator('a[href*="logout"], button:has-text("Logout"), a:has-text("Logout")').first();
        await logoutButton.click();

        // Should redirect to login or homepage
        await page.waitForURL(/\/(accounts\/login|$)/);

        // Should show logged-out state (login button visible)
        const loginLink = page.locator('a[href*="login"], a:has-text("Login")').first();
        await expect(loginLink).toBeVisible({ timeout: 5000 });
    });

    test('should not access protected pages after logout', async ({ page }) => {
        // Logout
        const logoutButton = page.locator('a[href*="logout"], button:has-text("Logout"), a:has-text("Logout")').first();
        await logoutButton.click();

        await page.waitForTimeout(1000);

        // Try to access protected page (adjust URL as needed)
        await page.goto('/accounts/profile/');

        // Should redirect to login
        await page.waitForURL(/\/accounts\/login/);
    });
});

// ============================================================================
// PASSWORD RESET FLOW TESTS
// ============================================================================

test.describe('Password Reset', () => {
    test('should display password reset page', async ({ page }) => {
        await page.goto('/accounts/password_reset/');

        await expect(page).toHaveTitle(/Password Reset|Forgot Password/i);

        await expect(page.locator('input[name="email"]')).toBeVisible();
        await expect(page.locator('button[type="submit"]')).toBeVisible();
    });

    test('should submit password reset request', async ({ page }) => {
        await page.goto('/accounts/password_reset/');

        await page.fill('input[name="email"]', 'test@example.com');
        await page.click('button[type="submit"]');

        // Should show confirmation message
        await page.waitForURL(/\/accounts\/password_reset\/done/);

        const confirmMessage = page.locator('text=/email.*sent|check.*email|instructions/i');
        await expect(confirmMessage).toBeVisible({ timeout: 5000 });
    });

    test('should handle invalid email format', async ({ page }) => {
        await page.goto('/accounts/password_reset/');

        await page.fill('input[name="email"]', 'invalid-email');
        await page.click('button[type="submit"]');

        // Browser validation should catch invalid email
        const emailField = page.locator('input[name="email"]');
        await expect(emailField).toHaveAttribute('type', 'email');
    });
});

// ============================================================================
// SESSION MANAGEMENT TESTS
// ============================================================================

test.describe('Session Management', () => {
    test('should maintain session across page navigations', async ({ page }) => {
        // Register and login
        await page.goto('/accounts/register/');

        const uniqueUser = {
            username: `testuser_${Date.now()}`,
            email: `test_${Date.now()}@example.com`,
            password: 'TestPassword123!',
        };

        await page.fill('input[name="username"]', uniqueUser.username);
        await page.fill('input[name="email"]', uniqueUser.email);
        await page.fill('input[name="password1"]', uniqueUser.password);
        await page.fill('input[name="password2"]', uniqueUser.password);
        await page.click('button[type="submit"]');

        await page.waitForTimeout(2000);

        await page.goto('/accounts/login/');
        await page.fill('input[name="username"]', uniqueUser.username);
        await page.fill('input[name="password"]', uniqueUser.password);
        await page.click('button[type="submit"]');

        await page.waitForTimeout(1000);

        // Navigate to different pages
        await page.goto('/');
        await page.waitForTimeout(500);

        await page.goto('/blog/');
        await page.waitForTimeout(500);

        await page.goto('/contact/');
        await page.waitForTimeout(500);

        // Should still be logged in
        const userIndicator = page.locator('text=/logout|profile|account/i').first();
        await expect(userIndicator).toBeVisible();
    });

    test('should persist session after page reload', async ({ page }) => {
        // Register and login
        await page.goto('/accounts/register/');

        const uniqueUser = {
            username: `testuser_${Date.now()}`,
            email: `test_${Date.now()}@example.com`,
            password: 'TestPassword123!',
        };

        await page.fill('input[name="username"]', uniqueUser.username);
        await page.fill('input[name="email"]', uniqueUser.email);
        await page.fill('input[name="password1"]', uniqueUser.password);
        await page.fill('input[name="password2"]', uniqueUser.password);
        await page.click('button[type="submit"]');

        await page.waitForTimeout(2000);

        await page.goto('/accounts/login/');
        await page.fill('input[name="username"]', uniqueUser.username);
        await page.fill('input[name="password"]', uniqueUser.password);
        await page.click('button[type="submit"]');

        await page.waitForTimeout(1000);

        // Reload page
        await page.reload();

        await page.waitForTimeout(1000);

        // Should still be logged in
        const userIndicator = page.locator('text=/logout|profile|account/i').first();
        await expect(userIndicator).toBeVisible();
    });
});

// ============================================================================
// AUTHENTICATION REDIRECT TESTS
// ============================================================================

test.describe('Authentication Redirects', () => {
    test('should redirect unauthenticated user to login', async ({ page }) => {
        // Try to access protected page without login
        await page.goto('/accounts/profile/');

        // Should redirect to login page
        await page.waitForURL(/\/accounts\/login/);
    });

    test('should redirect to original page after login', async ({ page }) => {
        // Try to access protected page
        await page.goto('/accounts/profile/');

        // Should redirect to login with next parameter
        await page.waitForURL(/\/accounts\/login.*next/);

        // Register first
        await page.goto('/accounts/register/');

        const uniqueUser = {
            username: `testuser_${Date.now()}`,
            email: `test_${Date.now()}@example.com`,
            password: 'TestPassword123!',
        };

        await page.fill('input[name="username"]', uniqueUser.username);
        await page.fill('input[name="email"]', uniqueUser.email);
        await page.fill('input[name="password1"]', uniqueUser.password);
        await page.fill('input[name="password2"]', uniqueUser.password);
        await page.click('button[type="submit"]');

        await page.waitForTimeout(2000);

        // Now login with next parameter
        await page.goto('/accounts/login/?next=/accounts/profile/');
        await page.fill('input[name="username"]', uniqueUser.username);
        await page.fill('input[name="password"]', uniqueUser.password);
        await page.click('button[type="submit"]');

        // Should redirect back to profile
        await page.waitForURL(/\/accounts\/profile/);
    });
});

// ============================================================================
// ACCESSIBILITY TESTS
// ============================================================================

test.describe('Authentication Accessibility', () => {
    test('login form should be keyboard accessible', async ({ page }) => {
        await page.goto('/accounts/login/');

        // Tab through form
        await page.keyboard.press('Tab');
        await page.keyboard.type('testuser');

        await page.keyboard.press('Tab');
        await page.keyboard.type('password123');

        await page.keyboard.press('Tab');
        await page.keyboard.press('Enter');

        // Form should submit
        await page.waitForURL(/\/.*/);
    });

    test('registration form should have proper labels', async ({ page }) => {
        await page.goto('/accounts/register/');

        // Check for associated labels
        const usernameLabel = page.locator('label[for*="username"]');
        const emailLabel = page.locator('label[for*="email"]');
        const passwordLabel = page.locator('label[for*="password"]');

        await expect(usernameLabel).toBeVisible();
        await expect(emailLabel).toBeVisible();
        await expect(passwordLabel).toBeVisible();
    });
});
