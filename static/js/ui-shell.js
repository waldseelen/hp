(function () {
    const doc = document;
    const NAV_SCROLL_THRESHOLD = 32;
    const NAV_HIDE_THRESHOLD = 160;

    let searchModal = null;
    let searchModalInput = null;
    let previouslyFocused = null;

    function initNavigation() {
        const nav = doc.querySelector('[data-nav-shell]');
        if (!nav) {
            return;
        }

        let lastY = window.scrollY;

        const handleScroll = () => {
            const currentY = window.scrollY;

            if (currentY > NAV_SCROLL_THRESHOLD) {
                nav.classList.add('is-scrolled');
            } else {
                nav.classList.remove('is-scrolled');
            }

            if (currentY > NAV_HIDE_THRESHOLD && currentY > lastY) {
                nav.classList.add('is-hidden');
            } else {
                nav.classList.remove('is-hidden');
            }

            lastY = currentY;
        };

        window.addEventListener('scroll', handleScroll, { passive: true });
        handleScroll();
    }

    function initRevealAnimations() {
        const elements = doc.querySelectorAll('[data-animate], [data-animate-card], .scroll-reveal, .scroll-reveal-left, .scroll-reveal-right');
        if (!elements.length || !('IntersectionObserver' in window)) {
            elements.forEach(el => el.classList.add('is-visible'));
            return;
        }

        const observer = new IntersectionObserver((entries, obs) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('is-visible');
                    obs.unobserve(entry.target);
                }
            });
        }, {
            rootMargin: '0px 0px -10% 0px',
            threshold: 0.15,
        });

        elements.forEach(el => observer.observe(el));
    }

    function initStarfield() {
        const body = doc.getElementById('app-body');
        const cursor = doc.querySelector('.cursor-blackhole');
        const starContainer = body ? body.querySelector('.starfield-layer') : null;
        const prefersReducedMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        const prefersCoarsePointer = window.matchMedia && window.matchMedia('(pointer: coarse)').matches;

        if (!body || !starContainer || !cursor || prefersCoarsePointer) {
            return;
        }

        const starCount = prefersReducedMotion ? 24 : 80;
        const stars = [];

        for (let i = 0; i < starCount; i += 1) {
            const star = doc.createElement('span');
            star.className = 'star';
            star.style.left = `${Math.random() * 100}%`;
            star.style.top = `${Math.random() * 100}%`;
            star.style.opacity = (0.4 + Math.random() * 0.55).toFixed(2);
            starContainer.appendChild(star);
            stars.push(star);
        }

        let latestPointerEvent = null;
        let rafId = null;

        const update = () => {
            if (!latestPointerEvent) {
                rafId = null;
                return;
            }

            const { clientX, clientY } = latestPointerEvent;
            cursor.style.opacity = '1';
            cursor.style.transform = `translate(${clientX}px, ${clientY}px) scale(1)`;

            if (!prefersReducedMotion) {
                stars.forEach(star => {
                    const rect = star.getBoundingClientRect();
                    const starX = rect.left + rect.width / 2;
                    const starY = rect.top + rect.height / 2;
                    const distX = (clientX - starX) * 0.09;
                    const distY = (clientY - starY) * 0.09;
                    star.style.transform = `translate(${distX}px, ${distY}px)`;
                    const opacity = Math.max(0.18, 1 - (Math.abs(distX) + Math.abs(distY)) / 90);
                    star.style.opacity = opacity.toFixed(2);
                });
            }

            rafId = null;
        };

        const scheduleUpdate = event => {
            latestPointerEvent = event;
            if (rafId === null) {
                rafId = window.requestAnimationFrame(update);
            }
        };

        doc.addEventListener('pointermove', scheduleUpdate, { passive: true });
        doc.addEventListener('pointerleave', () => {
            latestPointerEvent = null;
            cursor.style.opacity = '0';
        });
    }

    function initSearchModal() {
        searchModal = doc.getElementById('search-modal');
        if (!searchModal) {
            return;
        }

        searchModalInput = searchModal.querySelector('.search-modal__input');

        searchModal.addEventListener('mousedown', event => {
            if (event.target === searchModal) {
                closeSearchModal();
            }
        });

        doc.addEventListener('keydown', event => {
            const key = event.key.toLowerCase();
            if ((event.ctrlKey || event.metaKey) && key === 'k') {
                const active = doc.activeElement;
                const isEditable = active && (active.tagName === 'INPUT' || active.tagName === 'TEXTAREA' || active.isContentEditable);
                if (isEditable) {
                    return;
                }

                event.preventDefault();
                window.dispatchEvent(new CustomEvent('open-search'));
            }

            if (key === 'escape' && searchModal.classList.contains('is-visible')) {
                window.dispatchEvent(new CustomEvent('close-search'));
            }
        });

        const suggestions = searchModal.querySelectorAll('[data-suggestion]');
        suggestions.forEach(button => {
            button.addEventListener('click', () => {
                if (!searchModalInput) {
                    return;
                }
                searchModalInput.value = button.getAttribute('data-suggestion');
                searchModalInput.dispatchEvent(new Event('input'));
                searchModalInput.focus();
            });
        });
    }

    function openSearchModal() {
        if (!searchModal) {
            return;
        }

        previouslyFocused = doc.activeElement;
        window.searchAutocomplete?.reset();
        window.dispatchEvent(new CustomEvent('openSearchModal'));
        searchModal.removeAttribute('hidden');
        searchModal.setAttribute('aria-hidden', 'false');
        requestAnimationFrame(() => {
            searchModal.classList.add('is-visible');
            searchModalInput?.focus({ preventScroll: true });
        });
    }

    function initScrollProgress() {
        const progressBar = doc.querySelector('[data-scroll-progress]');
        if (!progressBar) {
            return;
        }

        const update = () => {
            const scrollTop = window.pageYOffset || doc.documentElement.scrollTop || 0;
            const documentHeight = doc.documentElement.scrollHeight - window.innerHeight;
            const progress = documentHeight > 0 ? (scrollTop / documentHeight) * 100 : 0;
            progressBar.style.width = `${progress}%`;
            progressBar.setAttribute('aria-valuenow', progress.toFixed(0));
            progressBar.setAttribute('aria-valuetext', `${Math.round(progress)}%`);
        };

        const schedule = () => window.requestAnimationFrame(update);

        window.addEventListener('scroll', schedule, { passive: true });
        window.addEventListener('resize', schedule);
        update();
    }

    function initBackToTop() {
        const backToTopBtn = doc.getElementById('back-to-top');
        if (!backToTopBtn) {
            return;
        }

        const toggleVisibility = () => {
            const shouldShow = window.pageYOffset > 400;
            backToTopBtn.classList.toggle('is-visible', shouldShow);
            backToTopBtn.setAttribute('aria-hidden', (!shouldShow).toString());
            backToTopBtn.setAttribute('tabindex', shouldShow ? '0' : '-1');
        };

        backToTopBtn.addEventListener('click', () => {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });

        const schedule = () => window.requestAnimationFrame(toggleVisibility);

        window.addEventListener('scroll', schedule, { passive: true });
        toggleVisibility();
    }

    function closeSearchModal() {
        if (!searchModal) {
            return;
        }

        searchModal.classList.remove('is-visible');
        searchModalInput?.blur();
        window.dispatchEvent(new CustomEvent('closeSearchModal'));
        searchModal.setAttribute('aria-hidden', 'true');
        window.setTimeout(() => {
            if (!searchModal.classList.contains('is-visible')) {
                searchModal.setAttribute('hidden', '');
            }
        }, 200);

        if (previouslyFocused && typeof previouslyFocused.focus === 'function') {
            previouslyFocused.focus({ preventScroll: true });
        }
    }

    window.openSearchModal = openSearchModal;
    window.closeSearchModal = closeSearchModal;

    document.addEventListener('DOMContentLoaded', () => {
        if (doc.body) {
            doc.body.classList.add('reveal-ready');
        }

        initNavigation();
        window.requestAnimationFrame(() => {
            initRevealAnimations();
        });
        const deferStarfield = () => window.requestAnimationFrame(initStarfield);
        if ('requestIdleCallback' in window) {
            requestIdleCallback(deferStarfield, { timeout: 1200 });
        } else {
            setTimeout(deferStarfield, 120);
        }
        initSearchModal();
        initScrollProgress();
        initBackToTop();
    });

    window.addEventListener('open-search', openSearchModal);
    window.addEventListener('close-search', closeSearchModal);
})();
