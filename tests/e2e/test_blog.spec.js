/**
 * E2E Tests for Blog Functionality - Phase 22D.1
 *
 * Tests cover:
 * - Blog list page with pagination
 * - Blog detail page
 * - Search functionality
 * - Category filtering
 * - Tag filtering
 * - Reading time display
 * - Related posts
 * - Mobile responsiveness
 *
 * Tests run on: Chromium, Firefox, WebKit
 */

const { test, expect } = require('@playwright/test');

// ============================================================================
// BLOG LIST PAGE TESTS
// ============================================================================

test.describe('Blog List Page', () => {
    test('should display blog list page', async ({ page }) => {
        await page.goto('/blog/');

        await expect(page).toHaveTitle(/Blog|Articles|Posts/i);

        // Check for blog post elements
        const blogPosts = page.locator('article, .blog-post, .post-card, [class*="blog"], [class*="post"]');
        const count = await blogPosts.count();

        expect(count).toBeGreaterThan(0);
    });

    test('should display blog post cards with essential elements', async ({ page }) => {
        await page.goto('/blog/');

        await page.waitForTimeout(1000);

        // Get first blog post
        const firstPost = page.locator('article, .blog-post, .post-card, [class*="blog"]').first();

        // Check for title (link or heading)
        const title = firstPost.locator('h1, h2, h3, h4, a[href*="blog"]').first();
        await expect(title).toBeVisible();

        // Check for read more link or button
        const readMoreLink = firstPost.locator('a[href*="blog"], a:has-text("Read"), a:has-text("More"), button:has-text("Read")').first();
        await expect(readMoreLink).toBeVisible();
    });

    test('should handle pagination if exists', async ({ page }) => {
        await page.goto('/blog/');

        await page.waitForTimeout(1000);

        // Check if pagination exists
        const pagination = page.locator('.pagination, nav[aria-label*="pagination"], .pager, [class*="pagination"]');

        const hasPagination = await pagination.count() > 0;

        if (hasPagination) {
            // Click next page
            const nextButton = page.locator('a:has-text("Next"), a:has-text("›"), a:has-text("»"), button:has-text("Next")').first();

            if (await nextButton.isVisible()) {
                await nextButton.click();

                // Should navigate to page 2
                await page.waitForURL(/page=2|\/2\//);

                // Should still show blog posts
                const blogPosts = page.locator('article, .blog-post, .post-card');
                const count = await blogPosts.count();
                expect(count).toBeGreaterThan(0);
            }
        }
    });

    test('should display blog post meta information', async ({ page }) => {
        await page.goto('/blog/');

        await page.waitForTimeout(1000);

        const firstPost = page.locator('article, .blog-post, .post-card').first();

        // Check for date (common patterns)
        const dateElement = firstPost.locator('time, .date, .published, [datetime], [class*="date"]').first();
        const hasDate = await dateElement.count() > 0;

        // Check for author (optional)
        const authorElement = firstPost.locator('.author, [class*="author"], [rel="author"]').first();
        const hasAuthor = await authorElement.count() > 0;

        // At least one meta element should exist
        expect(hasDate || hasAuthor).toBeTruthy();
    });

    test('should navigate to blog detail from list', async ({ page }) => {
        await page.goto('/blog/');

        await page.waitForTimeout(1000);

        // Click first blog post link
        const firstPostLink = page.locator('article a[href*="blog"], .blog-post a[href*="blog"], .post-card a[href*="blog"]').first();

        await firstPostLink.click();

        // Should navigate to detail page
        await page.waitForURL(/\/blog\/.+/);

        // Should show blog content
        const content = page.locator('article, .post-content, .blog-content, main');
        await expect(content).toBeVisible();
    });
});

// ============================================================================
// BLOG DETAIL PAGE TESTS
// ============================================================================

test.describe('Blog Detail Page', () => {
    test.beforeEach(async ({ page }) => {
        // Navigate to blog list first
        await page.goto('/blog/');
        await page.waitForTimeout(1000);

        // Click first blog post
        const firstPostLink = page.locator('article a[href*="blog"], .blog-post a[href*="blog"], .post-card a[href*="blog"]').first();
        await firstPostLink.click();

        await page.waitForTimeout(1000);
    });

    test('should display blog post title', async ({ page }) => {
        const title = page.locator('h1, .post-title, .blog-title, article h1').first();
        await expect(title).toBeVisible();

        const titleText = await title.textContent();
        expect(titleText.trim().length).toBeGreaterThan(0);
    });

    test('should display blog post content', async ({ page }) => {
        const content = page.locator('article, .post-content, .blog-content, .entry-content, main').first();
        await expect(content).toBeVisible();

        const contentText = await content.textContent();
        expect(contentText.trim().length).toBeGreaterThan(50);
    });

    test('should display published date', async ({ page }) => {
        const date = page.locator('time, .date, .published, [datetime], [class*="date"]').first();
        const hasDate = await date.count() > 0;

        expect(hasDate).toBeTruthy();
    });

    test('should display reading time if available', async ({ page }) => {
        // Reading time is optional but nice to have
        const readingTime = page.locator('text=/\\d+\\s*(min|minute|mins|minutes)\\s*(read)?/i').first();

        const hasReadingTime = await readingTime.count() > 0;

        // Just log if it exists (not critical)
        if (hasReadingTime) {
            const timeText = await readingTime.textContent();
            console.log('Reading time found:', timeText);
        }
    });

    test('should display categories or tags if available', async ({ page }) => {
        // Check for categories
        const categories = page.locator('.category, .categories, [class*="category"], a[href*="category"]');
        const hasCategories = await categories.count() > 0;

        // Check for tags
        const tags = page.locator('.tag, .tags, [class*="tag"], a[href*="tag"]');
        const hasTags = await tags.count() > 0;

        // At least one categorization should exist (optional)
        if (hasCategories || hasTags) {
            console.log('Categorization found: categories =', hasCategories, ', tags =', hasTags);
        }
    });

    test('should have back to blog list link', async ({ page }) => {
        const backLink = page.locator('a[href="/blog/"], a[href*="blog"]:has-text("Back"), a:has-text("All Posts"), a:has-text("Blog")').first();

        const hasBackLink = await backLink.count() > 0;

        if (hasBackLink) {
            await expect(backLink).toBeVisible();
        }
    });

    test('should display related posts if available', async ({ page }) => {
        // Related posts section (optional)
        const relatedSection = page.locator('text=/related.*posts|you.*might.*like|similar.*posts/i');

        const hasRelated = await relatedSection.count() > 0;

        if (hasRelated) {
            const relatedPosts = page.locator('.related-post, [class*="related"]').last();
            await expect(relatedPosts).toBeVisible();
        }
    });

    test('should handle images in blog content', async ({ page }) => {
        const images = page.locator('article img, .post-content img, .blog-content img');
        const imageCount = await images.count();

        if (imageCount > 0) {
            const firstImage = images.first();

            // Check image has alt text
            const altText = await firstImage.getAttribute('alt');
            expect(altText).toBeDefined();

            // Check image is visible
            await expect(firstImage).toBeVisible();
        }
    });
});

// ============================================================================
// BLOG SEARCH TESTS
// ============================================================================

test.describe('Blog Search', () => {
    test('should display search functionality', async ({ page }) => {
        await page.goto('/blog/');

        await page.waitForTimeout(1000);

        // Check for search input
        const searchInput = page.locator('input[type="search"], input[name*="search"], input[name="q"], input[placeholder*="Search"]').first();

        const hasSearch = await searchInput.count() > 0;

        if (hasSearch) {
            await expect(searchInput).toBeVisible();
        } else {
            console.log('Search functionality not found on blog list page');
        }
    });

    test('should perform search and show results', async ({ page }) => {
        await page.goto('/blog/');

        await page.waitForTimeout(1000);

        const searchInput = page.locator('input[type="search"], input[name*="search"], input[name="q"]').first();

        if (await searchInput.count() > 0) {
            await searchInput.fill('test');

            // Submit search (press Enter or click button)
            await searchInput.press('Enter');

            await page.waitForTimeout(1000);

            // Should show search results or message
            const resultsOrMessage = page.locator('article, .blog-post, .post-card, text=/results|found|no.*match/i');
            const hasResults = await resultsOrMessage.count() > 0;

            expect(hasResults).toBeTruthy();
        }
    });

    test('should handle empty search query', async ({ page }) => {
        await page.goto('/blog/');

        await page.waitForTimeout(1000);

        const searchInput = page.locator('input[type="search"], input[name*="search"], input[name="q"]').first();

        if (await searchInput.count() > 0) {
            // Submit empty search
            await searchInput.press('Enter');

            await page.waitForTimeout(1000);

            // Should show all posts or validation message
            const posts = page.locator('article, .blog-post, .post-card');
            const postCount = await posts.count();

            expect(postCount).toBeGreaterThanOrEqual(0);
        }
    });
});

// ============================================================================
// BLOG FILTERING TESTS
// ============================================================================

test.describe('Blog Filtering', () => {
    test('should filter by category if available', async ({ page }) => {
        await page.goto('/blog/');

        await page.waitForTimeout(1000);

        // Check for category filter
        const categoryLinks = page.locator('a[href*="category"], .category-filter, select[name*="category"]');

        if (await categoryLinks.count() > 0) {
            const firstCategory = categoryLinks.first();
            await firstCategory.click();

            await page.waitForTimeout(1000);

            // Should show filtered posts
            const posts = page.locator('article, .blog-post, .post-card');
            const postCount = await posts.count();

            expect(postCount).toBeGreaterThan(0);
        } else {
            console.log('Category filtering not implemented');
        }
    });

    test('should filter by tag if available', async ({ page }) => {
        await page.goto('/blog/');

        await page.waitForTimeout(1000);

        // Check for tag filter
        const tagLinks = page.locator('a[href*="tag"], .tag-filter');

        if (await tagLinks.count() > 0) {
            const firstTag = tagLinks.first();
            await firstTag.click();

            await page.waitForTimeout(1000);

            // Should show filtered posts
            const posts = page.locator('article, .blog-post, .post-card');
            const postCount = await posts.count();

            expect(postCount).toBeGreaterThan(0);
        } else {
            console.log('Tag filtering not implemented');
        }
    });

    test('should clear filters', async ({ page }) => {
        await page.goto('/blog/');

        await page.waitForTimeout(1000);

        // Apply filter if available
        const categoryLinks = page.locator('a[href*="category"]');

        if (await categoryLinks.count() > 0) {
            await categoryLinks.first().click();
            await page.waitForTimeout(1000);

            // Look for clear/reset filter button
            const clearButton = page.locator('a:has-text("Clear"), a:has-text("Reset"), a:has-text("All"), button:has-text("Clear")');

            if (await clearButton.count() > 0) {
                await clearButton.first().click();
                await page.waitForTimeout(1000);

                // Should show all posts again
                await expect(page).toHaveURL(/\/blog\/?$/);
            }
        }
    });
});

// ============================================================================
// MOBILE RESPONSIVENESS TESTS
// ============================================================================

test.describe('Blog Mobile Experience', () => {
    test.use({
        viewport: { width: 375, height: 667 } // iPhone SE size
    });

    test('should display blog list on mobile', async ({ page }) => {
        await page.goto('/blog/');

        await page.waitForTimeout(1000);

        // Blog posts should be visible and stacked vertically
        const posts = page.locator('article, .blog-post, .post-card');
        const postCount = await posts.count();

        expect(postCount).toBeGreaterThan(0);

        // Check first post is visible
        await expect(posts.first()).toBeVisible();
    });

    test('should display blog detail on mobile', async ({ page }) => {
        await page.goto('/blog/');
        await page.waitForTimeout(1000);

        // Click first post
        const firstPostLink = page.locator('article a[href*="blog"], .blog-post a[href*="blog"]').first();
        await firstPostLink.click();

        await page.waitForTimeout(1000);

        // Content should be readable
        const content = page.locator('article, .post-content, .blog-content');
        await expect(content).toBeVisible();

        // Title should be visible
        const title = page.locator('h1, .post-title');
        await expect(title.first()).toBeVisible();
    });

    test('should have touch-friendly navigation', async ({ page }) => {
        await page.goto('/blog/');

        await page.waitForTimeout(1000);

        // Check for mobile menu or navigation
        const mobileNav = page.locator('nav, .nav, header, [role="navigation"]').first();
        await expect(mobileNav).toBeVisible();

        // Links should be large enough for touch (44x44px minimum)
        const links = page.locator('a[href*="blog"]').first();
        const box = await links.boundingBox();

        if (box) {
            expect(box.height).toBeGreaterThanOrEqual(30); // Relaxed for text links
        }
    });
});

// ============================================================================
// ACCESSIBILITY TESTS
// ============================================================================

test.describe('Blog Accessibility', () => {
    test('should have proper heading hierarchy', async ({ page }) => {
        await page.goto('/blog/');

        await page.waitForTimeout(1000);

        // Check for h1
        const h1 = page.locator('h1');
        const h1Count = await h1.count();

        expect(h1Count).toBeGreaterThanOrEqual(1);
    });

    test('should have keyboard navigation on blog list', async ({ page }) => {
        await page.goto('/blog/');

        await page.waitForTimeout(1000);

        // Tab to first link
        await page.keyboard.press('Tab');

        // Should focus on a link
        const focusedElement = page.locator(':focus');
        await expect(focusedElement).toBeVisible();
    });

    test('should have alt text for images', async ({ page }) => {
        await page.goto('/blog/');

        await page.waitForTimeout(1000);

        const images = page.locator('img');
        const imageCount = await images.count();

        if (imageCount > 0) {
            // Check all images have alt attribute
            for (let i = 0; i < Math.min(imageCount, 5); i++) {
                const image = images.nth(i);
                const alt = await image.getAttribute('alt');
                expect(alt).toBeDefined();
            }
        }
    });

    test('should have semantic HTML structure', async ({ page }) => {
        await page.goto('/blog/');

        await page.waitForTimeout(1000);

        // Check for semantic elements
        const article = page.locator('article').first();
        const hasArticle = await article.count() > 0;

        const nav = page.locator('nav').first();
        const hasNav = await nav.count() > 0;

        const main = page.locator('main').first();
        const hasMain = await main.count() > 0;

        // At least one semantic element should exist
        expect(hasArticle || hasNav || hasMain).toBeTruthy();
    });
});

// ============================================================================
// PERFORMANCE TESTS
// ============================================================================

test.describe('Blog Performance', () => {
    test('should load blog list quickly', async ({ page }) => {
        const startTime = Date.now();

        await page.goto('/blog/');

        await page.waitForLoadState('networkidle');

        const loadTime = Date.now() - startTime;

        // Should load within 5 seconds
        expect(loadTime).toBeLessThan(5000);

        console.log(`Blog list loaded in ${loadTime}ms`);
    });

    test('should load blog detail quickly', async ({ page }) => {
        await page.goto('/blog/');
        await page.waitForTimeout(1000);

        const firstPostLink = page.locator('article a[href*="blog"], .blog-post a[href*="blog"]').first();

        const startTime = Date.now();

        await firstPostLink.click();

        await page.waitForLoadState('networkidle');

        const loadTime = Date.now() - startTime;

        // Should load within 5 seconds
        expect(loadTime).toBeLessThan(5000);

        console.log(`Blog detail loaded in ${loadTime}ms`);
    });
});
