/* global closeSearchModal */
(function () {
    const modal = document.getElementById('search-modal');
    if (!modal) {
        return;
    }

    const input = modal.querySelector('#search-input');
    const resultsContainer = modal.querySelector('#search-results');
    const loadingIndicator = modal.querySelector('#search-loading');
    const emptyState = modal.querySelector('#search-no-results');
    const recentSection = modal.querySelector('#search-recent');
    const recentList = modal.querySelector('#recent-searches-list');
    const suggestionsSection = modal.querySelector('#search-suggestions');
    const clearRecentButton = modal.querySelector('[data-search-clear]');
    const suggestionButtons = modal.querySelectorAll('.search-modal__suggestion');

    if (!input || !resultsContainer) {
        return;
    }

    const RECENT_STORAGE_KEY = 'portfolio_recent_searches';
    const MIN_QUERY = 2;
    const DEBOUNCE_DELAY = 320;

    let items = [];
    let selectedIndex = -1;
    let debounceTimer = null;

    function debounce(fn, delay) {
        return function (...args) {
            window.clearTimeout(debounceTimer);
            debounceTimer = window.setTimeout(() => fn.apply(this, args), delay);
        };
    }

    function getRecentSearches() {
        try {
            const stored = window.localStorage.getItem(RECENT_STORAGE_KEY);
            if (!stored) {
                return [];
            }
            const parsed = JSON.parse(stored);
            return Array.isArray(parsed) ? parsed : [];
        } catch (error) {
            console.warn('search: unable to read recent searches', error);
            return [];
        }
    }

    function saveRecentSearch(query) {
        const trimmed = (query || '').trim();
        if (!trimmed) {
            return;
        }
        const recent = getRecentSearches().filter(item => item.toLowerCase() !== trimmed.toLowerCase());
        recent.unshift(trimmed);
        const limited = recent.slice(0, 10);
        try {
            window.localStorage.setItem(RECENT_STORAGE_KEY, JSON.stringify(limited));
        } catch (error) {
            console.warn('search: unable to persist recent searches', error);
        }
    }

    function clearRecentSearches() {
        try {
            window.localStorage.removeItem(RECENT_STORAGE_KEY);
        } catch (error) {
            console.warn('search: unable to clear recent searches', error);
        }
        renderRecentSearches();
    }

    function renderRecentSearches() {
        const recent = getRecentSearches();
        recentList.innerHTML = '';
        if (!recent.length) {
            recentSection.hidden = true;
            suggestionsSection.hidden = false;
            return;
        }
        recentSection.hidden = false;
        recent.forEach(term => {
            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'search-modal__suggestion';
            button.textContent = term;
            button.addEventListener('click', () => {
                input.value = term;
                triggerSearch(term);
                input.focus();
            });
            recentList.appendChild(button);
        });
    }

    function setLoading(state) {
        if (!loadingIndicator) {
            return;
        }
        loadingIndicator.hidden = !state;
    }

    function showEmpty(query) {
        emptyState.hidden = false;
        resultsContainer.hidden = true;
        resultsContainer.setAttribute('aria-hidden', 'true');
        recentSection.hidden = true;
        suggestionsSection.hidden = false;
        emptyState.querySelector('.search-modal__empty-title').textContent = window.gettext ? window.gettext('No results found') : 'No results found';
        const textEl = emptyState.querySelector('.search-modal__empty-text');
        if (textEl && query) {
            textEl.textContent = window.gettext ? window.gettext('Try another keyword.') : 'Try another keyword.';
        }
        resultsContainer.hidden = true;
    }

    function clearEmpty() {
        if (emptyState) {
            emptyState.hidden = true;
        }
    }

    function clearResults() {
        resultsContainer.innerHTML = '';
        resultsContainer.hidden = true;
        items = [];
        selectedIndex = -1;
    }

    function highlight(text, query) {
        if (!query) {
            return text;
        }
        const escaped = query.replace(/[.*+?^${}()|[\]\\]/g, '\$&');
        const regex = new RegExp(`(${escaped})`, 'ig');
        return text.replace(regex, '<mark>$1</mark>');
    }

    function renderResults(data, query) {
        const suggestions = Array.isArray(data?.suggestions) ? data.suggestions : [];

        if (!suggestions.length) {
            showEmpty(query);
            return;
        }

        clearEmpty();
        recentSection.hidden = true;
        suggestionsSection.hidden = true;
        resultsContainer.hidden = false;
        resultsContainer.setAttribute('aria-hidden', 'false');
        resultsContainer.innerHTML = '';
        items = suggestions;
        selectedIndex = -1;

        const fragment = document.createDocumentFragment();

        suggestions.forEach((suggestion, index) => {
            const result = document.createElement('a');
            result.className = 'search-modal__result';
            result.href = suggestion.url || '#';
            result.dataset.index = index;
            result.setAttribute('role', 'option');

            const icon = document.createElement('div');
            icon.className = 'search-modal__result-icon';
            icon.textContent = suggestion.icon || '';

            const body = document.createElement('div');
            body.className = 'search-modal__result-body';

            const title = document.createElement('h4');
            title.className = 'search-modal__result-title';
            title.innerHTML = highlight(suggestion.title || '', query);

            const description = document.createElement('p');
            description.className = 'search-modal__result-text';
            if (suggestion.description) {
                description.innerHTML = highlight(suggestion.description, query);
            }

            const meta = document.createElement('div');
            meta.className = 'search-modal__result-meta';

            const tag = document.createElement('span');
            tag.className = 'search-modal__result-tag';
            tag.textContent = suggestion.type ? suggestion.type : '';

            const date = document.createElement('span');
            date.className = 'search-modal__result-date';
            date.textContent = suggestion.date || '';

            meta.appendChild(tag);
            meta.appendChild(date);

            body.appendChild(title);
            if (suggestion.description) {
                body.appendChild(description);
            }
            body.appendChild(meta);

            result.appendChild(icon);
            result.appendChild(body);

            result.addEventListener('mousedown', event => {
                event.preventDefault();
                selectResult(index);
            });

            fragment.appendChild(result);
        });

        resultsContainer.appendChild(fragment);
    }

    function updateSelection(nextIndex) {
        const resultElements = resultsContainer.querySelectorAll('.search-modal__result');
        resultElements.forEach(element => element.classList.remove('selected'));

        if (!resultElements.length) {
            selectedIndex = -1;
            return;
        }

        if (nextIndex < 0) {
            nextIndex = resultElements.length - 1;
        } else if (nextIndex >= resultElements.length) {
            nextIndex = 0;
        }

        selectedIndex = nextIndex;
        const selected = resultElements[selectedIndex];
        selected.classList.add('selected');
        selected.scrollIntoView({ block: 'nearest' });
    }

    function openResult(item, query) {
        if (item?.url) {
            window.location.href = item.url;
            return;
        }
        if (query) {
            window.location.href = `/search/?q=${encodeURIComponent(query)}`;
        }
    }

    function selectResult(index) {
        if (!items.length) {
            return;
        }
        const item = items[index >= 0 ? index : 0];
        const query = input.value.trim();
        saveRecentSearch(query);
        closeSearchModal();
        openResult(item, query);
    }

    async function requestSuggestions(query) {
        if (!query || query.length < MIN_QUERY) {
            clearResults();
            renderRecentSearches();
            setLoading(false);
            return;
        }

        setLoading(true);
        clearEmpty();

        try {
            const response = await fetch(`/api/search/suggest/?q=${encodeURIComponent(query)}`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'application/json',
                },
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const payload = await response.json();
            renderResults(payload, query);
        } catch (error) {
            console.warn('search: suggestion fetch failed', error);
            showEmpty(query);
        } finally {
            setLoading(false);
        }
    }

    const triggerSearch = debounce(requestSuggestions, DEBOUNCE_DELAY);

    input.addEventListener('input', () => {
        const query = input.value.trim();
        if (!query) {
            setLoading(false);
            clearResults();
            renderRecentSearches();
            return;
        }
        // Show loading only when user is typing
        setLoading(true);
        triggerSearch(query);
    });

    input.addEventListener('focus', () => {
        const query = input.value.trim();
        if (query.length < MIN_QUERY) {
            renderRecentSearches();
        }
    });

    input.addEventListener('keydown', event => {
        const key = event.key;
        switch (key) {
            case 'ArrowDown':
                event.preventDefault();
                updateSelection(selectedIndex + 1);
                break;
            case 'ArrowUp':
                event.preventDefault();
                updateSelection(selectedIndex - 1);
                break;
            case 'Enter':
                event.preventDefault();
                if (selectedIndex >= 0) {
                    selectResult(selectedIndex);
                } else {
                    const query = input.value.trim();
                    if (query) {
                        saveRecentSearch(query);
                        closeSearchModal();
                        window.location.href = `/search/?q=${encodeURIComponent(query)}`;
                    }
                }
                break;
            case 'Escape':
                closeSearchModal();
                break;
            default:
                break;
        }
    });

    clearRecentButton?.addEventListener('click', () => clearRecentSearches());

    suggestionButtons.forEach(button => {
        button.addEventListener('click', () => {
            const term = button.getAttribute('data-suggestion');
            if (!term) {
                return;
            }
            input.value = term;
            triggerSearch(term);
            input.focus();
        });
    });

    function resetModalState() {
        input.value = '';
        clearResults();
        clearEmpty();
        setLoading(false); // Hide loading indicator on reset
        renderRecentSearches();
    }

    window.addEventListener('openSearchModal', () => {
        resetModalState();
        window.setTimeout(() => input.focus({ preventScroll: true }), 60);
    });

    window.addEventListener('closeSearchModal', () => {
        clearResults();
    });

    window.searchAutocomplete = {
        showRecent: renderRecentSearches,
        reset: resetModalState,
    };

    renderRecentSearches();
})();
