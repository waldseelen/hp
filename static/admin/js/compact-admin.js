(function () {
    'use strict';

    const storageKey = 'adminSidebarCollapsed';
    const docEl = document.documentElement;
    const sidebar = document.getElementById('nav-sidebar');
    const toggle = document.querySelector('[data-admin-toggle="sidebar"]');
    const prefersCompactWidth = () => window.innerWidth <= 1024;

    const storage = {
        get() {
            try {
                return window.localStorage.getItem(storageKey);
            } catch (error) {
                console.warn('Admin sidebar preference unavailable:', error);
                return null;
            }
        },
        set(value) {
            try {
                window.localStorage.setItem(storageKey, value);
            } catch (error) {
                console.warn('Admin sidebar preference could not be saved:', error);
            }
        }
    };

    const setCollapsedState = (collapsed, persist = true) => {
        if (!sidebar) {
            return;
        }

        sidebar.classList.toggle('collapsed', collapsed);
        docEl.classList.toggle('admin-sidebar-collapsed', collapsed);
        toggle?.setAttribute('aria-expanded', (!collapsed).toString());

        if (persist) {
            storage.set(collapsed ? '1' : '0');
        }
    };

    const applyPreferredState = () => {
        const stored = storage.get();
        if (stored === '1' || stored === '0') {
            setCollapsedState(stored === '1', false);
            return;
        }

        setCollapsedState(prefersCompactWidth(), false);
    };

    const debounce = (fn, wait) => {
        let timer = null;
        return (...args) => {
            window.clearTimeout(timer);
            timer = window.setTimeout(() => fn.apply(null, args), wait);
        };
    };

    const handleResize = debounce(() => {
        const stored = storage.get();
        if (stored === '1' || stored === '0') {
            setCollapsedState(stored === '1', false);
            return;
        }

        setCollapsedState(prefersCompactWidth(), false);
    }, 120);

    const enhanceDocument = () => {
        docEl.classList.add('admin-enhanced');
        if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
            docEl.classList.add('admin-reduced-motion');
        }
    };

    const bindToggle = () => {
        if (!toggle) {
            return;
        }

        toggle.addEventListener('click', () => {
            const willCollapse = !docEl.classList.contains('admin-sidebar-collapsed');
            setCollapsedState(willCollapse);
        });
    };

    const bindKeyboardShortcut = () => {
        document.addEventListener('keydown', (event) => {
            if (!(event.metaKey || event.ctrlKey)) {
                return;
            }

            if (event.key.toLowerCase() !== 'b') {
                return;
            }

            event.preventDefault();
            const willCollapse = !docEl.classList.contains('admin-sidebar-collapsed');
            setCollapsedState(willCollapse);
        });
    };

    const init = () => {
        if (!sidebar) {
            return;
        }

        enhanceDocument();
        applyPreferredState();
        bindToggle();
        bindKeyboardShortcut();
        window.addEventListener('resize', handleResize);
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
