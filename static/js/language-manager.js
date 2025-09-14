/**
 * LANGUAGE MANAGER - Dil Değiştirme Sistemi
 * ==========================================
 * 
 * Theme Manager'a benzer şekilde dil tercihlerini yönetir.
 * Kullanıcının dil seçimini localStorage'da saklar ve 
 * sayfa yenilendiğinde korur.
 * 
 * Özellikler:
 * - TR/EN toggle sistemi
 * - localStorage ile kalıcı saklama
 * - Sistem dili algılama
 * - Smooth geçişler
 * - Django i18n entegrasyonu
 */

class LanguageManager {
    constructor() {
        this.currentLanguage = this.getStoredLanguage() || this.detectSystemLanguage() || 'tr';
        this.init();
    }

    init() {
        this.applyLanguage(this.currentLanguage);
        this.bindEvents();
        this.updateToggleButtons();
        console.log('LanguageManager initialized with language:', this.currentLanguage);
    }

    /**
     * Depolanan dil tercihini al
     */
    getStoredLanguage() {
        return localStorage.getItem('portfolio-language');
    }

    /**
     * Sistem dilini algıla
     */
    detectSystemLanguage() {
        const browserLang = navigator.language.toLowerCase();
        if (browserLang.startsWith('tr')) {
            return 'tr';
        } else if (browserLang.startsWith('en')) {
            return 'en';
        }
        return 'tr'; // Varsayılan olarak Türkçe
    }

    /**
     * Dili değiştir
     */
    toggleLanguage() {
        const newLanguage = this.currentLanguage === 'tr' ? 'en' : 'tr';
        this.setLanguage(newLanguage);
    }

    /**
     * Belirli bir dil ayarla
     */
    setLanguage(language) {
        if (!['tr', 'en'].includes(language)) {
            console.warn('Unsupported language:', language);
            return;
        }

        this.currentLanguage = language;
        localStorage.setItem('portfolio-language', language);
        this.applyLanguage(language);
        this.updateToggleButtons();
        
        // Django i18n için cookie ayarla
        this.setDjangoCookie(language);
        
        // Event dispatch et
        window.dispatchEvent(new CustomEvent('languageChanged', {
            detail: { language }
        }));
        
        // Django'ya AJAX ile dil değişikliğini bildir
        this.notifyDjangoLanguageChange(language);
    }

    /**
     * Django'nun dil çerezini ayarla
     */
    setDjangoCookie(language) {
        document.cookie = `django_language=${language}; path=/; max-age=31536000; SameSite=Lax`;
    }

    /**
     * Django'ya AJAX ile dil değişikliğini bildir
     */
    notifyDjangoLanguageChange(language) {
        // Django'nun set_language view'ini kullan
        const formData = new FormData();
        formData.append('language', language);
        formData.append('next', window.location.pathname);
        
        // CSRF token'ı al
        const csrfToken = document.querySelector('[name=csrf-token]')?.getAttribute('content') || 
                         document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        
        if (csrfToken) {
            formData.append('csrfmiddlewaretoken', csrfToken);
        }
        
        // Sessizce POST et (sayfayı yenileme)
        fetch('/i18n/setlang/', {
            method: 'POST',
            body: formData,
            credentials: 'same-origin'
        }).then(() => {
            // Başarılı olursa sayfayı yenile
            window.location.reload();
        }).catch(error => {
            console.warn('Language change notification failed:', error);
            // Hata durumunda da sayfayı yenile
            window.location.reload();
        });
    }

    /**
     * Dili uygula
     */
    applyLanguage(language) {
        // HTML lang attribute'unu güncelle
        document.documentElement.lang = language;
        
        // Body'ye dil class'ı ekle
        document.body.className = document.body.className
            .replace(/\blang-\w+\b/g, '') + ` lang-${language}`;
        
        // Meta tag'leri güncelle
        this.updateMetaTags(language);
        
        // JavaScript string'leri güncelle
        this.updateJavaScriptStrings(language);
    }

    /**
     * Meta tag'leri güncelle
     */
    updateMetaTags(language) {
        // Language meta tag
        let langMeta = document.querySelector('meta[name="language"]');
        if (!langMeta) {
            langMeta = document.createElement('meta');
            langMeta.name = 'language';
            document.head.appendChild(langMeta);
        }
        langMeta.content = language;

        // Alternate language links güncelle
        this.updateAlternateLinks(language);
    }

    /**
     * Alternate language link'leri güncelle
     */
    updateAlternateLinks(language) {
        // Mevcut alternate link'leri kaldır
        document.querySelectorAll('link[rel="alternate"][hreflang]').forEach(link => {
            link.remove();
        });

        // Yeni alternate link'leri ekle
        const currentUrl = window.location.pathname;
        const languages = ['tr', 'en'];
        
        languages.forEach(lang => {
            const link = document.createElement('link');
            link.rel = 'alternate';
            link.hreflang = lang;
            link.href = `${window.location.origin}${currentUrl}?lang=${lang}`;
            document.head.appendChild(link);
        });

        // x-default için de bir tane ekle
        const defaultLink = document.createElement('link');
        defaultLink.rel = 'alternate';
        defaultLink.hreflang = 'x-default';
        defaultLink.href = `${window.location.origin}${currentUrl}`;
        document.head.appendChild(defaultLink);
    }

    /**
     * JavaScript string'leri güncelle
     */
    updateJavaScriptStrings(language) {
        // Global translations objesi oluştur
        window.translations = this.getTranslations(language);
        
        // Dinamik içerikleri güncelle
        this.updateDynamicContent(language);
    }

    /**
     * Çeviri objesi döndür
     */
    getTranslations(language) {
        const translations = {
            tr: {
                // Navigation
                'home': 'Ana Sayfa',
                'about': 'Hakkımda',
                'projects': 'Projeler',
                'blog': 'Blog',
                'tools': 'Araçlar',
                'contact': 'İletişim',
                
                // UI Elements
                'search': 'Ara',
                'search_placeholder': 'Blog, proje veya içerik ara...',
                'loading': 'Yükleniyor...',
                'load_more': 'Daha Fazla Yükle',
                'back_to_top': 'Başa Dön',
                
                // Forms
                'name': 'İsim',
                'email': 'E-posta',
                'message': 'Mesaj',
                'send': 'Gönder',
                'sending': 'Gönderiliyor...',
                'sent': 'Gönderildi',
                'error': 'Hata',
                
                // Time & Dates
                'read_time': 'dakika okuma',
                'published': 'Yayınlandı',
                'updated': 'Güncellendi',
                
                // Messages
                'success_message': 'İşlem başarıyla tamamlandı',
                'error_message': 'Bir hata oluştu',
                'network_error': 'Bağlantı hatası',
            },
            en: {
                // Navigation
                'home': 'Home',
                'about': 'About',
                'projects': 'Projects',
                'blog': 'Blog',
                'tools': 'Tools',
                'contact': 'Contact',
                
                // UI Elements
                'search': 'Search',
                'search_placeholder': 'Search blog, projects or content...',
                'loading': 'Loading...',
                'load_more': 'Load More',
                'back_to_top': 'Back to Top',
                
                // Forms
                'name': 'Name',
                'email': 'Email',
                'message': 'Message',
                'send': 'Send',
                'sending': 'Sending...',
                'sent': 'Sent',
                'error': 'Error',
                
                // Time & Dates
                'read_time': 'min read',
                'published': 'Published',
                'updated': 'Updated',
                
                // Messages
                'success_message': 'Operation completed successfully',
                'error_message': 'An error occurred',
                'network_error': 'Network error',
            }
        };
        
        return translations[language] || translations.tr;
    }

    /**
     * Dinamik içerikleri güncelle
     */
    updateDynamicContent(language) {
        // JavaScript tarafından oluşturulan içerikleri güncelle
        const elementsToUpdate = document.querySelectorAll('[data-translate]');
        elementsToUpdate.forEach(element => {
            const key = element.getAttribute('data-translate');
            if (window.translations[key]) {
                element.textContent = window.translations[key];
            }
        });

        // Placeholder'ları güncelle
        const inputsToUpdate = document.querySelectorAll('[data-translate-placeholder]');
        inputsToUpdate.forEach(input => {
            const key = input.getAttribute('data-translate-placeholder');
            if (window.translations[key]) {
                input.placeholder = window.translations[key];
            }
        });

        // Title attribute'larını güncelle
        const titlesToUpdate = document.querySelectorAll('[data-translate-title]');
        titlesToUpdate.forEach(element => {
            const key = element.getAttribute('data-translate-title');
            if (window.translations[key]) {
                element.title = window.translations[key];
            }
        });
    }

    /**
     * Toggle butonlarını güncelle
     */
    updateToggleButtons() {
        const toggleButtons = document.querySelectorAll('[data-language-switch]');
        toggleButtons.forEach(button => {
            // Aktif dil butonunu işaretle
            const buttonLang = button.getAttribute('data-language-switch');
            if (buttonLang === this.currentLanguage) {
                // Aktif button stilleri
                button.className = 'px-2 py-1 text-xs font-medium rounded transition-colors duration-200 bg-primary-600 text-white';
                button.setAttribute('aria-pressed', 'true');
                // Alpine.js x-bind:class'ını kaldır
                button.removeAttribute('x-bind:class');
            } else {
                // İnaktif button stilleri - Alpine.js kullan
                button.className = 'px-2 py-1 text-xs font-medium rounded transition-colors duration-200';
                button.setAttribute('x-bind:class', "{ 'text-gray-300 hover:text-white hover:bg-gray-700': darkMode, 'text-gray-600 hover:text-gray-900 hover:bg-gray-300': !darkMode }");
                button.setAttribute('aria-pressed', 'false');
            }
            
            // Button text'ini güncelle
            this.updateButtonText(button);
        });

        // Generic toggle button'ları güncelle
        const genericToggleButtons = document.querySelectorAll('[data-toggle="language"]');
        genericToggleButtons.forEach(button => {
            this.updateButtonText(button);
        });
    }

    /**
     * Button text'ini güncelle
     */
    updateButtonText(button) {
        const langLabels = {
            tr: 'TR',
            en: 'EN'
        };
        
        // Eğer button sadece dil kodu gösteriyorsa
        if (button.hasAttribute('data-show-current')) {
            button.textContent = langLabels[this.currentLanguage];
        }
        
        // Eğer button alternatif dili gösteriyorsa
        if (button.hasAttribute('data-show-alternative')) {
            const altLang = this.currentLanguage === 'tr' ? 'en' : 'tr';
            button.textContent = langLabels[altLang];
        }
    }

    /**
     * Event listener'ları bağla
     */
    bindEvents() {
        // Dil toggle butonları
        document.addEventListener('click', (e) => {
            // Spesifik dil butonları
            if (e.target.hasAttribute('data-language-switch')) {
                e.preventDefault();
                const targetLang = e.target.getAttribute('data-language-switch');
                this.setLanguage(targetLang);
            }
            
            // Generic toggle butonları
            if (e.target.hasAttribute('data-toggle') && e.target.getAttribute('data-toggle') === 'language') {
                e.preventDefault();
                this.toggleLanguage();
            }
        });

        // Klavye kısayolları (Alt+L)
        document.addEventListener('keydown', (e) => {
            if (e.altKey && e.key.toLowerCase() === 'l') {
                e.preventDefault();
                this.toggleLanguage();
            }
        });

        // System language change detection
        window.addEventListener('languagechange', () => {
            if (!this.getStoredLanguage()) {
                const newSystemLang = this.detectSystemLanguage();
                if (newSystemLang !== this.currentLanguage) {
                    this.setLanguage(newSystemLang);
                }
            }
        });
    }

    /**
     * Mevcut dili döndür
     */
    getCurrentLanguage() {
        return this.currentLanguage;
    }

    /**
     * Dil değişiklik callback'i ekle
     */
    onLanguageChange(callback) {
        window.addEventListener('languageChanged', (e) => {
            callback(e.detail.language);
        });
    }
}

// Auto-initialize
let languageManager;
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        languageManager = new LanguageManager();
        window.languageManager = languageManager;
    });
} else {
    languageManager = new LanguageManager();
    window.languageManager = languageManager;
}

// Utility function for translations
window.t = function(key, fallback = key) {
    return (window.translations && window.translations[key]) || fallback;
};

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = LanguageManager;
}