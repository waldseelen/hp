/**
 * Critical CSS Generator
 * Extracts above-the-fold CSS for faster page load times
 */

const fs = require('fs');
const path = require('path');

// Critical CSS extraction function
async function generateCriticalCSS() {
    try {
        console.log('🚀 Starting Critical CSS generation...');

        // Define critical pages for CSS extraction
        const criticalPages = [
            {
                name: 'home',
                url: 'http://127.0.0.1:8000/',
                template: 'templates/main/home.html',
                output: 'static/css/critical/home.css'
            },
            {
                name: 'blog',
                url: 'http://127.0.0.1:8000/blog/',
                template: 'templates/blog/list.html',
                output: 'static/css/critical/blog.css'
            },
            {
                name: 'contact',
                url: 'http://127.0.0.1:8000/contact/',
                template: 'templates/contact/form.html',
                output: 'static/css/critical/contact.css'
            }
        ];

        // Create critical CSS directory
        const criticalDir = path.join(__dirname, '..', 'static', 'css', 'critical');
        if (!fs.existsSync(criticalDir)) {
            fs.mkdirSync(criticalDir, { recursive: true });
        }

        // Manual critical CSS rules for above-the-fold content
        const baseCriticalCSS = `
/* Critical CSS - Above the fold styles */
/* Base styles for immediate render */
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background-color: #0f172a;
  color: #f8fafc;
  transition: background-color 0.3s ease;
}

/* Navigation critical styles */
nav {
  background-color: rgba(15, 23, 42, 0.9);
  backdrop-filter: blur(8px);
  border-bottom: 1px solid rgba(71, 85, 105, 0.5);
  position: sticky;
  top: 0;
  z-index: 40;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1rem;
}

/* Skip navigation for accessibility */
.skip-nav {
  position: absolute;
  top: -40px;
  left: 6px;
  z-index: 9999;
  padding: 8px 12px;
  background: #0f172a;
  color: #f8fafc;
  text-decoration: none;
  border-radius: 0 0 4px 4px;
  border: 2px solid #c8b560;
  transform: translateY(-100%);
  transition: transform 0.3s ease;
}

.skip-nav:focus {
  transform: translateY(0%);
  top: 0;
}

/* Critical button styles */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
  font-weight: 500;
  border-radius: 0.5rem;
  transition: all 0.2s ease;
  border: none;
  cursor: pointer;
  text-decoration: none;
}

.btn-primary {
  background-color: #c8b560;
  color: #ffffff;
}

.btn-primary:hover {
  background-color: #a89550;
}

/* Critical text utilities */
.text-center { text-align: center; }
.text-white { color: #ffffff; }
.text-gray-300 { color: #d1d5db; }
.text-primary-400 { color: #f0e68c; }

/* Critical spacing utilities */
.p-4 { padding: 1rem; }
.py-4 { padding-top: 1rem; padding-bottom: 1rem; }
.px-4 { padding-left: 1rem; padding-right: 1rem; }
.mb-4 { margin-bottom: 1rem; }
.mt-8 { margin-top: 2rem; }

/* Critical layout utilities */
.flex { display: flex; }
.items-center { align-items: center; }
.justify-between { justify-content: space-between; }
.w-full { width: 100%; }
.hidden { display: none; }
.block { display: block; }

/* Critical responsive utilities */
@media (min-width: 768px) {
  .md\\:flex { display: flex; }
  .md\\:hidden { display: none; }
}

/* Loading state to prevent FOUC */
[x-cloak] { display: none !important; }

/* Critical focus styles */
*:focus-visible {
  outline: 2px solid #c8b560;
  outline-offset: 2px;
}

/* Dark theme variables */
:root {
  --primary-500: #c8b560;
  --primary-600: #a89550;
  --bg-primary: #0f172a;
  --text-primary: #f8fafc;
}

/* Starfield background for immediate render */
.starfield {
  position: fixed;
  inset: 0;
  opacity: 0.1;
  background-image: radial-gradient(2px 2px at 20px 30px, #eee, transparent),
                    radial-gradient(2px 2px at 40px 70px, #fff, transparent);
  background-repeat: repeat;
  background-size: 100px 100px;
}
`;

        // Write base critical CSS
        fs.writeFileSync(
            path.join(criticalDir, 'base.css'),
            baseCriticalCSS.trim()
        );

        // Page-specific critical CSS
        const homeCriticalCSS = `
/* Home page critical styles */
.hero-section {
  min-height: 60vh;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.hero-title {
  font-size: 3rem;
  font-weight: bold;
  background: linear-gradient(to right, #f0e68c, #c8b560);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  margin-bottom: 1rem;
}

@media (min-width: 768px) {
  .hero-title {
    font-size: 4rem;
  }
}
`;

        fs.writeFileSync(
            path.join(criticalDir, 'home.css'),
            (baseCriticalCSS + homeCriticalCSS).trim()
        );

        // Blog critical CSS
        const blogCriticalCSS = `
/* Blog page critical styles */
.blog-header {
  padding: 2rem 0;
  text-align: center;
}

.blog-grid {
  display: grid;
  gap: 1.5rem;
  margin-top: 2rem;
}

@media (min-width: 768px) {
  .blog-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (min-width: 1024px) {
  .blog-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

.blog-card {
  background-color: rgba(30, 41, 59, 0.5);
  border-radius: 0.5rem;
  padding: 1.5rem;
  border: 1px solid rgba(71, 85, 105, 0.3);
}
`;

        fs.writeFileSync(
            path.join(criticalDir, 'blog.css'),
            (baseCriticalCSS + blogCriticalCSS).trim()
        );

        // Contact critical CSS
        const contactCriticalCSS = `
/* Contact page critical styles */
.contact-form {
  background-color: rgba(30, 41, 59, 0.5);
  border-radius: 0.5rem;
  padding: 2rem;
}

.form-input {
  width: 100%;
  padding: 0.75rem 1rem;
  background-color: rgba(55, 65, 81, 0.5);
  border: 1px solid rgba(107, 114, 128, 1);
  border-radius: 0.5rem;
  color: #ffffff;
}

.form-input:focus {
  border-color: #c8b560;
  outline: none;
}

.form-label {
  display: block;
  font-size: 0.875rem;
  font-weight: 500;
  color: #d1d5db;
  margin-bottom: 0.5rem;
}
`;

        fs.writeFileSync(
            path.join(criticalDir, 'contact.css'),
            (baseCriticalCSS + contactCriticalCSS).trim()
        );

        console.log('✅ Critical CSS files generated successfully!');
        console.log('📁 Files created:');
        console.log('   - static/css/critical/base.css');
        console.log('   - static/css/critical/home.css');
        console.log('   - static/css/critical/blog.css');
        console.log('   - static/css/critical/contact.css');

        // Generate usage instructions
        const usageInstructions = `
<!-- Critical CSS Usage in Django Templates -->

<!-- Base template (templates/base.html) -->
<style>
  {% include "static/css/critical/base.css" %}
</style>

<!-- Home page (templates/main/home.html) -->
{% block critical_css %}
<style>
  {% include "static/css/critical/home.css" %}
</style>
{% endblock %}

<!-- Blog page (templates/blog/list.html) -->
{% block critical_css %}
<style>
  {% include "static/css/critical/blog.css" %}
</style>
{% endblock %}

<!-- Contact page (templates/contact/form.html) -->
{% block critical_css %}
<style>
  {% include "static/css/critical/contact.css" %}
</style>
{% endblock %}

<!-- Load non-critical CSS asynchronously -->
<link rel="preload" href="{% static 'css/output.css' %}" as="style" onload="this.onload=null;this.rel='stylesheet'">
<noscript><link rel="stylesheet" href="{% static 'css/output.css' %}"></noscript>
`;

        fs.writeFileSync(
            path.join(criticalDir, 'USAGE.md'),
            usageInstructions.trim()
        );

        console.log('   - static/css/critical/USAGE.md (implementation guide)');

    } catch (error) {
        console.error('❌ Error generating critical CSS:', error);
        process.exit(1);
    }
}

// Run if called directly
if (require.main === module) {
    generateCriticalCSS();
}

module.exports = { generateCriticalCSS };
