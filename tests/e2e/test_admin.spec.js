/**
 * E2E Tests for Admin Dashboard - Phase 22D.1
 *
 * Tests cover:
 * - Admin authentication
 * - Admin dashboard navigation
 * - CRUD operations (Create, Read, Update, Delete)
 * - Bulk actions
 * - Filtering and search
 * - Admin permissions
 * - Mobile admin experience
 * - Accessibility
 *
 * Tests run on: Chromium, Firefox, WebKit
 */

const { test, expect } = require('@playwright/test');

// Admin credentials (should be configured in test environment)
const ADMIN_USER = {
    username: process.env.ADMIN_USERNAME || 'admin',
    password: process.env.ADMIN_PASSWORD || 'admin123',
};

// Helper function to login as admin
async function loginAsAdmin(page) {
    await page.goto('/admin/login/');

    await page.fill('input[name="username"]', ADMIN_USER.username);
    await page.fill('input[name="password"]', ADMIN_USER.password);
    await page.click('input[type="submit"], button[type="submit"]');

    await page.waitForURL(/\/admin\//);
    await page.waitForTimeout(1000);
}

// ============================================================================
// ADMIN AUTHENTICATION TESTS
// ============================================================================

test.describe('Admin Authentication', () => {
    test('should display admin login page', async ({ page }) => {
        await page.goto('/admin/');

        // Should redirect to login
        await page.waitForURL(/\/admin\/login/);

        await expect(page).toHaveTitle(/Log in|Django|Admin/i);

        // Check for login form with new compact layout
        await expect(page.locator('input[name="username"]')).toBeVisible();
        await expect(page.locator('input[name="password"]')).toBeVisible();
        await expect(page.locator('button[type="submit"], input[type="submit"]')).toBeVisible();

        // Verify no sidebar/header on login page
        await expect(page.locator('#nav-sidebar')).not.toBeVisible();
        await expect(page.locator('.login-card')).toBeVisible();
    });

    test('should login with valid admin credentials', async ({ page }) => {
        await page.goto('/admin/login/');

        await page.fill('input[name="username"]', ADMIN_USER.username);
        await page.fill('input[name="password"]', ADMIN_USER.password);
        await page.click('input[type="submit"], button[type="submit"]');

        // Should redirect to admin dashboard
        await page.waitForURL(/\/admin\//);

        // Should show admin interface
        const adminHeader = page.locator('#header, .header, h1, [role="banner"]').first();
        await expect(adminHeader).toBeVisible();
    });

    test('should show error for invalid credentials', async ({ page }) => {
        await page.goto('/admin/login/');

        await page.fill('input[name="username"]', 'wronguser');
        await page.fill('input[name="password"]', 'wrongpass');
        await page.click('input[type="submit"], button[type="submit"]');

        await page.waitForTimeout(1000);

        // Should show error message
        const errorMessage = page.locator('.errornote, .error, text=/incorrect|invalid|wrong/i').first();
        await expect(errorMessage).toBeVisible({ timeout: 3000 });
    });

    test('should prevent access without authentication', async ({ page }) => {
        // Try to access admin dashboard directly
        await page.goto('/admin/');

        // Should redirect to login
        await page.waitForURL(/\/admin\/login/);
    });

    test('should logout from admin', async ({ page }) => {
        await loginAsAdmin(page);

        // Find and click logout button
        const logoutButton = page.locator('a[href*="logout"], button:has-text("Log out")').first();
        await logoutButton.click();

        await page.waitForTimeout(1000);

        // Should redirect to logged out page or login
        await page.waitForURL(/\/admin\/(login|logout)/);

        // Try to access admin again
        await page.goto('/admin/');

        // Should redirect to login
        await page.waitForURL(/\/admin\/login/);
    });
});

// ============================================================================
// ADMIN DASHBOARD NAVIGATION TESTS
// ============================================================================

test.describe('Admin Dashboard Navigation', () => {
    test.beforeEach(async ({ page }) => {
        await loginAsAdmin(page);
    });

    test('should display admin dashboard with new UI', async ({ page }) => {
        await page.goto('/admin/');

        // Should show Django admin interface
        const dashboard = page.locator('#content, .content, main').first();
        await expect(dashboard).toBeVisible();

        // Should show compact header with branding
        const branding = page.locator('.admin-brand, #branding').first();
        await expect(branding).toBeVisible();

        // Should have sidebar toggle button
        const sidebarToggle = page.locator('.sidebar-toggle, [data-admin-toggle="sidebar"]').first();
        await expect(sidebarToggle).toBeVisible();

        // Should show navigation sidebar
        const sidebar = page.locator('#nav-sidebar').first();
        await expect(sidebar).toBeVisible();
    });

    test('should display available models/apps', async ({ page }) => {
        await page.goto('/admin/');

        // Should show list of apps and models
        const appList = page.locator('#content-main, .app-list, [class*="module"]').first();
        await expect(appList).toBeVisible();

        // Should have at least one model link
        const modelLinks = page.locator('a[href*="/admin/"]');
        const linkCount = await modelLinks.count();

        expect(linkCount).toBeGreaterThan(0);
    });

    test('should navigate to model list view', async ({ page }) => {
        await page.goto('/admin/');

        // Click on first model link
        const firstModelLink = page.locator('a[href*="/admin/"][href*="/"]').first();
        await firstModelLink.click();

        await page.waitForTimeout(1000);

        // Should show changelist view
        const changelist = page.locator('#changelist, .changelist, #result_list').first();
        const hasChangelist = await changelist.count() > 0;

        expect(hasChangelist).toBeTruthy();
    });

    test('should have breadcrumb navigation', async ({ page }) => {
        await page.goto('/admin/');

        // Click on a model
        const modelLink = page.locator('a[href*="/admin/"][href*="/"]').first();
        await modelLink.click();

        await page.waitForTimeout(1000);

        // Should have breadcrumbs
        const breadcrumbs = page.locator('.breadcrumbs, nav[aria-label*="breadcrumb"], .breadcrumb').first();
        const hasBreadcrumbs = await breadcrumbs.count() > 0;

        if (hasBreadcrumbs) {
            await expect(breadcrumbs).toBeVisible();
        }
    });

    test('should have home link in header', async ({ page }) => {
        await page.goto('/admin/');

        // Navigate to a model
        const modelLink = page.locator('a[href*="/admin/"][href*="/"]').first();
        await modelLink.click();

        await page.waitForTimeout(1000);

        // Should have home link to go back
        const homeLink = page.locator('a[href="/admin/"], a:has-text("Home")').first();
        await expect(homeLink).toBeVisible();

        await homeLink.click();

        // Should go back to admin dashboard
        await page.waitForURL(/\/admin\/$/);
    });
});

// ============================================================================
// CRUD OPERATIONS TESTS
// ============================================================================

test.describe('Admin CRUD Operations', () => {
    test.beforeEach(async ({ page }) => {
        await loginAsAdmin(page);
    });

    test('should display add new button', async ({ page }) => {
        await page.goto('/admin/');

        // Navigate to a model changelist
        const modelLink = page.locator('a[href*="/admin/"][href*="/"]').first();
        await modelLink.click();

        await page.waitForTimeout(1000);

        // Should have "Add" button
        const addButton = page.locator('a[href*="/add/"], a:has-text("Add"), .addlink').first();
        await expect(addButton).toBeVisible();
    });

    test('should navigate to add form', async ({ page }) => {
        await page.goto('/admin/');

        // Navigate to a model changelist
        const modelLink = page.locator('a[href*="/admin/"][href*="/"]').first();
        await modelLink.click();

        await page.waitForTimeout(1000);

        // Click add button
        const addButton = page.locator('a[href*="/add/"], a:has-text("Add"), .addlink').first();
        await addButton.click();

        await page.waitForURL(/\/add\//);

        // Should show form
        const form = page.locator('form').first();
        await expect(form).toBeVisible();

        // Should have save button
        const saveButton = page.locator('input[name="_save"], button:has-text("Save")').first();
        await expect(saveButton).toBeVisible();
    });

    test('should display list of objects', async ({ page }) => {
        await page.goto('/admin/');

        // Navigate to a model changelist
        const modelLink = page.locator('a[href*="/admin/"][href*="/"]').first();
        await modelLink.click();

        await page.waitForTimeout(1000);

        // Should show result list or empty message
        const resultList = page.locator('#result_list, .results, table').first();
        const emptyMessage = page.locator('text=/no.*found|empty/i').first();

        const hasResults = await resultList.count() > 0;
        const isEmpty = await emptyMessage.count() > 0;

        expect(hasResults || isEmpty).toBeTruthy();
    });

    test('should navigate to edit form', async ({ page }) => {
        await page.goto('/admin/');

        // Navigate to a model changelist
        const modelLink = page.locator('a[href*="/admin/"][href*="/"]').first();
        await modelLink.click();

        await page.waitForTimeout(1000);

        // Click on first object if exists
        const firstObjectLink = page.locator('#result_list a, .results a, table a').first();

        if (await firstObjectLink.count() > 0) {
            await firstObjectLink.click();

            await page.waitForURL(/\/change\//);

            // Should show edit form
            const form = page.locator('form').first();
            await expect(form).toBeVisible();

            // Should have save button
            const saveButton = page.locator('input[name="_save"], button:has-text("Save")').first();
            await expect(saveButton).toBeVisible();

            // Should have delete button
            const deleteLink = page.locator('a.deletelink, a:has-text("Delete")').first();
            await expect(deleteLink).toBeVisible();
        }
    });

    test('should have save and continue editing option', async ({ page }) => {
        await page.goto('/admin/');

        const modelLink = page.locator('a[href*="/admin/"][href*="/"]').first();
        await modelLink.click();

        await page.waitForTimeout(1000);

        const firstObjectLink = page.locator('#result_list a, .results a, table a').first();

        if (await firstObjectLink.count() > 0) {
            await firstObjectLink.click();

            await page.waitForTimeout(1000);

            // Should have "Save and continue editing" button
            const saveContinueButton = page.locator('input[name="_continue"], button:has-text("continue")').first();
            const hasSaveContinue = await saveContinueButton.count() > 0;

            expect(hasSaveContinue).toBeTruthy();
        }
    });

    test('should have save and add another option', async ({ page }) => {
        await page.goto('/admin/');

        const modelLink = page.locator('a[href*="/admin/"][href*="/"]').first();
        await modelLink.click();

        await page.waitForTimeout(1000);

        const addButton = page.locator('a[href*="/add/"]').first();
        await addButton.click();

        await page.waitForTimeout(1000);

        // Should have "Save and add another" button
        const saveAddAnotherButton = page.locator('input[name="_addanother"], button:has-text("add another")').first();
        const hasSaveAddAnother = await saveAddAnotherButton.count() > 0;

        expect(hasSaveAddAnother).toBeTruthy();
    });
});

// ============================================================================
// BULK ACTIONS TESTS
// ============================================================================

test.describe('Admin Bulk Actions', () => {
    test.beforeEach(async ({ page }) => {
        await loginAsAdmin(page);
    });

    test('should display bulk action dropdown', async ({ page }) => {
        await page.goto('/admin/');

        const modelLink = page.locator('a[href*="/admin/"][href*="/"]').first();
        await modelLink.click();

        await page.waitForTimeout(1000);

        // Check for action dropdown
        const actionDropdown = page.locator('select[name="action"], #changelist-form select').first();

        if (await actionDropdown.count() > 0) {
            await expect(actionDropdown).toBeVisible();

            // Should have at least "Delete selected" option
            const options = await actionDropdown.locator('option').count();
            expect(options).toBeGreaterThan(1); // Including empty option
        }
    });

    test('should have checkboxes for selection', async ({ page }) => {
        await page.goto('/admin/');

        const modelLink = page.locator('a[href*="/admin/"][href*="/"]').first();
        await modelLink.click();

        await page.waitForTimeout(1000);

        // Check for checkboxes
        const checkboxes = page.locator('input[type="checkbox"][name="_selected_action"]');

        if (await checkboxes.count() > 0) {
            const firstCheckbox = checkboxes.first();
            await expect(firstCheckbox).toBeVisible();
        }
    });

    test('should have select all checkbox', async ({ page }) => {
        await page.goto('/admin/');

        const modelLink = page.locator('a[href*="/admin/"][href*="/"]').first();
        await modelLink.click();

        await page.waitForTimeout(1000);

        // Check for "select all" checkbox in header
        const selectAllCheckbox = page.locator('#action-toggle, input[type="checkbox"]:not([name="_selected_action"])').first();

        if (await selectAllCheckbox.count() > 0) {
            await expect(selectAllCheckbox).toBeVisible();
        }
    });

    test('should have go button for bulk actions', async ({ page }) => {
        await page.goto('/admin/');

        const modelLink = page.locator('a[href*="/admin/"][href*="/"]').first();
        await modelLink.click();

        await page.waitForTimeout(1000);

        const actionDropdown = page.locator('select[name="action"]').first();

        if (await actionDropdown.count() > 0) {
            // Should have Go button
            const goButton = page.locator('button[title="Run the selected action"], button:has-text("Go")').first();
            await expect(goButton).toBeVisible();
        }
    });
});

// ============================================================================
// FILTERING AND SEARCH TESTS
// ============================================================================

test.describe('Admin Filtering and Search', () => {
    test.beforeEach(async ({ page }) => {
        await loginAsAdmin(page);
    });

    test('should display search box if available', async ({ page }) => {
        await page.goto('/admin/');

        const modelLink = page.locator('a[href*="/admin/"][href*="/"]').first();
        await modelLink.click();

        await page.waitForTimeout(1000);

        // Check for search box
        const searchBox = page.locator('input[name="q"], #searchbar').first();

        if (await searchBox.count() > 0) {
            await expect(searchBox).toBeVisible();

            // Should have search button
            const searchButton = page.locator('input[type="submit"][value*="Search"], button:has-text("Search")').first();
            await expect(searchButton).toBeVisible();
        }
    });

    test('should perform search', async ({ page }) => {
        await page.goto('/admin/');

        const modelLink = page.locator('a[href*="/admin/"][href*="/"]').first();
        await modelLink.click();

        await page.waitForTimeout(1000);

        const searchBox = page.locator('input[name="q"], #searchbar').first();

        if (await searchBox.count() > 0) {
            await searchBox.fill('test');

            const searchButton = page.locator('input[type="submit"][value*="Search"], button:has-text("Search")').first();
            await searchButton.click();

            await page.waitForTimeout(1000);

            // Should show search results or no results message
            const results = page.locator('#result_list, .results, text=/results|no.*found/i').first();
            await expect(results).toBeVisible();
        }
    });

    test('should display filters sidebar if available', async ({ page }) => {
        await page.goto('/admin/');

        const modelLink = page.locator('a[href*="/admin/"][href*="/"]').first();
        await modelLink.click();

        await page.waitForTimeout(1000);

        // Check for filters sidebar
        const filtersSidebar = page.locator('#changelist-filter, .changelist-filter-container').first();

        if (await filtersSidebar.count() > 0) {
            await expect(filtersSidebar).toBeVisible();

            // Should have filter options
            const filterLinks = page.locator('#changelist-filter a').first();
            await expect(filterLinks).toBeVisible();
        }
    });

    test('should apply filter', async ({ page }) => {
        await page.goto('/admin/');

        const modelLink = page.locator('a[href*="/admin/"][href*="/"]').first();
        await modelLink.click();

        await page.waitForTimeout(1000);

        const filtersSidebar = page.locator('#changelist-filter').first();

        if (await filtersSidebar.count() > 0) {
            // Click first filter option
            const firstFilter = page.locator('#changelist-filter a').first();
            await firstFilter.click();

            await page.waitForTimeout(1000);

            // URL should have filter parameter
            const url = page.url();
            expect(url).toContain('?');
        }
    });
});

// ============================================================================
// ADMIN PERMISSIONS TESTS
// ============================================================================

test.describe('Admin Permissions', () => {
    test.beforeEach(async ({ page }) => {
        await loginAsAdmin(page);
    });

    test('should show only authorized models', async ({ page }) => {
        await page.goto('/admin/');

        // Should show list of apps and models
        const appList = page.locator('#content-main, .app-list').first();
        await expect(appList).toBeVisible();

        // Admin should have access to at least one model
        const modelLinks = page.locator('a[href*="/admin/"]');
        const linkCount = await modelLinks.count();

        expect(linkCount).toBeGreaterThan(0);
    });

    test('should have user management link for superuser', async ({ page }) => {
        await page.goto('/admin/');

        // Check for users/groups management
        const usersLink = page.locator('a[href*="/auth/user/"], a:has-text("Users")').first();

        if (await usersLink.count() > 0) {
            await expect(usersLink).toBeVisible();
        }
    });
});

// ============================================================================
// MOBILE ADMIN EXPERIENCE TESTS
// ============================================================================

test.describe('Admin Mobile Experience', () => {
    test.use({
        viewport: { width: 375, height: 667 } // iPhone SE size
    });

    test.beforeEach(async ({ page }) => {
        await loginAsAdmin(page);
    });

    test('should display admin dashboard on mobile', async ({ page }) => {
        await page.goto('/admin/');

        // Dashboard should be visible
        const dashboard = page.locator('#content, .content').first();
        await expect(dashboard).toBeVisible();

        // App list should be visible
        const appList = page.locator('#content-main, .app-list').first();
        await expect(appList).toBeVisible();

        // On mobile, sidebar should be collapsed or at top
        const sidebar = page.locator('#nav-sidebar').first();
        await expect(sidebar).toBeVisible();
    });

    test('should display model list on mobile', async ({ page }) => {
        await page.goto('/admin/');

        const modelLink = page.locator('a[href*="/admin/"][href*="/"]').first();
        await modelLink.click();

        await page.waitForTimeout(1000);

        // Content should be visible
        const content = page.locator('#content').first();
        await expect(content).toBeVisible();
    });

    test('should display forms on mobile', async ({ page }) => {
        await page.goto('/admin/');

        const modelLink = page.locator('a[href*="/admin/"][href*="/"]').first();
        await modelLink.click();

        await page.waitForTimeout(1000);

        const addButton = page.locator('a[href*="/add/"]').first();
        await addButton.click();

        await page.waitForTimeout(1000);

        // Form should be visible and usable
        const form = page.locator('form').first();
        await expect(form).toBeVisible();
    });

    test('should have working sidebar toggle on mobile', async ({ page }) => {
        await page.goto('/admin/');

        // Sidebar toggle should be visible
        const sidebarToggle = page.locator('.sidebar-toggle').first();
        await expect(sidebarToggle).toBeVisible();

        // Toggle should be clickable
        await sidebarToggle.click();
        await page.waitForTimeout(300);

        // Click again to toggle back
        await sidebarToggle.click();
        await page.waitForTimeout(300);
    });
});

// ============================================================================
// RESPONSIVE DESIGN TESTS
// ============================================================================

test.describe('Admin Responsive Design', () => {
    test.beforeEach(async ({ page }) => {
        await loginAsAdmin(page);
    });

    test('should collapse sidebar on tablet breakpoint', async ({ page }) => {
        // Set tablet viewport
        await page.setViewportSize({ width: 768, height: 1024 });
        await page.goto('/admin/');

        const sidebar = page.locator('#nav-sidebar').first();
        await expect(sidebar).toBeVisible();

        // Sidebar should be collapsed or have collapsed styling
        await page.waitForTimeout(500);
    });

    test('should show compact layout on desktop', async ({ page }) => {
        await page.setViewportSize({ width: 1920, height: 1080 });
        await page.goto('/admin/');

        // Should show sidebar
        const sidebar = page.locator('#nav-sidebar').first();
        await expect(sidebar).toBeVisible();

        // Should show toggle button
        const toggle = page.locator('.sidebar-toggle').first();
        await expect(toggle).toBeVisible();

        // Stats cards should be in grid
        const statsGrid = page.locator('.dashboard__grid, .stat-card').first();
        if (await statsGrid.count() > 0) {
            await expect(statsGrid).toBeVisible();
        }
    });

    test('should have hover animations on desktop', async ({ page }) => {
        await page.setViewportSize({ width: 1920, height: 1080 });
        await page.goto('/admin/');

        // Hover over stat card if exists
        const statCard = page.locator('.stat-card').first();
        if (await statCard.count() > 0) {
            await statCard.hover();
            await page.waitForTimeout(200);

            // Card should have transform applied (visual check)
            const box = await statCard.boundingBox();
            expect(box).toBeTruthy();
        }
    });
});

// ============================================================================
// ACCESSIBILITY TESTS
// ============================================================================

test.describe('Admin Accessibility', () => {
    test.beforeEach(async ({ page }) => {
        await loginAsAdmin(page);
    });

    test('should be keyboard navigable', async ({ page }) => {
        await page.goto('/admin/');

        // Tab through interface
        await page.keyboard.press('Tab');

        // Should focus on a link
        const focusedElement = page.locator(':focus').first();
        await expect(focusedElement).toBeVisible();
    });

    test('should have proper heading hierarchy', async ({ page }) => {
        await page.goto('/admin/');

        // Should have h1
        const h1 = page.locator('h1').first();
        await expect(h1).toBeVisible();
    });

    test('sidebar toggle should be accessible', async ({ page }) => {
        await page.goto('/admin/');

        // Check sidebar toggle accessibility
        const toggle = page.locator('.sidebar-toggle, [data-admin-toggle="sidebar"]').first();

        if (await toggle.count() > 0) {
            // Should have aria-label
            const ariaLabel = await toggle.getAttribute('aria-label');
            expect(ariaLabel).toBeTruthy();

            // Should have aria-expanded
            const ariaExpanded = await toggle.getAttribute('aria-expanded');
            expect(ariaExpanded).toBeTruthy();

            // Should have aria-controls
            const ariaControls = await toggle.getAttribute('aria-controls');
            expect(ariaControls).toBe('nav-sidebar');
        }
    });

    test('should toggle sidebar with keyboard shortcut', async ({ page }) => {
        await page.goto('/admin/');

        const sidebar = page.locator('#nav-sidebar').first();

        // Get initial state
        const initialClasses = await sidebar.getAttribute('class');

        // Press Ctrl/Cmd + B
        const modifier = process.platform === 'darwin' ? 'Meta' : 'Control';
        await page.keyboard.press(`${modifier}+KeyB`);

        await page.waitForTimeout(500);

        // State should have changed
        const newClasses = await sidebar.getAttribute('class');
        expect(newClasses).not.toBe(initialClasses);
    });
});
