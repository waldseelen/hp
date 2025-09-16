/**
 * JavaScript Internationalization System
 * Provides gettext-like functionality for client-side translations
 */

// Translation cache
let translationCache = {};
let currentLanguage = 'en';
let fallbackLanguage = 'en';

/**
 * Initialize the i18n system
 * @param {string} language - Current language code
 * @param {Object} translations - Translation object
 */
function initI18n(language = 'en', translations = {}) {
    currentLanguage = language;
    translationCache = translations;
    
    // Detect language from HTML lang attribute if not provided
    if (!language) {
        const htmlLang = document.documentElement.lang || 'en';
        currentLanguage = htmlLang.split('-')[0]; // Take just the language part
    }
    
    console.log(`[i18n] Initialized with language: ${currentLanguage}`);
}

/**
 * Get translated string (main translation function)
 * @param {string} text - Text to translate
 * @param {Object} params - Parameters for string interpolation
 * @returns {string} Translated text
 */
function gettext(text, params = {}) {
    // Get translation from cache
    const translation = getTranslation(text);
    
    // Perform parameter substitution
    return interpolateString(translation, params);
}

/**
 * Alias for gettext (shorter syntax)
 */
const _ = gettext;

/**
 * Pluralization support
 * @param {string} singular - Singular form
 * @param {string} plural - Plural form  
 * @param {number} count - Number to determine plural form
 * @param {Object} params - Parameters for string interpolation
 * @returns {string} Translated text in appropriate plural form
 */
function ngettext(singular, plural, count, params = {}) {
    const text = count === 1 ? singular : plural;
    const translation = getTranslation(text);
    
    // Add count to parameters
    const allParams = { ...params, count };
    return interpolateString(translation, allParams);
}

/**
 * Get translation from cache with fallback
 * @param {string} text - Text to translate
 * @returns {string} Translated text or original text if not found
 */
function getTranslation(text) {
    // Try current language
    if (translationCache[currentLanguage] && translationCache[currentLanguage][text]) {
        return translationCache[currentLanguage][text];
    }
    
    // Try fallback language
    if (currentLanguage !== fallbackLanguage && 
        translationCache[fallbackLanguage] && 
        translationCache[fallbackLanguage][text]) {
        return translationCache[fallbackLanguage][text];
    }
    
    // Return original text if no translation found
    return text;
}

/**
 * String interpolation for parameters
 * @param {string} text - Text with placeholders
 * @param {Object} params - Parameters to substitute
 * @returns {string} Text with parameters substituted
 */
function interpolateString(text, params) {
    return text.replace(/\{(\w+)\}/g, (match, key) => {
        return params.hasOwnProperty(key) ? params[key] : match;
    });
}

/**
 * Load translations from server
 * @param {string} language - Language code to load
 * @returns {Promise} Promise that resolves when translations are loaded
 */
async function loadTranslations(language) {
    try {
        const response = await fetch(`/static/js/translations/${language}.json`);
        if (!response.ok) {
            throw new Error(`Failed to load translations for ${language}`);
        }
        
        const translations = await response.json();
        
        // Merge with existing cache
        if (!translationCache[language]) {
            translationCache[language] = {};
        }
        Object.assign(translationCache[language], translations);
        
        console.log(`[i18n] Loaded translations for ${language}`);
        return translations;
    } catch (error) {
        console.warn(`[i18n] Failed to load translations for ${language}:`, error);
        return {};
    }
}

/**
 * Change current language and reload translations
 * @param {string} language - New language code
 * @returns {Promise} Promise that resolves when language is changed
 */
async function changeLanguage(language) {
    currentLanguage = language;
    
    // Load translations if not cached
    if (!translationCache[language]) {
        await loadTranslations(language);
    }
    
    // Dispatch language change event
    const event = new CustomEvent('language-changed', {
        detail: { language, translations: translationCache[language] }
    });
    document.dispatchEvent(event);
    
    console.log(`[i18n] Language changed to: ${language}`);
}

/**
 * Get current language
 * @returns {string} Current language code
 */
function getCurrentLanguage() {
    return currentLanguage;
}

/**
 * Check if text has translation
 * @param {string} text - Text to check
 * @returns {boolean} True if translation exists
 */
function hasTranslation(text) {
    return !!(translationCache[currentLanguage] && translationCache[currentLanguage][text]);
}

/**
 * Mark text for translation (no-op function for extraction tools)
 * @param {string} text - Text to mark
 * @returns {string} Original text
 */
function gettext_noop(text) {
    return text;
}

// Aliases
const N_ = gettext_noop;
const lazy_gettext = gettext_noop;

// DOM content loaded initialization
document.addEventListener('DOMContentLoaded', () => {
    // Auto-initialize with HTML lang attribute
    const htmlLang = document.documentElement.lang || 'en';
    const language = htmlLang.split('-')[0];
    
    // Try to get embedded translations from the page
    const translationScript = document.querySelector('script[type="application/json"][data-translations]');
    let translations = {};
    
    if (translationScript) {
        try {
            translations = JSON.parse(translationScript.textContent);
        } catch (error) {
            console.warn('[i18n] Failed to parse embedded translations:', error);
        }
    }
    
    initI18n(language, translations);
    
    // Load additional translations if needed
    if (!translations[language]) {
        loadTranslations(language).catch(() => {
            // Fallback - continue without translations
        });
    }
});

// Export functions for global use
window.gettext = gettext;
window._ = _;
window.ngettext = ngettext;
window.gettext_noop = gettext_noop;
window.N_ = N_;
window.lazy_gettext = lazy_gettext;
window.i18n = {
    init: initI18n,
    gettext,
    ngettext,
    changeLanguage,
    getCurrentLanguage,
    loadTranslations,
    hasTranslation,
    _,
    N_
};

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        gettext,
        ngettext,
        gettext_noop,
        initI18n,
        changeLanguage,
        getCurrentLanguage,
        loadTranslations,
        hasTranslation,
        _,
        N_
    };
}