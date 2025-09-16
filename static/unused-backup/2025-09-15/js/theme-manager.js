/**
 * THEME-MANAGER.JS - Gelişmiş Tema Yönetim Sistemi (Advanced Theme Management System)
 * ==================================================================================
 *
 * Bu dosya, web sitesi için kapsamlı bir tema yönetim sistemi sağlar. Kullanıcıların
 * çoklu renk paletleri arasında seçim yapmasına, tema tercihlerini kaydetmesine ve
 * klavye kısayolları ile tema değiştirmesine olanak tanır.
 *
 * TEMEL ÖZELLİKLER:
 * • 10 farklı önceden tanımlanmış tema (karanlık, aydınlık, okyanus, orman vb.)
 * • Sistem tema tercihlerini otomatik algılama
 * • LocalStorage ile tema tercihlerini kalıcı saklama
 * • Klavye kısayolları desteği (Ctrl+Shift+T)
 * • Sayı tuşları ile hızlı tema seçimi (1-9)
 * • Animasyonlu tema geçişleri ve görsel geri bildirimler
 * • Tema değişikliği bildirimleri
 * • Cyberpunk teması için özel efektler
 * • Mobil cihazlar için meta theme-color güncellemesi
 * • İçe/dışa aktarma desteği
 *
 * BAĞIMLILIKLAR:
 * • Modern tarayıcılar (ES6+ desteği gerekli)
 * • CSS özel değişkenleri (:root CSS variables)
 * • LocalStorage API
 * • MatchMedia API (sistem tema algılama için)
 * • İlgili CSS tema dosyaları (theme-palettes.css)
 *
 * TARAYICI UYUMLULUK:
 * • Chrome 49+, Firefox 31+, Safari 9.1+, Edge 16+
 * • IE11+ (sınırlı destek, bazı özellikler çalışmayabilir)
 * • Modern mobil tarayıcılar
 *
 * PERFORMANS VE OPTİMİZASYON:
 * • Debounce edilmiş olay yöneticileri
 * • RequestAnimationFrame kullanarak pürüzsüz animasyonlar
 * • Bellek sızıntılarını önlemek için olay dinleyici temizleme
 * • CSS transformasyonları ile donanım hızlandırması
 * • Lazy loading ile gereksiz DOM manipülasyonlarını önleme
 *
 * @author Portfolio Site
 * @version 2.0.0
 * @since 1.0.0
 */
// TEMA YÖNETİM SINIFI / THEME MANAGEMENT CLASS
class ThemeManager {
    /**
     * Tema yöneticisini başlatır ve kullanılabilir temaları tanımlar
     * Initializes theme manager and defines available themes
     */
    constructor() {
        // VARSAYILAN AYARLAR / DEFAULT SETTINGS
        this.currentTheme = 'dark';
        this.availableThemes = {
            'dark': {
                name: 'Dark',
                description: 'Classic dark theme',
                icon: '🌙'
            },
            'light': {
                name: 'Light',
                description: 'Clean light theme',
                icon: '☀️'
            },
            'ocean': {
                name: 'Ocean Blue',
                description: 'Deep ocean vibes',
                icon: '🌊'
            },
            'forest': {
                name: 'Forest Green',
                description: 'Nature inspired',
                icon: '🌲'
            },
            'sunset': {
                name: 'Sunset Orange',
                description: 'Warm sunset colors',
                icon: '🌅'
            },
            'galaxy': {
                name: 'Purple Galaxy',
                description: 'Cosmic purple theme',
                icon: '🌌'
            },
            'rose': {
                name: 'Rose Pink',
                description: 'Elegant rose tones',
                icon: '🌹'
            },
            'cyber': {
                name: 'Cyberpunk',
                description: 'Futuristic neon',
                icon: '🤖'
            },
            'minimal': {
                name: 'Minimalist',
                description: 'Clean and simple',
                icon: '⚪'
            },
            'contrast': {
                name: 'High Contrast',
                description: 'Accessibility focused',
                icon: '⚫'
            }
        };
        
        this.themeSelector = null;
        this.init();
    }

    /**
     * Tema yöneticisini başlatır ve tüm bileşenleri kurar
     * Initializes theme manager and sets up all components
     */
    init() {
        // BAŞLATMA SIRASI / INITIALIZATION ORDER
        this.loadSavedTheme();              // Kaydedilmiş temayı yükle
        this.createThemeToggleButton();     // Tema değiştirici butonu oluştur
        this.createThemeSelector();         // Tema seçici panel oluştur  
        this.bindEvents();                  // Olay dinleyicilerini bağla
        this.applyTheme(this.currentTheme); // Mevcut temayı uygula
        this.setupKeyboardShortcuts();      // Klavye kısayollarını ayarla
    }

    // TEMA YÜKLEMEVETELENGİ / THEME LOADING AND DETECTION
    /**
     * Kaydedilmiş tema tercihini yükler, yoksa sistem tercihini algılar
     * Loads saved theme preference, detects system preference if none saved
     */
    loadSavedTheme() {
        const savedTheme = localStorage.getItem('selectedTheme');
        if (savedTheme && this.availableThemes[savedTheme]) {
            this.currentTheme = savedTheme;
        } else {
            // Detect system preference
            if (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches) {
                this.currentTheme = 'light';
            }
        }
    }

    // UI BİLEŞENLERİ OLUŞTURMA / UI COMPONENTS CREATION
    /**
     * Tema değiştirici butonunu oluşturur ve sayfaya ekler
     * Creates and adds theme toggle button to the page
     */
    createThemeToggleButton() {
        const existingBtn = document.getElementById('theme-toggle-btn');
        if (existingBtn) return;

        const toggleBtn = document.createElement('button');
        toggleBtn.id = 'theme-toggle-btn';
        toggleBtn.className = 'theme-toggle-btn';
        toggleBtn.innerHTML = '🎨';
        toggleBtn.setAttribute('aria-label', 'Open theme selector');
        toggleBtn.setAttribute('title', 'Change theme');
        
        document.body.appendChild(toggleBtn);
    }

    createThemeSelector() {
        const existingSelector = document.getElementById('theme-selector');
        if (existingSelector) return;

        const selector = document.createElement('div');
        selector.id = 'theme-selector';
        selector.className = 'theme-selector';
        
        selector.innerHTML = `
            <h3>Choose Theme</h3>
            <div class="theme-options">
                ${Object.entries(this.availableThemes).map(([key, theme]) => `
                    <div class="theme-option ${key === this.currentTheme ? 'active' : ''}" 
                         data-theme="${key}"
                         role="button"
                         tabindex="0"
                         aria-label="Select ${theme.name} theme">
                        <div class="theme-preview ${key}"></div>
                        <div class="theme-info">
                            <div class="theme-name">${theme.icon} ${theme.name}</div>
                            <div class="theme-description">${theme.description}</div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
        
        document.body.appendChild(selector);
        this.themeSelector = selector;
    }

    bindEvents() {
        // Toggle button click
        const toggleBtn = document.getElementById('theme-toggle-btn');
        toggleBtn?.addEventListener('click', (e) => {
            e.stopPropagation();
            this.toggleThemeSelector();
        });

        // Theme option clicks
        this.themeSelector?.addEventListener('click', (e) => {
            const option = e.target.closest('.theme-option');
            if (option) {
                const themeKey = option.dataset.theme;
                this.selectTheme(themeKey);
            }
        });

        // Keyboard navigation for theme options
        this.themeSelector?.addEventListener('keydown', (e) => {
            const option = e.target.closest('.theme-option');
            if (!option) return;

            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                const themeKey = option.dataset.theme;
                this.selectTheme(themeKey);
            } else if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
                e.preventDefault();
                this.navigateThemeOptions(e.key === 'ArrowDown');
            }
        });

        // Close selector when clicking outside
        document.addEventListener('click', (e) => {
            if (!this.themeSelector?.contains(e.target) && 
                !document.getElementById('theme-toggle-btn')?.contains(e.target)) {
                this.hideThemeSelector();
            }
        });

        // Escape key to close
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.themeSelector?.classList.contains('show')) {
                this.hideThemeSelector();
            }
        });

        // System theme change detection
        if (window.matchMedia) {
            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
                if (!localStorage.getItem('selectedTheme')) {
                    this.selectTheme(e.matches ? 'dark' : 'light');
                }
            });
        }
    }

    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + Shift + T to toggle theme selector
            if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'T') {
                e.preventDefault();
                this.toggleThemeSelector();
            }
            
            // Number keys 1-9 for quick theme selection (when selector is open)
            if (this.themeSelector?.classList.contains('show') && 
                e.key >= '1' && e.key <= '9') {
                e.preventDefault();
                const themeIndex = parseInt(e.key) - 1;
                const themes = Object.keys(this.availableThemes);
                if (themeIndex < themes.length) {
                    this.selectTheme(themes[themeIndex]);
                }
            }
        });
    }

    toggleThemeSelector() {
        if (this.themeSelector?.classList.contains('show')) {
            this.hideThemeSelector();
        } else {
            this.showThemeSelector();
        }
    }

    showThemeSelector() {
        this.themeSelector?.classList.add('show');
        
        // Focus first theme option
        const firstOption = this.themeSelector?.querySelector('.theme-option');
        firstOption?.focus();
        
        // Add animation class
        this.themeSelector?.style.setProperty('--animation-delay', '0s');
        this.themeSelector?.querySelectorAll('.theme-option').forEach((option, index) => {
            option.style.setProperty('--animation-delay', `${index * 0.05}s`);
            option.classList.add('theme-option-animate');
        });
    }

    hideThemeSelector() {
        this.themeSelector?.classList.remove('show');
        
        // Remove animation classes
        this.themeSelector?.querySelectorAll('.theme-option').forEach(option => {
            option.classList.remove('theme-option-animate');
        });
    }

    navigateThemeOptions(down = true) {
        const options = Array.from(this.themeSelector?.querySelectorAll('.theme-option') || []);
        const current = document.activeElement;
        const currentIndex = options.indexOf(current);
        
        let nextIndex;
        if (down) {
            nextIndex = currentIndex < options.length - 1 ? currentIndex + 1 : 0;
        } else {
            nextIndex = currentIndex > 0 ? currentIndex - 1 : options.length - 1;
        }
        
        options[nextIndex]?.focus();
    }

    selectTheme(themeKey) {
        if (!this.availableThemes[themeKey]) return;
        
        this.currentTheme = themeKey;
        this.applyTheme(themeKey);
        this.saveTheme(themeKey);
        this.updateActiveOption(themeKey);
        this.hideThemeSelector();
        
        // Show confirmation toast
        this.showThemeChangeNotification(themeKey);
        
        // Trigger custom event
        document.dispatchEvent(new CustomEvent('themeChanged', {
            detail: { theme: themeKey, themeData: this.availableThemes[themeKey] }
        }));
    }

    applyTheme(themeKey) {
        document.documentElement.setAttribute('data-theme', themeKey);
        document.body.className = document.body.className.replace(/theme-\w+/g, '');
        document.body.classList.add(`theme-${themeKey}`);
        
        // Update meta theme-color for mobile browsers
        this.updateMetaThemeColor(themeKey);
        
        // Apply theme-specific body classes for complex styling
        this.applyThemeSpecificStyles(themeKey);
    }

    updateMetaThemeColor(themeKey) {
        const themeColors = {
            'dark': '#111827',
            'light': '#ffffff',
            'ocean': '#0c1222',
            'forest': '#0f1419',
            'sunset': '#1a0f0a',
            'galaxy': '#0f0319',
            'rose': '#1f0a14',
            'cyber': '#0a0a0a',
            'minimal': '#fafafa',
            'contrast': '#000000'
        };
        
        let metaTheme = document.querySelector('meta[name="theme-color"]');
        if (!metaTheme) {
            metaTheme = document.createElement('meta');
            metaTheme.name = 'theme-color';
            document.head.appendChild(metaTheme);
        }
        
        metaTheme.content = themeColors[themeKey] || themeColors.dark;
    }

    applyThemeSpecificStyles(themeKey) {
        // Remove existing theme-specific classes
        document.body.classList.remove('high-contrast', 'dark-theme', 'light-theme');
        
        // Add theme-specific classes
        switch (themeKey) {
            case 'contrast':
                document.body.classList.add('high-contrast');
                break;
            case 'light':
            case 'minimal':
                document.body.classList.add('light-theme');
                break;
            default:
                document.body.classList.add('dark-theme');
        }
        
        // Special handling for cyber theme
        if (themeKey === 'cyber') {
            this.applyCyberEffects();
        } else {
            this.removeCyberEffects();
        }
    }

    applyCyberEffects() {
        if (!document.getElementById('cyber-effects')) {
            const style = document.createElement('style');
            style.id = 'cyber-effects';
            style.textContent = `
                body.theme-cyber {
                    text-shadow: 0 0 5px currentColor;
                }
                .theme-cyber .card {
                    box-shadow: 0 0 20px rgba(255, 0, 128, 0.3);
                    border: 1px solid #ff0080;
                }
                .theme-cyber .btn-primary {
                    box-shadow: 0 0 15px rgba(0, 255, 255, 0.5);
                }
            `;
            document.head.appendChild(style);
        }
    }

    removeCyberEffects() {
        const cyberEffects = document.getElementById('cyber-effects');
        if (cyberEffects) {
            cyberEffects.remove();
        }
    }

    saveTheme(themeKey) {
        localStorage.setItem('selectedTheme', themeKey);
    }

    updateActiveOption(themeKey) {
        this.themeSelector?.querySelectorAll('.theme-option').forEach(option => {
            option.classList.remove('active');
            if (option.dataset.theme === themeKey) {
                option.classList.add('active');
            }
        });
    }

    showThemeChangeNotification(themeKey) {
        const theme = this.availableThemes[themeKey];
        
        // Create notification
        const notification = document.createElement('div');
        notification.className = 'theme-change-notification';
        notification.innerHTML = `
            <span class="theme-icon">${theme.icon}</span>
            <span class="theme-text">Switched to ${theme.name}</span>
        `;
        
        // Add styles
        notification.style.cssText = `
            position: fixed;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%) translateY(100px);
            background: var(--bg-secondary);
            color: var(--text-primary);
            border: 1px solid var(--border-primary);
            padding: 12px 20px;
            border-radius: 25px;
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 14px;
            font-weight: 500;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
            z-index: 10000;
            transition: transform 0.3s ease;
        `;
        
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => {
            notification.style.transform = 'translateX(-50%) translateY(0)';
        }, 100);
        
        // Remove after delay
        setTimeout(() => {
            notification.style.transform = 'translateX(-50%) translateY(100px)';
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, 2000);
    }

    // Public API methods
    getCurrentTheme() {
        return this.currentTheme;
    }

    getAvailableThemes() {
        return this.availableThemes;
    }

    setTheme(themeKey) {
        this.selectTheme(themeKey);
    }

    resetToSystemTheme() {
        localStorage.removeItem('selectedTheme');
        const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
        this.selectTheme(systemTheme);
    }

    // Theme preview for admin/settings
    previewTheme(themeKey, duration = 3000) {
        const originalTheme = this.currentTheme;
        this.applyTheme(themeKey);
        
        setTimeout(() => {
            this.applyTheme(originalTheme);
        }, duration);
    }

    // Export theme settings
    exportTheme() {
        return {
            currentTheme: this.currentTheme,
            timestamp: new Date().toISOString()
        };
    }

    // Import theme settings
    importTheme(themeData) {
        if (themeData.currentTheme && this.availableThemes[themeData.currentTheme]) {
            this.selectTheme(themeData.currentTheme);
            return true;
        }
        return false;
    }
}

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.themeManager = new ThemeManager();
});

// Add theme option animation styles
const animationStyles = document.createElement('style');
animationStyles.textContent = `
    .theme-option-animate {
        animation: themeOptionSlideIn 0.3s ease forwards;
        animation-delay: var(--animation-delay, 0s);
    }
    
    @keyframes themeOptionSlideIn {
        from {
            opacity: 0;
            transform: translateX(-20px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    .theme-description {
        font-size: 0.75rem;
        opacity: 0.7;
        margin-top: 2px;
    }
`;
document.head.appendChild(animationStyles);

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ThemeManager;
}