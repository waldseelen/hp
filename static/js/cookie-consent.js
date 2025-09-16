/**
 * Cookie Consent Banner
 * GDPR-compliant cookie consent management
 */

class CookieConsent {
    constructor() {
        this.consentGiven = false;
        this.preferences = {
            necessary: true,
            functional: false,
            analytics: false,
            marketing: false
        };

        this.init();
    }

    async init() {
        // Check if consent already given
        await this.checkConsentStatus();

        if (!this.consentGiven) {
            this.showConsentBanner();
        }

        this.bindEvents();
    }

    async checkConsentStatus() {
        try {
            const response = await fetch('/gdpr/cookie-consent/status/');
            const data = await response.json();

            this.consentGiven = data.consent_given;
            this.preferences = data.preferences;

        } catch (error) {
            console.error('Error checking consent status:', error);
        }
    }

    showConsentBanner() {
        const banner = this.createConsentBanner();
        document.body.appendChild(banner);

        // Animate in
        setTimeout(() => {
            banner.classList.add('show');
        }, 100);
    }

    createConsentBanner() {
        const banner = document.createElement('div');
        banner.className = 'cookie-consent-banner';
        banner.innerHTML = `
            <div class="cookie-consent-content">
                <div class="cookie-consent-header">
                    <h3>🍪 Çerez Tercihleri</h3>
                    <p>Web sitemizi geliştirmek ve size daha iyi hizmet sunmak için çerezler kullanıyoruz.</p>
                </div>

                <div class="cookie-consent-options">
                    <div class="cookie-option">
                        <label>
                            <input type="checkbox" id="necessary" checked disabled>
                            <span class="cookie-label">
                                <strong>Gerekli Çerezler</strong>
                                <small>Sitenin çalışması için gerekli</small>
                            </span>
                        </label>
                    </div>

                    <div class="cookie-option">
                        <label>
                            <input type="checkbox" id="functional">
                            <span class="cookie-label">
                                <strong>İşlevsel Çerezler</strong>
                                <small>Gelişmiş özellikler için</small>
                            </span>
                        </label>
                    </div>

                    <div class="cookie-option">
                        <label>
                            <input type="checkbox" id="analytics">
                            <span class="cookie-label">
                                <strong>Analitik Çerezler</strong>
                                <small>Site iyileştirmeleri için</small>
                            </span>
                        </label>
                    </div>

                    <div class="cookie-option">
                        <label>
                            <input type="checkbox" id="marketing">
                            <span class="cookie-label">
                                <strong>Pazarlama Çerezleri</strong>
                                <small>Kişiselleştirilmiş reklamlar için</small>
                            </span>
                        </label>
                    </div>
                </div>

                <div class="cookie-consent-actions">
                    <button class="btn-accept-all" onclick="cookieConsent.acceptAll()">
                        Hepsini Kabul Et
                    </button>
                    <button class="btn-save-preferences" onclick="cookieConsent.savePreferences()">
                        Tercihleri Kaydet
                    </button>
                    <button class="btn-reject-optional" onclick="cookieConsent.rejectOptional()">
                        Sadece Gerekli
                    </button>
                </div>

                <div class="cookie-consent-links">
                    <a href="/gdpr/privacy-policy/" target="_blank">Gizlilik Politikası</a>
                    <a href="/gdpr/cookie-policy/" target="_blank">Çerez Politikası</a>
                </div>
            </div>
        `;

        return banner;
    }

    async acceptAll() {
        this.preferences = {
            necessary: true,
            functional: true,
            analytics: true,
            marketing: true
        };

        await this.saveConsent();
        this.hideConsentBanner();
        this.enableTrackingServices();
    }

    async rejectOptional() {
        this.preferences = {
            necessary: true,
            functional: false,
            analytics: false,
            marketing: false
        };

        await this.saveConsent();
        this.hideConsentBanner();
    }

    async savePreferences() {
        const banner = document.querySelector('.cookie-consent-banner');

        this.preferences = {
            necessary: true, // Always true
            functional: banner.querySelector('#functional').checked,
            analytics: banner.querySelector('#analytics').checked,
            marketing: banner.querySelector('#marketing').checked
        };

        await this.saveConsent();
        this.hideConsentBanner();
        this.enableTrackingServices();
    }

    async saveConsent() {
        try {
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
                            document.querySelector('meta[name=csrf-token]')?.content;

            const response = await fetch('/gdpr/cookie-consent/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                },
                body: JSON.stringify(this.preferences)
            });

            if (response.ok) {
                this.consentGiven = true;
                console.log('Cookie consent saved successfully');
            } else {
                console.error('Failed to save cookie consent');
            }

        } catch (error) {
            console.error('Error saving consent:', error);
        }
    }

    hideConsentBanner() {
        const banner = document.querySelector('.cookie-consent-banner');
        if (banner) {
            banner.classList.add('hide');
            setTimeout(() => {
                banner.remove();
            }, 300);
        }
    }

    enableTrackingServices() {
        // Enable analytics if consented
        if (this.preferences.analytics) {
            this.enableAnalytics();
        }

        // Enable marketing if consented
        if (this.preferences.marketing) {
            this.enableMarketing();
        }

        // Enable functional features if consented
        if (this.preferences.functional) {
            this.enableFunctional();
        }
    }

    enableAnalytics() {
        // Example: Initialize Google Analytics
        console.log('Analytics enabled');

        // gtag('consent', 'update', {
        //     'analytics_storage': 'granted'
        // });
    }

    enableMarketing() {
        // Example: Initialize marketing pixels
        console.log('Marketing enabled');

        // gtag('consent', 'update', {
        //     'ad_storage': 'granted'
        // });
    }

    enableFunctional() {
        // Example: Enable chat widgets, etc.
        console.log('Functional features enabled');
    }

    bindEvents() {
        // Settings button to manage preferences
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('cookie-settings-btn')) {
                this.showPreferencesModal();
            }
        });
    }

    showPreferencesModal() {
        // Show modal to update preferences
        const modal = this.createPreferencesModal();
        document.body.appendChild(modal);
    }

    createPreferencesModal() {
        const modal = document.createElement('div');
        modal.className = 'cookie-preferences-modal';
        modal.innerHTML = `
            <div class="modal-overlay" onclick="this.parentElement.remove()"></div>
            <div class="modal-content">
                <div class="modal-header">
                    <h3>Çerez Tercihleri</h3>
                    <button class="modal-close" onclick="this.closest('.cookie-preferences-modal').remove()">×</button>
                </div>

                <div class="modal-body">
                    <div class="cookie-option">
                        <label>
                            <input type="checkbox" id="modal-necessary" checked disabled>
                            <span class="cookie-label">
                                <strong>Gerekli Çerezler</strong>
                                <small>Sitenin çalışması için gerekli</small>
                            </span>
                        </label>
                    </div>

                    <div class="cookie-option">
                        <label>
                            <input type="checkbox" id="modal-functional" ${this.preferences.functional ? 'checked' : ''}>
                            <span class="cookie-label">
                                <strong>İşlevsel Çerezler</strong>
                                <small>Gelişmiş özellikler için</small>
                            </span>
                        </label>
                    </div>

                    <div class="cookie-option">
                        <label>
                            <input type="checkbox" id="modal-analytics" ${this.preferences.analytics ? 'checked' : ''}>
                            <span class="cookie-label">
                                <strong>Analitik Çerezler</strong>
                                <small>Site iyileştirmeleri için</small>
                            </span>
                        </label>
                    </div>

                    <div class="cookie-option">
                        <label>
                            <input type="checkbox" id="modal-marketing" ${this.preferences.marketing ? 'checked' : ''}>
                            <span class="cookie-label">
                                <strong>Pazarlama Çerezleri</strong>
                                <small>Kişiselleştirilmiş reklamlar için</small>
                            </span>
                        </label>
                    </div>
                </div>

                <div class="modal-footer">
                    <button class="btn-save" onclick="cookieConsent.updatePreferencesFromModal()">
                        Tercihleri Kaydet
                    </button>
                </div>
            </div>
        `;

        return modal;
    }

    async updatePreferencesFromModal() {
        const modal = document.querySelector('.cookie-preferences-modal');

        this.preferences = {
            necessary: true,
            functional: modal.querySelector('#modal-functional').checked,
            analytics: modal.querySelector('#modal-analytics').checked,
            marketing: modal.querySelector('#modal-marketing').checked
        };

        await this.saveConsent();
        modal.remove();

        // Reload page to apply new settings
        window.location.reload();
    }
}

// Initialize cookie consent when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.cookieConsent = new CookieConsent();
});

// CSS for cookie consent banner
const style = document.createElement('style');
style.textContent = `
    .cookie-consent-banner {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: rgba(0, 0, 0, 0.95);
        color: white;
        z-index: 10000;
        padding: 20px;
        box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.3);
        transform: translateY(100%);
        transition: transform 0.3s ease;
    }

    .cookie-consent-banner.show {
        transform: translateY(0);
    }

    .cookie-consent-banner.hide {
        transform: translateY(100%);
    }

    .cookie-consent-content {
        max-width: 1200px;
        margin: 0 auto;
    }

    .cookie-consent-header h3 {
        margin: 0 0 10px 0;
        font-size: 1.2em;
    }

    .cookie-consent-header p {
        margin: 0 0 20px 0;
        opacity: 0.9;
    }

    .cookie-consent-options {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 15px;
        margin-bottom: 20px;
    }

    .cookie-option {
        display: flex;
        align-items: center;
    }

    .cookie-option label {
        display: flex;
        align-items: center;
        cursor: pointer;
        width: 100%;
    }

    .cookie-option input {
        margin-right: 10px;
    }

    .cookie-label strong {
        display: block;
        font-size: 0.9em;
    }

    .cookie-label small {
        display: block;
        opacity: 0.7;
        font-size: 0.8em;
    }

    .cookie-consent-actions {
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
        margin-bottom: 15px;
    }

    .cookie-consent-actions button {
        padding: 10px 20px;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        font-weight: 500;
        transition: all 0.2s ease;
    }

    .btn-accept-all {
        background: #28a745;
        color: white;
    }

    .btn-save-preferences {
        background: #007bff;
        color: white;
    }

    .btn-reject-optional {
        background: #6c757d;
        color: white;
    }

    .cookie-consent-actions button:hover {
        opacity: 0.9;
        transform: translateY(-1px);
    }

    .cookie-consent-links {
        display: flex;
        gap: 15px;
        font-size: 0.8em;
    }

    .cookie-consent-links a {
        color: #ccc;
        text-decoration: underline;
    }

    .cookie-consent-links a:hover {
        color: white;
    }

    .cookie-preferences-modal {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        z-index: 10001;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .modal-overlay {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.7);
    }

    .modal-content {
        background: white;
        border-radius: 8px;
        max-width: 500px;
        width: 90%;
        max-height: 80vh;
        overflow-y: auto;
        position: relative;
        color: #333;
    }

    .modal-header {
        padding: 20px;
        border-bottom: 1px solid #eee;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .modal-close {
        background: none;
        border: none;
        font-size: 24px;
        cursor: pointer;
        color: #666;
    }

    .modal-body {
        padding: 20px;
    }

    .modal-footer {
        padding: 20px;
        border-top: 1px solid #eee;
        text-align: right;
    }

    .btn-save {
        background: #007bff;
        color: white;
        padding: 10px 20px;
        border: none;
        border-radius: 4px;
        cursor: pointer;
    }

    @media (max-width: 768px) {
        .cookie-consent-options {
            grid-template-columns: 1fr;
        }

        .cookie-consent-actions {
            flex-direction: column;
        }

        .cookie-consent-actions button {
            width: 100%;
        }
    }
`;

document.head.appendChild(style);