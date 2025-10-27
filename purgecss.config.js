/**
 * PurgeCSS Configuration
 * Removes unused CSS classes to optimize bundle size
 */

module.exports = {
    content: [
        './templates/**/*.html',
        './static/js/**/*.js',
        './apps/**/*.py',
        './main/**/*.py',
        './blog/**/*.py',
        './tools/**/*.py',
        './contact/**/*.py',
        './chat/**/*.py',
    ],

    css: [
        './static/css/consolidated.css',
        './static/css/components-compiled.css',
        './static/css/custom.css',
    ],

    // Output directory for purged CSS
    output: './static/css/purged/',

    // CSS selectors to keep (never purge)
    safelist: [
        // Alpine.js dynamic classes
        /^x-/,
        'x-cloak',

        // Dynamic theme classes
        'dark',
        'light',

        // Animation and transition classes that may be added dynamically
        /^animate-/,
        /^transition-/,
        /^transform/,

        // Focus and hover states
        /^focus:/,
        /^hover:/,
        /^active:/,

        // Responsive classes
        /^sm:/,
        /^md:/,
        /^lg:/,
        /^xl:/,
        /^2xl:/,

        // State classes added by JavaScript
        'loading',
        'error',
        'success',
        'visible',
        'hidden',
        'open',
        'closed',

        // ARIA and accessibility classes
        /^sr-/,
        'sr-only',
        'skip-nav',
        'focus-visible',

        // Custom utility classes
        'btn',
        'btn-primary',
        'btn-secondary',
        'btn-outline',
        'card',
        'form-input',
        'form-label',
        'form-error',

        // Classes used in Django templates but might not be detected
        'pagination',
        'breadcrumb',
        'toast',
        'modal',
        'dropdown',

        // Progress and loading states
        'progress',
        'spinner',
        'skeleton',

        // Blog specific classes
        'post-content',
        'post-meta',
        'tag',
        'category',

        // Portfolio specific classes
        'project-card',
        'skill-item',
        'timeline',

        // Language switching classes
        'lang-switch',
        'active-lang',
    ],

    // Patterns to match for dynamic class detection
    defaultExtractor: content => {
        // Extract classes from content
        const broadMatches = content.match(/[^<>"'`\s]*[^<>"'`\s:]/g) || [];
        const innerMatches = content.match(/[^<>"'`\s.()]*[^<>"'`\s.():]/g) || [];

        return broadMatches.concat(innerMatches);
    },

    // Additional extraction patterns for different file types
    extractors: [
        {
            extractor: content => {
                // Extract Django template variables and tags
                const djangoClasses = content.match(/class=["']([^"']+)["']/g) || [];
                const alpineClasses = content.match(/x-bind:class=["']([^"']+)["']/g) || [];

                return [...djangoClasses, ...alpineClasses]
                    .join(' ')
                    .split(/\s+/)
                    .filter(cls => cls.length > 0);
            },
            extensions: ['html']
        },
        {
            extractor: content => {
                // Extract JavaScript class manipulations
                const jsClasses = content.match(/classList\.(add|remove|toggle)\(['"]([^'"]+)['"]\)/g) || [];
                const classNamePattern = content.match(/className\s*=\s*['"]([^'"]+)['"]/g) || [];

                return [...jsClasses, ...classNamePattern]
                    .join(' ')
                    .split(/\s+/)
                    .filter(cls => cls.length > 0);
            },
            extensions: ['js']
        }
    ],

    // Whitelist patterns for dynamic content
    whitelistPatterns: [
        /^bg-/,
        /^text-/,
        /^border-/,
        /^rounded/,
        /^p-/,
        /^m-/,
        /^w-/,
        /^h-/,
        /^flex/,
        /^grid/,
        /^space-/,
        /^gap-/,
    ],

    // Remove unused keyframes
    keyframes: true,

    // Remove unused font faces
    fontFace: true,

    // Variables to keep
    variables: true,

    // Reject selectors (always remove these)
    rejected: true,

    // Output rejected selectors to file for debugging
    rejectedCss: './static/css/purged/rejected.css',
};
