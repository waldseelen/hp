/**
 * PostCSS Configuration
 * Processes CSS with plugins including PurgeCSS for production
 */

const isProduction = process.env.NODE_ENV === 'production';

module.exports = {
  plugins: [
    // Tailwind CSS
    require('@tailwindcss/postcss'),
    
    // Autoprefixer for vendor prefixes
    require('autoprefixer'),
    
    // PurgeCSS for production builds
    ...(isProduction ? [
      require('@fullhuman/postcss-purgecss').default({
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
        
        // Default extractors for different file types
        defaultExtractor: content => {
          // Match all possible class names
          const broadMatches = content.match(/[^<>"'`\s]*[^<>"'`\s:]/g) || [];
          const innerMatches = content.match(/[^<>"'`\s.()]*[^<>"'`\s.():]/g) || [];
          return broadMatches.concat(innerMatches);
        },
        
        // Keep dynamic classes that might be added by JavaScript
        safelist: [
          // Alpine.js classes
          /^x-/,
          'x-cloak',
          
          // Theme classes
          'dark',
          'light',
          
          // Dynamic state classes
          'loading',
          'error',
          'success',
          'visible',
          'hidden',
          'open',
          'closed',
          'active',
          
          // Animation classes
          /^animate-/,
          /^transition-/,
          
          // Pseudo-class variants
          /^hover:/,
          /^focus:/,
          /^active:/,
          /^group-hover:/,
          
          // Responsive variants
          /^sm:/,
          /^md:/,
          /^lg:/,
          /^xl:/,
          /^2xl:/,
          
          // Custom component classes
          'btn',
          'btn-primary',
          'btn-secondary',
          'btn-outline',
          'card',
          'form-input',
          'form-label',
          'skip-nav',
          'sr-only',
          'focus-visible',
          
          // Dynamic background and text colors
          /^bg-/,
          /^text-/,
          /^border-/,
        ],
        
        // Patterns for whitelist
        whitelistPatterns: [
          /^bg-.*-\d+$/,
          /^text-.*-\d+$/,
          /^border-.*-\d+$/,
          /^rounded/,
          /^p-\d+$/,
          /^m-\d+$/,
          /^w-/,
          /^h-/,
          /^flex/,
          /^grid/,
          /^space-/,
          /^gap-/,
        ],
      })
    ] : []),
    
    // CSS minification for production
    ...(isProduction ? [
      require('cssnano')({
        preset: ['default', {
          discardComments: {
            removeAll: true,
          },
          normalizeWhitespace: true,
          minifyFontValues: true,
          minifySelectors: true,
        }]
      })
    ] : []),
  ],
};