(function () {
  const doc = document;
  const NAV_SCROLL_THRESHOLD = 32;
  const NAV_HIDE_THRESHOLD = 160;

  let searchModal = null;
  let searchModalInput = null;
  let previouslyFocused = null;

  function initSearchTrigger() {
    const trigger = doc.querySelector('[data-search-trigger]');
    if (!trigger) {
      return;
    }

    trigger.addEventListener('click', (event) => {
      event.preventDefault();
      openSearchModal();
    });
  }

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
      elements.forEach((el) => el.classList.add('is-visible'));
      return;
    }

    const observer = new IntersectionObserver((entries, obs) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          obs.unobserve(entry.target);
        }
      });
    }, {
      rootMargin: '0px 0px -10% 0px',
      threshold: 0.15,
    });

    elements.forEach((el) => observer.observe(el));
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

    const starCount = prefersReducedMotion ? 40 : 140;
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
        stars.forEach((star) => {
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

    const scheduleUpdate = (event) => {
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
    const dismissors = searchModal.querySelectorAll('[data-search-dismiss]');

    dismissors.forEach((element) => {
      element.addEventListener('click', () => {
        closeSearchModal();
      });
    });

    searchModal.addEventListener('mousedown', (event) => {
      if (event.target === searchModal) {
        closeSearchModal();
      }
    });

    doc.addEventListener('keydown', (event) => {
      const key = event.key.toLowerCase();
      if ((event.ctrlKey || event.metaKey) && key === 'k') {
        event.preventDefault();
        openSearchModal();
      }

      if (key === 'escape' && searchModal.classList.contains('is-visible')) {
        closeSearchModal();
      }
    });

    const suggestions = searchModal.querySelectorAll('[data-suggestion]');
    suggestions.forEach((button) => {
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
    requestAnimationFrame(() => {
      searchModal.classList.add('is-visible');
      searchModalInput?.focus({ preventScroll: true });
    });
  }

  function closeSearchModal() {
    if (!searchModal) {
      return;
    }

    searchModal.classList.remove('is-visible');
    searchModalInput?.blur();
    window.dispatchEvent(new CustomEvent('closeSearchModal'));
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
    initSearchTrigger();
    initNavigation();
    initRevealAnimations();
    initStarfield();
    initSearchModal();
  });
})();
