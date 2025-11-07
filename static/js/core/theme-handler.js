// Theme Handler - CSP-compliant dark mode management
(function () {
    'use strict';

    // Initialize theme management
    function initTheme() {
        const body = document.getElementById('app-body');
        if (!body) { return; }

        // Get saved theme or default to dark
        const savedTheme = localStorage.getItem('darkMode');
        const isDarkMode = savedTheme === 'true' || savedTheme === null;

        // Apply initial theme
        document.documentElement.classList.toggle('dark', isDarkMode);
        body.classList.toggle('dark', isDarkMode);

        // Store the theme state for Alpine.js components
        window.themeState = {
            darkMode: isDarkMode,
            toggle: function () {
                this.darkMode = !this.darkMode;
                localStorage.setItem('darkMode', this.darkMode);
                document.documentElement.classList.toggle('dark', this.darkMode);
                body.classList.toggle('dark', this.darkMode);

                // Dispatch custom event for other components
                document.dispatchEvent(new CustomEvent('theme-changed', {
                    detail: { darkMode: this.darkMode }
                }));
            }
        };
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initTheme);
    } else {
        initTheme();
    }
})();
