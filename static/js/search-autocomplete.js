/**
 * Advanced Search Autocomplete System with Debouncing
 * Features:
 * - Debounced search requests to reduce server load
 * - Real-time suggestions with keyboard navigation
 * - Search result highlighting
 * - Search analytics tracking
 * - Responsive design with mobile support
 */

class SearchAutocomplete {
    constructor(inputSelector, resultsSelector, options = {}) {
        this.input = document.querySelector(inputSelector);
        this.resultsContainer = document.querySelector(resultsSelector);

        if (!this.input || !this.resultsContainer) {
            console.error('Search autocomplete: Input or results container not found');
            return;
        }

        this.options = {
            debounceDelay: 300,
            minQueryLength: 2,
            maxSuggestions: 10,
            apiEndpoint: '/api/search/autocomplete/',
            searchEndpoint: '/api/search/',
            cacheTimeout: 300000, // 5 minutes
            enableAnalytics: true,
            enableKeyboardNav: true,
            enableCategories: true,
            showRecentSearches: true,
            highlightQuery: true,
            ...options
        };

        this.cache = new Map();
        this.currentQuery = '';
        this.selectedIndex = -1;
        this.isVisible = false;
        this.debounceTimer = null;
        this.analytics = {
            searches: [],
            selections: [],
            abandonedSearches: []
        };

        this.init();
    }

    /**
     * Initialize the autocomplete system
     */
    init() {
        this.setupEventListeners();
        this.setupResultsContainer();
        this.loadRecentSearches();

        // Preload popular searches
        if (this.options.showRecentSearches) {
            this.preloadPopularSearches();
        }

        console.log('Search autocomplete initialized');
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Input events
        this.input.addEventListener('input', (e) => this.handleInput(e));
        this.input.addEventListener('focus', (e) => this.handleFocus(e));
        this.input.addEventListener('blur', (e) => this.handleBlur(e));

        // Keyboard navigation
        if (this.options.enableKeyboardNav) {
            this.input.addEventListener('keydown', (e) => this.handleKeydown(e));
        }

        // Click outside to close
        document.addEventListener('click', (e) => {
            if (!this.input.contains(e.target) && !this.resultsContainer.contains(e.target)) {
                this.hide();
            }
        });

        // Prevent form submission on Enter if suggestion is selected
        const form = this.input.closest('form');
        if (form) {
            form.addEventListener('submit', (e) => {
                if (this.selectedIndex >= 0) {
                    e.preventDefault();
                    this.selectSuggestion(this.selectedIndex);
                }
            });
        }
    }

    /**
     * Setup results container structure
     */
    setupResultsContainer() {
        this.resultsContainer.className = 'search-autocomplete-results';
        this.resultsContainer.setAttribute('role', 'listbox');
        this.resultsContainer.style.display = 'none';

        // Add CSS styles
        if (!document.querySelector('#search-autocomplete-styles')) {
            const styles = document.createElement('style');
            styles.id = 'search-autocomplete-styles';
            styles.textContent = this.getAutocompleteCSS();
            document.head.appendChild(styles);
        }
    }

    /**
     * Handle input events with debouncing
     */
    handleInput(e) {
        const query = e.target.value.trim();

        // Clear previous timer
        if (this.debounceTimer) {
            clearTimeout(this.debounceTimer);
        }

        // Reset selection
        this.selectedIndex = -1;

        if (query.length < this.options.minQueryLength) {
            this.hide();
            return;
        }

        // Debounce the search
        this.debounceTimer = setTimeout(() => {
            this.performSearch(query);
        }, this.options.debounceDelay);
    }

    /**
     * Handle input focus
     */
    handleFocus(e) {
        const query = e.target.value.trim();

        if (query.length >= this.options.minQueryLength) {
            this.performSearch(query);
        } else if (this.options.showRecentSearches) {
            this.showRecentSearches();
        }
    }

    /**
     * Handle input blur with delay to allow clicks on suggestions
     */
    handleBlur(e) {
        setTimeout(() => {
            if (!this.resultsContainer.matches(':hover')) {
                this.hide();
            }
        }, 150);
    }

    /**
     * Handle keyboard navigation
     */
    handleKeydown(e) {
        if (!this.isVisible) return;

        const suggestions = this.resultsContainer.querySelectorAll('.suggestion-item');

        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                this.selectedIndex = Math.min(this.selectedIndex + 1, suggestions.length - 1);
                this.updateSelection();
                break;

            case 'ArrowUp':
                e.preventDefault();
                this.selectedIndex = Math.max(this.selectedIndex - 1, -1);
                this.updateSelection();
                break;

            case 'Enter':
                e.preventDefault();
                if (this.selectedIndex >= 0) {
                    this.selectSuggestion(this.selectedIndex);
                } else {
                    // Submit form with current query
                    this.submitSearch(this.input.value);
                }
                break;

            case 'Escape':
                this.hide();
                this.input.blur();
                break;

            case 'Tab':
                if (this.selectedIndex >= 0) {
                    e.preventDefault();
                    this.selectSuggestion(this.selectedIndex);
                }
                break;
        }
    }

    /**
     * Perform search and show suggestions
     */
    async performSearch(query) {
        if (query === this.currentQuery) return;

        this.currentQuery = query;

        // Check cache first
        const cacheKey = `search_${query.toLowerCase()}`;
        const cached = this.getCached(cacheKey);

        if (cached) {
            this.showSuggestions(cached, query);
            return;
        }

        try {
            // Show loading state
            this.showLoading();

            const response = await fetch(`${this.options.apiEndpoint}?q=${encodeURIComponent(query)}`, {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/json',
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();

            // Cache the results
            this.setCached(cacheKey, data);

            // Show suggestions
            this.showSuggestions(data, query);

            // Track search analytics
            if (this.options.enableAnalytics) {
                this.trackSearch(query, data.suggestions?.length || 0);
            }

        } catch (error) {
            console.error('Search autocomplete error:', error);
            this.showError('Search suggestions unavailable');
        }
    }

    /**
     * Show suggestions in the results container
     */
    showSuggestions(data, query) {
        const suggestions = data.suggestions || [];

        if (suggestions.length === 0) {
            this.showNoResults(query);
            return;
        }

        let html = '';

        // Group suggestions by type if categories are enabled
        if (this.options.enableCategories) {
            const grouped = this.groupSuggestionsByType(suggestions);

            for (const [type, items] of Object.entries(grouped)) {
                if (items.length === 0) continue;

                html += `<div class="suggestion-category">
                    <div class="category-header">${this.getCategoryName(type)}</div>
                </div>`;

                items.forEach((suggestion, index) => {
                    html += this.renderSuggestionItem(suggestion, query, index);
                });
            }
        } else {
            suggestions.forEach((suggestion, index) => {
                html += this.renderSuggestionItem(suggestion, query, index);
            });
        }

        // Add "View all results" option
        html += `<div class="suggestion-item view-all-item" data-index="${suggestions.length}">
            <div class="suggestion-content">
                <span class="suggestion-text">View all results for "${query}"</span>
                <span class="suggestion-meta">Search</span>
            </div>
        </div>`;

        this.resultsContainer.innerHTML = html;
        this.setupSuggestionEvents();
        this.show();
    }

    /**
     * Render individual suggestion item
     */
    renderSuggestionItem(suggestion, query, index) {
        const highlightedText = this.options.highlightQuery
            ? this.highlightQuery(suggestion.text, query)
            : suggestion.text;

        const icon = this.getSuggestionIcon(suggestion.type);
        const meta = suggestion.category || suggestion.type || '';

        return `<div class="suggestion-item" data-index="${index}" data-text="${suggestion.text}" data-url="${suggestion.url || ''}">
            <div class="suggestion-content">
                <span class="suggestion-icon">${icon}</span>
                <span class="suggestion-text">${highlightedText}</span>
                ${meta ? `<span class="suggestion-meta">${meta}</span>` : ''}
            </div>
        </div>`;
    }

    /**
     * Setup click events for suggestions
     */
    setupSuggestionEvents() {
        const suggestions = this.resultsContainer.querySelectorAll('.suggestion-item');

        suggestions.forEach((item, index) => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                this.selectSuggestion(index);
            });

            item.addEventListener('mouseenter', () => {
                this.selectedIndex = index;
                this.updateSelection();
            });
        });
    }

    /**
     * Select a suggestion
     */
    selectSuggestion(index) {
        const suggestion = this.resultsContainer.querySelector(`[data-index="${index}"]`);

        if (!suggestion) return;

        const text = suggestion.getAttribute('data-text');
        const url = suggestion.getAttribute('data-url');

        if (suggestion.classList.contains('view-all-item')) {
            // Submit search for "view all results"
            this.submitSearch(this.currentQuery);
        } else if (url) {
            // Navigate to specific result
            window.location.href = url;
        } else {
            // Update search input
            this.input.value = text;
            this.submitSearch(text);
        }

        // Track selection
        if (this.options.enableAnalytics) {
            this.trackSelection(text, index);
        }

        // Save to recent searches
        this.saveRecentSearch(text);

        this.hide();
    }

    /**
     * Submit search form or navigate to search page
     */
    submitSearch(query) {
        const form = this.input.closest('form');

        if (form) {
            form.submit();
        } else {
            // Navigate to search page
            window.location.href = `${this.options.searchEndpoint}?q=${encodeURIComponent(query)}`;
        }
    }

    /**
     * Show loading state
     */
    showLoading() {
        this.resultsContainer.innerHTML = `
            <div class="suggestion-loading">
                <div class="loading-spinner"></div>
                <span>Searching...</span>
            </div>
        `;
        this.show();
    }

    /**
     * Show error state
     */
    showError(message) {
        this.resultsContainer.innerHTML = `
            <div class="suggestion-error">
                <span class="error-icon">⚠️</span>
                <span>${message}</span>
            </div>
        `;
        this.show();
    }

    /**
     * Show no results state
     */
    showNoResults(query) {
        this.resultsContainer.innerHTML = `
            <div class="suggestion-empty">
                <span>No suggestions for "${query}"</span>
                <div class="suggestion-item view-all-item" data-index="0">
                    <div class="suggestion-content">
                        <span class="suggestion-text">Search anyway</span>
                    </div>
                </div>
            </div>
        `;
        this.setupSuggestionEvents();
        this.show();
    }

    /**
     * Show recent searches
     */
    showRecentSearches() {
        const recent = this.getRecentSearches();

        if (recent.length === 0) return;

        let html = '<div class="suggestion-category"><div class="category-header">Recent Searches</div></div>';

        recent.forEach((search, index) => {
            html += `<div class="suggestion-item recent-search" data-index="${index}" data-text="${search}">
                <div class="suggestion-content">
                    <span class="suggestion-icon">🕒</span>
                    <span class="suggestion-text">${search}</span>
                    <button class="remove-recent" data-search="${search}">×</button>
                </div>
            </div>`;
        });

        this.resultsContainer.innerHTML = html;
        this.setupSuggestionEvents();
        this.setupRemoveRecentEvents();
        this.show();
    }

    /**
     * Update visual selection
     */
    updateSelection() {
        const suggestions = this.resultsContainer.querySelectorAll('.suggestion-item');

        suggestions.forEach((item, index) => {
            item.classList.toggle('selected', index === this.selectedIndex);
        });

        // Update input value for keyboard navigation
        if (this.selectedIndex >= 0 && this.selectedIndex < suggestions.length) {
            const selectedText = suggestions[this.selectedIndex].getAttribute('data-text');
            if (selectedText) {
                this.input.value = selectedText;
            }
        }
    }

    /**
     * Show results container
     */
    show() {
        this.resultsContainer.style.display = 'block';
        this.resultsContainer.setAttribute('aria-hidden', 'false');
        this.isVisible = true;
    }

    /**
     * Hide results container
     */
    hide() {
        this.resultsContainer.style.display = 'none';
        this.resultsContainer.setAttribute('aria-hidden', 'true');
        this.isVisible = false;
        this.selectedIndex = -1;
    }

    /**
     * Utility methods
     */
    groupSuggestionsByType(suggestions) {
        return suggestions.reduce((groups, suggestion) => {
            const type = suggestion.type || 'general';
            if (!groups[type]) groups[type] = [];
            groups[type].push(suggestion);
            return groups;
        }, {});
    }

    getCategoryName(type) {
        const names = {
            'title': 'Pages',
            'term': 'Popular Terms',
            'tag': 'Tags',
            'category': 'Categories',
            'recent': 'Recent Searches',
            'general': 'Suggestions'
        };
        return names[type] || type;
    }

    getSuggestionIcon(type) {
        const icons = {
            'title': '📄',
            'term': '🔍',
            'tag': '🏷️',
            'category': '📂',
            'recent': '🕒',
            'blog_post': '📝',
            'tool': '🔧',
            'ai_tool': '🤖'
        };
        return icons[type] || '💭';
    }

    highlightQuery(text, query) {
        if (!query || !text) return text;

        const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
        return text.replace(regex, '<mark>$1</mark>');
    }

    /**
     * Cache management
     */
    setCached(key, data) {
        this.cache.set(key, {
            data,
            timestamp: Date.now()
        });
    }

    getCached(key) {
        const cached = this.cache.get(key);

        if (!cached) return null;

        if (Date.now() - cached.timestamp > this.options.cacheTimeout) {
            this.cache.delete(key);
            return null;
        }

        return cached.data;
    }

    /**
     * Recent searches management
     */
    saveRecentSearch(query) {
        if (!query) return;

        let recent = this.getRecentSearches();
        recent = recent.filter(search => search !== query);
        recent.unshift(query);
        recent = recent.slice(0, 10); // Keep only 10 recent searches

        localStorage.setItem('recentSearches', JSON.stringify(recent));
    }

    getRecentSearches() {
        try {
            return JSON.parse(localStorage.getItem('recentSearches')) || [];
        } catch {
            return [];
        }
    }

    setupRemoveRecentEvents() {
        const removeButtons = this.resultsContainer.querySelectorAll('.remove-recent');

        removeButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.stopPropagation();
                const search = button.getAttribute('data-search');
                this.removeRecentSearch(search);
                this.showRecentSearches();
            });
        });
    }

    removeRecentSearch(query) {
        let recent = this.getRecentSearches();
        recent = recent.filter(search => search !== query);
        localStorage.setItem('recentSearches', JSON.stringify(recent));
    }

    /**
     * Analytics
     */
    trackSearch(query, resultCount) {
        this.analytics.searches.push({
            query,
            resultCount,
            timestamp: Date.now()
        });
    }

    trackSelection(text, index) {
        this.analytics.selections.push({
            text,
            index,
            timestamp: Date.now()
        });
    }

    /**
     * Preload popular searches
     */
    async preloadPopularSearches() {
        try {
            const response = await fetch('/api/search/popular/');
            const data = await response.json();

            // Cache popular searches
            this.setCached('popular_searches', data);
        } catch (error) {
            console.warn('Could not load popular searches:', error);
        }
    }

    /**
     * Get CSS styles for autocomplete
     */
    getAutocompleteCSS() {
        return `
            .search-autocomplete-results {
                position: absolute;
                top: 100%;
                left: 0;
                right: 0;
                background: white;
                border: 1px solid #e1e5e9;
                border-radius: 8px;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                z-index: 1000;
                max-height: 400px;
                overflow-y: auto;
            }

            .dark .search-autocomplete-results {
                background: #1f2937;
                border-color: #374151;
            }

            .suggestion-category {
                padding: 8px 0;
            }

            .category-header {
                padding: 8px 16px;
                font-size: 12px;
                font-weight: 600;
                color: #6b7280;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }

            .suggestion-item {
                padding: 12px 16px;
                cursor: pointer;
                border-bottom: 1px solid #f3f4f6;
                transition: background-color 0.15s ease;
            }

            .suggestion-item:hover,
            .suggestion-item.selected {
                background-color: #f9fafb;
            }

            .dark .suggestion-item {
                border-bottom-color: #374151;
            }

            .dark .suggestion-item:hover,
            .dark .suggestion-item.selected {
                background-color: #374151;
            }

            .suggestion-content {
                display: flex;
                align-items: center;
                gap: 8px;
            }

            .suggestion-icon {
                font-size: 14px;
                flex-shrink: 0;
            }

            .suggestion-text {
                flex: 1;
                font-size: 14px;
                color: #1f2937;
            }

            .dark .suggestion-text {
                color: #f9fafb;
            }

            .suggestion-text mark {
                background-color: #fef3c7;
                color: #92400e;
                font-weight: 600;
                padding: 0 2px;
                border-radius: 2px;
            }

            .dark .suggestion-text mark {
                background-color: #451a03;
                color: #fbbf24;
            }

            .suggestion-meta {
                font-size: 12px;
                color: #6b7280;
            }

            .suggestion-loading,
            .suggestion-error,
            .suggestion-empty {
                padding: 20px 16px;
                text-align: center;
                color: #6b7280;
            }

            .loading-spinner {
                display: inline-block;
                width: 16px;
                height: 16px;
                border: 2px solid #e5e7eb;
                border-radius: 50%;
                border-top-color: #3b82f6;
                animation: spin 1s ease-in-out infinite;
                margin-right: 8px;
            }

            .remove-recent {
                background: none;
                border: none;
                color: #9ca3af;
                cursor: pointer;
                padding: 2px 6px;
                font-size: 16px;
                line-height: 1;
                border-radius: 4px;
            }

            .remove-recent:hover {
                background-color: #fee2e2;
                color: #dc2626;
            }

            .view-all-item {
                border-top: 1px solid #e5e7eb;
                font-weight: 500;
            }

            @keyframes spin {
                to { transform: rotate(360deg); }
            }
        `;
    }

    /**
     * Cleanup and destroy
     */
    destroy() {
        if (this.debounceTimer) {
            clearTimeout(this.debounceTimer);
        }

        this.cache.clear();
        this.hide();

        console.log('Search autocomplete destroyed');
    }
}

// Auto-initialize search autocomplete when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Initialize for main search input
    const searchInput = document.querySelector('input[name="search"], #search-input, .search-input');
    const resultsContainer = document.querySelector('#search-results, .search-autocomplete-container');

    if (searchInput && resultsContainer) {
        window.searchAutocomplete = new SearchAutocomplete(
            searchInput,
            resultsContainer,
            {
                debounceDelay: 300,
                minQueryLength: 2,
                maxSuggestions: 8,
                enableAnalytics: true,
                enableKeyboardNav: true,
                showRecentSearches: true
            }
        );
    }

    console.log('Search autocomplete system initialized');
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SearchAutocomplete;
}