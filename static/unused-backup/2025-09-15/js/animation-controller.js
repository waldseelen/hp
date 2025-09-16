/**
 * ANIMATION CONTROLLER
 * Intersection Observer based animations with performance optimization
 */

class AnimationController {
  constructor(options = {}) {
    this.options = {
      threshold: 0.1,
      rootMargin: '50px 0px',
      animateOnce: true,
      enableParallax: true,
      respectReducedMotion: true,
      ...options
    };
    
    this.observers = [];
    this.animatedElements = new Set();
    this.parallaxElements = [];
    this.reducedMotion = false;
    
    this.init();
  }
  
  init() {
    console.log('🎬 Animation Controller initialized');
    
    // Check for reduced motion preference
    this.checkReducedMotion();
    
    // Initialize intersection observers
    this.initScrollAnimations();
    this.initParallaxAnimations();
    this.initStaggerAnimations();
    
    // Bind events
    this.bindEvents();
    
    // Performance monitoring
    this.initPerformanceMonitoring();
  }
  
  checkReducedMotion() {
    if (window.matchMedia) {
      const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
      this.reducedMotion = mediaQuery.matches;
      
      // Listen for changes
      mediaQuery.addEventListener('change', (e) => {
        this.reducedMotion = e.matches;
        this.updateAnimationsForReducedMotion();
      });
    }
    
    // Also check localStorage override
    if (localStorage.getItem('reduced-motion') === 'true') {
      this.reducedMotion = true;
    }
  }
  
  updateAnimationsForReducedMotion() {
    if (this.reducedMotion) {
      document.body.classList.add('reduced-motion');
      this.disableHeavyAnimations();
    } else {
      document.body.classList.remove('reduced-motion');
      this.enableAnimations();
    }
  }
  
  initScrollAnimations() {
    // Scroll reveal animations
    const scrollRevealObserver = new IntersectionObserver(
      (entries) => this.handleScrollReveal(entries),
      {
        threshold: this.options.threshold,
        rootMargin: this.options.rootMargin
      }
    );
    
    // Observe elements with scroll animation classes
    const scrollElements = document.querySelectorAll(`
      .scroll-reveal,
      .scroll-scale,
      .animate-fade-in,
      .animate-fade-in-up,
      .animate-fade-in-down,
      .animate-fade-in-left,
      .animate-fade-in-right,
      .animate-scale-in,
      .animate-slide-up,
      .animate-slide-down,
      .animate-bounce-in
    `);
    
    scrollElements.forEach(element => {
      // Add initial hidden state
      if (!element.classList.contains('revealed')) {
        element.style.animationPlayState = 'paused';
      }
      
      scrollRevealObserver.observe(element);
    });
    
    this.observers.push(scrollRevealObserver);
  }
  
  handleScrollReveal(entries) {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const element = entry.target;
        
        // Prevent re-animation if animateOnce is enabled
        if (this.options.animateOnce && this.animatedElements.has(element)) {
          return;
        }
        
        // Trigger animation
        this.triggerAnimation(element);
        this.animatedElements.add(element);
        
        // Unobserve if animateOnce is enabled
        if (this.options.animateOnce) {
          entry.target.removeAttribute('data-animate-on-scroll');
        }
      }
    });
  }
  
  triggerAnimation(element) {
    // Don't animate if reduced motion is preferred
    if (this.reducedMotion && this.options.respectReducedMotion) {
      element.classList.add('revealed');
      return;
    }
    
    // Add revealed class for CSS animations
    element.classList.add('revealed');
    
    // Start CSS animation if paused
    if (element.style.animationPlayState === 'paused') {
      element.style.animationPlayState = 'running';
    }
    
    // Add will-change for performance
    element.classList.add('will-animate');
    
    // Clean up will-change after animation
    const animationDuration = this.getAnimationDuration(element);
    setTimeout(() => {
      element.classList.remove('will-animate');
      element.classList.add('will-animate-complete');
    }, animationDuration);
    
    // Trigger custom event
    element.dispatchEvent(new CustomEvent('animation-start', {
      detail: { element, timestamp: performance.now() }
    }));
  }
  
  initStaggerAnimations() {
    const staggerContainers = document.querySelectorAll('.animate-stagger');
    
    staggerContainers.forEach(container => {
      const children = container.children;
      const observer = new IntersectionObserver(
        (entries) => {
          entries.forEach(entry => {
            if (entry.isIntersecting) {
              this.triggerStaggerAnimation(container);
              observer.unobserve(entry.target);
            }
          });
        },
        {
          threshold: 0.2,
          rootMargin: '0px 0px -50px 0px'
        }
      );
      
      observer.observe(container);
      this.observers.push(observer);
    });
  }
  
  triggerStaggerAnimation(container) {
    const children = Array.from(container.children);
    const staggerDelay = 100; // ms between each item
    
    children.forEach((child, index) => {
      setTimeout(() => {
        if (!this.reducedMotion) {
          child.classList.add('revealed');
          child.style.animationPlayState = 'running';
        } else {
          // Instant reveal for reduced motion
          child.style.opacity = '1';
          child.style.transform = 'none';
        }
      }, index * staggerDelay);
    });
  }
  
  initParallaxAnimations() {
    if (!this.options.enableParallax || this.reducedMotion) {
      return;
    }
    
    // Find parallax elements
    this.parallaxElements = Array.from(document.querySelectorAll('[data-parallax]'));
    
    if (this.parallaxElements.length === 0) return;
    
    // Throttled scroll handler for performance
    let ticking = false;
    const updateParallax = () => {
      if (!ticking) {
        requestAnimationFrame(() => {
          this.updateParallaxElements();
          ticking = false;
        });
        ticking = true;
      }
    };
    
    // Use passive event listener for better performance
    window.addEventListener('scroll', updateParallax, { passive: true });
  }
  
  updateParallaxElements() {
    const scrollTop = window.pageYOffset;
    const windowHeight = window.innerHeight;
    
    this.parallaxElements.forEach(element => {
      const rect = element.getBoundingClientRect();
      const elementTop = rect.top + scrollTop;
      const elementHeight = rect.height;
      
      // Only update if element is in viewport
      if (rect.bottom >= 0 && rect.top <= windowHeight) {
        const speed = parseFloat(element.dataset.parallax) || 0.5;
        const yPos = -(scrollTop - elementTop) * speed;
        
        // Use transform3d for better performance
        element.style.transform = `translate3d(0, ${yPos}px, 0)`;
      }
    });
  }
  
  initPerformanceMonitoring() {
    // Monitor animation performance
    let animationFrameCount = 0;
    let lastTime = performance.now();
    
    const monitorAnimations = () => {
      const currentTime = performance.now();
      const deltaTime = currentTime - lastTime;
      
      animationFrameCount++;
      
      // Check FPS every second
      if (animationFrameCount >= 60) {
        const fps = Math.round(1000 / (deltaTime / animationFrameCount));
        
        // Reduce animation quality if FPS drops
        if (fps < 50) {
          this.reduceAnimationQuality();
        } else if (fps > 55) {
          this.restoreAnimationQuality();
        }
        
        animationFrameCount = 0;
        lastTime = currentTime;
      }
      
      requestAnimationFrame(monitorAnimations);
    };
    
    // Start monitoring only in development
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
      requestAnimationFrame(monitorAnimations);
    }
  }
  
  reduceAnimationQuality() {
    console.warn('🎬 Reducing animation quality due to low FPS');
    document.body.classList.add('low-performance');
    
    // Disable heavy animations
    this.disableHeavyAnimations();
  }
  
  restoreAnimationQuality() {
    if (document.body.classList.contains('low-performance')) {
      console.log('🎬 Restoring animation quality');
      document.body.classList.remove('low-performance');
      
      if (!this.reducedMotion) {
        this.enableAnimations();
      }
    }
  }
  
  disableHeavyAnimations() {
    const heavyAnimations = document.querySelectorAll(`
      .animate-pulse-subtle,
      .animate-breathe,
      .parallax-layer,
      [data-parallax]
    `);
    
    heavyAnimations.forEach(element => {
      element.style.animation = 'none';
      element.style.transform = 'none';
    });
  }
  
  enableAnimations() {
    const heavyAnimations = document.querySelectorAll(`
      .animate-pulse-subtle,
      .animate-breathe,
      .parallax-layer,
      [data-parallax]
    `);
    
    heavyAnimations.forEach(element => {
      element.style.animation = '';
      element.style.transform = '';
    });
  }
  
  getAnimationDuration(element) {
    const computedStyle = getComputedStyle(element);
    const duration = computedStyle.animationDuration;
    
    if (duration === '0s') return 300; // Default fallback
    
    return parseFloat(duration) * 1000; // Convert to ms
  }
  
  bindEvents() {
    // Handle visibility change to pause/resume animations
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) {
        this.pauseAnimations();
      } else {
        this.resumeAnimations();
      }
    });
    
    // Handle page unload
    window.addEventListener('beforeunload', () => {
      this.cleanup();
    });
    
    // Handle reduced motion toggle
    document.addEventListener('keydown', (e) => {
      // Toggle reduced motion with Ctrl+Alt+M
      if (e.ctrlKey && e.altKey && e.key === 'm') {
        this.toggleReducedMotion();
      }
    });
  }
  
  pauseAnimations() {
    const animatedElements = document.querySelectorAll('[class*="animate-"]');
    animatedElements.forEach(element => {
      element.style.animationPlayState = 'paused';
    });
  }
  
  resumeAnimations() {
    if (!this.reducedMotion) {
      const animatedElements = document.querySelectorAll('[class*="animate-"]');
      animatedElements.forEach(element => {
        element.style.animationPlayState = 'running';
      });
    }
  }
  
  toggleReducedMotion() {
    this.reducedMotion = !this.reducedMotion;
    localStorage.setItem('reduced-motion', this.reducedMotion.toString());
    this.updateAnimationsForReducedMotion();
    
    console.log(`🎬 Reduced motion ${this.reducedMotion ? 'enabled' : 'disabled'}`);
  }
  
  // Public API methods
  animateElement(element, animationClass, options = {}) {
    const {
      delay = 0,
      duration = null,
      callback = null
    } = options;
    
    setTimeout(() => {
      if (duration) {
        element.style.animationDuration = `${duration}ms`;
      }
      
      element.classList.add(animationClass);
      
      if (callback) {
        const animationDuration = duration || this.getAnimationDuration(element);
        setTimeout(callback, animationDuration);
      }
    }, delay);
  }
  
  createStaggeredAnimation(elements, animationClass, staggerDelay = 100) {
    elements.forEach((element, index) => {
      this.animateElement(element, animationClass, {
        delay: index * staggerDelay
      });
    });
  }
  
  cleanup() {
    // Disconnect all observers
    this.observers.forEach(observer => observer.disconnect());
    this.observers = [];
    
    // Clear performance monitoring
    this.animatedElements.clear();
    this.parallaxElements = [];
  }
  
  // Utility methods
  static isElementInViewport(element, threshold = 0) {
    const rect = element.getBoundingClientRect();
    const windowHeight = window.innerHeight;
    const windowWidth = window.innerWidth;
    
    return (
      rect.top >= -threshold &&
      rect.left >= -threshold &&
      rect.bottom <= windowHeight + threshold &&
      rect.right <= windowWidth + threshold
    );
  }
  
  static waitForAnimation(element) {
    return new Promise(resolve => {
      const handleAnimationEnd = () => {
        element.removeEventListener('animationend', handleAnimationEnd);
        resolve();
      };
      
      element.addEventListener('animationend', handleAnimationEnd);
    });
  }
}

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  window.animationController = new AnimationController();
  
  // Add global CSS class for JavaScript availability
  document.documentElement.classList.add('js-animations-available');
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
  module.exports = AnimationController;
}

// Export class globally
window.AnimationController = AnimationController;