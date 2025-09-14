/**
 * REDUCED MOTION MANAGER
 * Accessibility-focused animation management with user preferences
 */

class ReducedMotionManager {
  constructor() {
    this.isReducedMotion = false;
    this.userPreference = null;
    this.systemPreference = false;
    
    this.animationElements = new Map();
    this.observedElements = new Set();
    
    this.init();
  }
  
  init() {
    console.log('♿ Reduced Motion Manager initialized');
    
    // Detect system preference
    this.detectSystemPreference();
    
    // Check user override
    this.loadUserPreference();
    
    // Apply initial state
    this.updateMotionState();
    
    // Setup UI controls
    this.createMotionToggle();
    
    // Bind events
    this.bindEvents();
    
    // Monitor for changes
    this.startMonitoring();
  }
  
  detectSystemPreference() {
    if (window.matchMedia) {
      const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
      this.systemPreference = mediaQuery.matches;
      
      // Listen for system preference changes
      mediaQuery.addEventListener('change', (e) => {
        this.systemPreference = e.matches;
        
        // Only update if user hasn't overridden
        if (this.userPreference === null) {
          this.updateMotionState();
        }
      });
      
      console.log(`🔍 System prefers reduced motion: ${this.systemPreference}`);
    }
  }
  
  loadUserPreference() {
    const stored = localStorage.getItem('motion-preference');
    if (stored !== null) {
      this.userPreference = stored === 'reduced';
      console.log(`👤 User preference: ${this.userPreference ? 'reduced' : 'full'} motion`);
    }
  }
  
  updateMotionState() {
    // User preference overrides system preference
    this.isReducedMotion = this.userPreference !== null 
      ? this.userPreference 
      : this.systemPreference;
    
    // Apply to document
    if (this.isReducedMotion) {
      this.enableReducedMotion();
    } else {
      this.disableReducedMotion();
    }
    
    // Notify other systems
    this.notifyMotionChange();
  }
  
  enableReducedMotion() {
    console.log('🚫 Enabling reduced motion');
    
    // Add CSS class
    document.documentElement.classList.add('reduced-motion');
    document.body.classList.add('prefers-reduced-motion');
    
    // Disable problematic animations
    this.disableHeavyAnimations();
    
    // Convert animations to instant changes
    this.convertAnimationsToInstant();
    
    // Update toggle UI
    this.updateToggleUI(true);
  }
  
  disableReducedMotion() {
    console.log('✨ Enabling full motion');
    
    // Remove CSS classes
    document.documentElement.classList.remove('reduced-motion');
    document.body.classList.remove('prefers-reduced-motion');
    
    // Re-enable animations
    this.enableAnimations();
    
    // Update toggle UI
    this.updateToggleUI(false);
  }
  
  disableHeavyAnimations() {
    const heavySelectors = [
      '.animate-pulse-subtle',
      '.animate-breathe',
      '.loading-spinner',
      '.loading-dots',
      '[data-parallax]',
      '.parallax-layer'
    ];
    
    heavySelectors.forEach(selector => {
      const elements = document.querySelectorAll(selector);
      elements.forEach(element => {
        this.animationElements.set(element, {
          originalAnimation: element.style.animation || '',
          originalTransition: element.style.transition || '',
          originalTransform: element.style.transform || ''
        });
        
        // Stop animations
        element.style.animation = 'none';
        element.style.transition = 'none';
      });
    });
  }
  
  convertAnimationsToInstant() {
    // Convert entrance animations to instant reveals
    const entranceElements = document.querySelectorAll(`
      .animate-fade-in,
      .animate-fade-in-up,
      .animate-fade-in-down,
      .animate-fade-in-left,
      .animate-fade-in-right,
      .animate-scale-in,
      .animate-slide-up,
      .animate-slide-down,
      .scroll-reveal,
      .scroll-scale
    `);
    
    entranceElements.forEach(element => {
      element.style.opacity = '1';
      element.style.transform = 'none';
      element.classList.add('reduced-motion-instant');
    });
  }
  
  enableAnimations() {
    // Restore original animations
    this.animationElements.forEach((original, element) => {
      element.style.animation = original.originalAnimation;
      element.style.transition = original.originalTransition;
      element.style.transform = original.originalTransform;
    });
    
    this.animationElements.clear();
    
    // Remove instant reveal styles
    const instantElements = document.querySelectorAll('.reduced-motion-instant');
    instantElements.forEach(element => {
      element.style.opacity = '';
      element.style.transform = '';
      element.classList.remove('reduced-motion-instant');
    });
  }
  
  createMotionToggle() {
    // Create accessible toggle button
    const toggle = document.createElement('button');
    toggle.className = 'motion-toggle';
    toggle.setAttribute('aria-label', 'Toggle animation preferences');
    toggle.setAttribute('title', 'Toggle reduced motion');
    toggle.innerHTML = `
      <svg class="motion-icon" width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
        <path class="motion-on" d="M10 2L6 6h3v8h2V6h3l-4-4z" />
        <path class="motion-off" d="M2 2h16v2H2V2zm0 4h16v2H2V6zm0 4h16v2H2v-2zm0 4h16v2H2v-2z" style="display: none;" />
      </svg>
      <span class="motion-label">Animations</span>
    `;
    
    // Style the toggle
    const styles = `
      .motion-toggle {
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 1000;
        background: var(--bg-secondary, #1e293b);
        color: var(--text-primary, #f8fafc);
        border: 1px solid var(--border-color, #374151);
        border-radius: 8px;
        padding: 12px 16px;
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 14px;
        cursor: pointer;
        transition: all 0.2s ease;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
      }
      
      .motion-toggle:hover {
        background: var(--bg-tertiary, #334155);
        transform: translateY(-1px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
      }
      
      .motion-toggle:focus {
        outline: 2px solid var(--primary-500, #3b82f6);
        outline-offset: 2px;
      }
      
      .reduced-motion .motion-toggle {
        transition: none;
        transform: none !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1) !important;
      }
      
      .motion-icon {
        flex-shrink: 0;
      }
      
      .reduced-motion .motion-on {
        display: none;
      }
      
      .reduced-motion .motion-off {
        display: block !important;
      }
      
      @media (max-width: 768px) {
        .motion-toggle {
          bottom: 80px; /* Above mobile navigation */
        }
        
        .motion-label {
          display: none;
        }
      }
      
      @media print {
        .motion-toggle {
          display: none;
        }
      }
    `;
    
    // Inject styles
    const styleSheet = document.createElement('style');
    styleSheet.textContent = styles;
    document.head.appendChild(styleSheet);
    
    // Add click handler
    toggle.addEventListener('click', () => {
      this.toggleUserPreference();
    });
    
    // Add to document
    document.body.appendChild(toggle);
    
    this.toggleElement = toggle;
  }
  
  updateToggleUI(isReduced) {
    if (!this.toggleElement) return;
    
    const label = this.toggleElement.querySelector('.motion-label');
    if (label) {
      label.textContent = isReduced ? 'Reduced Motion' : 'Animations';
    }
    
    this.toggleElement.setAttribute(
      'aria-label', 
      `${isReduced ? 'Enable' : 'Disable'} animations`
    );
    
    this.toggleElement.setAttribute(
      'title',
      `${isReduced ? 'Enable' : 'Disable'} animations and motion effects`
    );
  }
  
  toggleUserPreference() {
    this.userPreference = !this.isReducedMotion;
    localStorage.setItem('motion-preference', this.userPreference ? 'reduced' : 'full');
    
    console.log(`👤 User toggled to: ${this.userPreference ? 'reduced' : 'full'} motion`);
    
    this.updateMotionState();
    
    // Show confirmation toast
    this.showToast(
      this.userPreference 
        ? 'Animations disabled for better accessibility' 
        : 'Animations enabled'
    );
  }
  
  showToast(message) {
    const toast = document.createElement('div');
    toast.className = 'motion-toast';
    toast.textContent = message;
    
    const toastStyles = `
      .motion-toast {
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 1001;
        background: var(--bg-secondary, #1e293b);
        color: var(--text-primary, #f8fafc);
        border: 1px solid var(--border-color, #374151);
        border-radius: 8px;
        padding: 12px 16px;
        font-size: 14px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        opacity: 0;
        transform: translateX(100%);
        transition: all 0.3s ease;
      }
      
      .motion-toast.show {
        opacity: 1;
        transform: translateX(0);
      }
      
      .reduced-motion .motion-toast {
        transition: none;
        opacity: 1 !important;
        transform: translateX(0) !important;
      }
    `;
    
    if (!document.querySelector('style[data-motion-toast]')) {
      const styleSheet = document.createElement('style');
      styleSheet.setAttribute('data-motion-toast', '');
      styleSheet.textContent = toastStyles;
      document.head.appendChild(styleSheet);
    }
    
    document.body.appendChild(toast);
    
    // Trigger show animation
    requestAnimationFrame(() => {
      toast.classList.add('show');
    });
    
    // Remove after 3 seconds
    setTimeout(() => {
      if (this.isReducedMotion) {
        toast.remove();
      } else {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => toast.remove(), 300);
      }
    }, 3000);
  }
  
  bindEvents() {
    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
      // Ctrl + Alt + M to toggle motion
      if (e.ctrlKey && e.altKey && e.key.toLowerCase() === 'm') {
        e.preventDefault();
        this.toggleUserPreference();
      }
    });
    
    // Listen for page visibility changes
    document.addEventListener('visibilitychange', () => {
      if (document.hidden && this.isReducedMotion) {
        // Pause any remaining animations when page is hidden
        this.pauseAllAnimations();
      }
    });
  }
  
  pauseAllAnimations() {
    const animatedElements = document.querySelectorAll('[class*="animate-"]');
    animatedElements.forEach(element => {
      element.style.animationPlayState = 'paused';
    });
  }
  
  startMonitoring() {
    // Monitor for new animated elements
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        mutation.addedNodes.forEach((node) => {
          if (node.nodeType === 1 && this.isReducedMotion) {
            this.processNewElement(node);
          }
        });
      });
    });
    
    observer.observe(document.body, {
      childList: true,
      subtree: true
    });
  }
  
  processNewElement(element) {
    // Apply reduced motion to new elements
    if (element.matches('[class*="animate-"]')) {
      element.style.animation = 'none';
      element.style.transition = 'none';
      element.style.opacity = '1';
      element.style.transform = 'none';
    }
    
    // Process child elements
    const animatedChildren = element.querySelectorAll('[class*="animate-"]');
    animatedChildren.forEach(child => {
      child.style.animation = 'none';
      child.style.transition = 'none';
      child.style.opacity = '1';
      child.style.transform = 'none';
    });
  }
  
  notifyMotionChange() {
    // Dispatch custom event for other systems
    document.dispatchEvent(new CustomEvent('motionpreference-change', {
      detail: {
        isReducedMotion: this.isReducedMotion,
        userPreference: this.userPreference,
        systemPreference: this.systemPreference
      }
    }));
  }
  
  // Public API
  getMotionPreference() {
    return {
      isReducedMotion: this.isReducedMotion,
      userPreference: this.userPreference,
      systemPreference: this.systemPreference
    };
  }
  
  setUserPreference(reduced) {
    this.userPreference = reduced;
    localStorage.setItem('motion-preference', reduced ? 'reduced' : 'full');
    this.updateMotionState();
  }
  
  resetToSystemDefault() {
    this.userPreference = null;
    localStorage.removeItem('motion-preference');
    this.updateMotionState();
    
    this.showToast('Reset to system default motion preference');
  }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  window.reducedMotionManager = new ReducedMotionManager();
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
  module.exports = ReducedMotionManager;
}

window.ReducedMotionManager = ReducedMotionManager;