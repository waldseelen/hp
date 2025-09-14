/**
 * Language Auto-Detection and UX Optimization
 * Automatically detects user's preferred language and improves language switching UX
 */

class LanguageAutoDetect {
    constructor() {
        this.supportedLanguages = ['tr', 'en'];
        this.defaultLanguage = 'en';
        this.currentLanguage = this.getCurrentLanguage();
        
        this.init();
    }

    /**
     * Initialize the language auto-detection system
     */
    init() {
        // Auto-detect language on first visit
        if (!this.hasLanguagePreference()) {
            this.autoDetectLanguage();
        }

        // Setup language switching UX
        this.setupLanguageSwitcher();
        
        // Setup page persistence for language changes
        this.setupPagePersistence();
        
        console.log('[Language] Auto-detection initialized');
    }

    /**
     * Auto-detect user's preferred language from browser settings
     */
    autoDetectLanguage() {
        // Get browser languages in order of preference
        const browserLanguages = navigator.languages || [navigator.language || navigator.userLanguage];
        
        // Find the first supported language
        for (const lang of browserLanguages) {
            const languageCode = lang.split('-')[0].toLowerCase();
            
            if (this.supportedLanguages.includes(languageCode)) {
                console.log(`[Language] Auto-detected: ${languageCode} from browser preferences`);
                this.setLanguagePreference(languageCode);
                
                // Only redirect if we're on a different language
                if (this.currentLanguage !== languageCode) {
                    this.switchToLanguage(languageCode, false); // No reload, just switch
                }
                return;
            }
        }
        
        // Fallback to default language
        console.log(`[Language] Using default language: ${this.defaultLanguage}`);
        this.setLanguagePreference(this.defaultLanguage);
    }

    /**
     * Setup enhanced language switcher UX
     * NOTE: Disabled to avoid conflict with language-manager.js
     */
    setupLanguageSwitcher() {
        // Language switching is handled by language-manager.js
        // This method is kept for future enhancements
        console.log('[Language Auto-detect] Language switching delegated to language-manager.js');
    }

    /**
     * Setup page persistence - keep user on same page when switching languages
     */
    setupPagePersistence() {
        // Store current page info for language switches
        this.currentPath = window.location.pathname;
        this.currentSearch = window.location.search;
        
        // Listen for language change events
        document.addEventListener('language-switched', (e) => {
            this.handleLanguageSwitch(e.detail);
        });
    }

    /**
     * Switch to a specific language with UX improvements
     */
    switchToLanguage(language, showFeedback = true) {
        if (!this.supportedLanguages.includes(language)) {
            console.warn(`[Language] Unsupported language: ${language}`);
            return;
        }

        // Store language preference
        this.setLanguagePreference(language);
        
        // Show loading feedback if requested
        if (showFeedback) {
            this.showLanguageSwitchFeedback(language);
        }

        // Build new URL preserving current page
        const newUrl = this.buildLanguageUrl(language);
        
        // Dispatch custom event
        const event = new CustomEvent('language-switched', {
            detail: { 
                from: this.currentLanguage, 
                to: language, 
                url: newUrl 
            }
        });
        document.dispatchEvent(event);
        
        // Navigate to new language version
        window.location.href = newUrl;
    }

    /**
     * Build URL for language switch while preserving current page
     */
    buildLanguageUrl(language) {
        const baseUrl = window.location.origin;
        let path = this.currentPath;
        let search = this.currentSearch;

        // Remove existing language parameter
        const searchParams = new URLSearchParams(search);
        searchParams.set('lang', language);
        
        // Build final URL
        const newSearch = searchParams.toString();
        return `${baseUrl}${path}${newSearch ? '?' + newSearch : ''}`;
    }

    /**
     * Show user feedback during language switch
     */
    showLanguageSwitchFeedback(language) {
        // Create or update language switch indicator
        let indicator = document.getElementById('language-switch-indicator');
        
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.id = 'language-switch-indicator';
            indicator.className = 'fixed top-4 right-4 bg-primary-600 text-white px-4 py-2 rounded-lg shadow-lg z-50 transition-all duration-300';
            document.body.appendChild(indicator);
        }

        const languageName = language === 'tr' ? 'Türkçe' : 'English';
        indicator.textContent = `${gettext ? gettext('Switching to') : 'Switching to'} ${languageName}...`;
        indicator.style.opacity = '1';
        indicator.style.transform = 'translateX(0)';

        // Hide after delay
        setTimeout(() => {
            if (indicator) {
                indicator.style.opacity = '0';
                indicator.style.transform = 'translateX(100%)';
            }
        }, 1500);
    }

    /**
     * Update language switcher visual state
     */
    updateLanguageSwitcherState() {
        const languageSwitchers = document.querySelectorAll('[data-language-switch]');
        
        languageSwitchers.forEach(switcher => {
            const switcherLanguage = switcher.getAttribute('data-language-switch');
            
            if (switcherLanguage === this.currentLanguage) {
                switcher.classList.add('active', 'font-semibold');
                switcher.setAttribute('aria-current', 'true');
            } else {
                switcher.classList.remove('active', 'font-semibold');
                switcher.removeAttribute('aria-current');
            }
        });
    }

    /**
     * Get current language from URL, localStorage, or default
     */
    getCurrentLanguage() {
        // Check URL parameter first
        const urlParams = new URLSearchParams(window.location.search);
        const urlLang = urlParams.get('lang');
        
        if (urlLang && this.supportedLanguages.includes(urlLang)) {
            return urlLang;
        }

        // Check HTML lang attribute
        const htmlLang = document.documentElement.lang;
        if (htmlLang && this.supportedLanguages.includes(htmlLang.split('-')[0])) {
            return htmlLang.split('-')[0];
        }

        // Check localStorage
        const storedLang = localStorage.getItem('preferred-language');
        if (storedLang && this.supportedLanguages.includes(storedLang)) {
            return storedLang;
        }

        return this.defaultLanguage;
    }

    /**
     * Check if user has a language preference set
     */
    hasLanguagePreference() {
        const urlParams = new URLSearchParams(window.location.search);
        const urlLang = urlParams.get('lang');
        const storedLang = localStorage.getItem('preferred-language');
        
        return !!(urlLang || storedLang);
    }

    /**
     * Store language preference
     */
    setLanguagePreference(language) {
        localStorage.setItem('preferred-language', language);
        
        // Update HTML lang attribute
        document.documentElement.lang = language;
        
        this.currentLanguage = language;
    }

    /**
     * Handle language switch event
     */
    handleLanguageSwitch(detail) {
        console.log(`[Language] Switching from ${detail.from} to ${detail.to}`);
        
        // Update analytics if available
        if (window.gtag) {
            gtag('event', 'language_switch', {
                'from_language': detail.from,
                'to_language': detail.to
            });
        }
        
        // Update any language-dependent content immediately
        this.updateLanguageDependentContent(detail.to);
    }

    /**
     * Update content that depends on language immediately (before page reload)
     */
    updateLanguageDependentContent(language) {
        // Update direction if needed (for RTL languages in future)
        document.documentElement.dir = 'ltr'; // Default for tr and en
        
        // Update any immediate UI elements
        const currentLangElements = document.querySelectorAll('[data-current-language]');
        currentLangElements.forEach(element => {
            element.textContent = language === 'tr' ? 'Türkçe' : 'English';
        });
    }

    /**
     * Get user's language preference
     */
    getLanguagePreference() {
        return {
            current: this.currentLanguage,
            stored: localStorage.getItem('preferred-language'),
            browser: navigator.language,
            supported: this.supportedLanguages
        };
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.languageAutoDetect = new LanguageAutoDetect();
});

// Export for global access
window.LanguageAutoDetect = LanguageAutoDetect;