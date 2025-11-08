/**
 * PWA Manager
 * Handles installation prompts, updates, and PWA features
 */

class PWAManager {
    constructor() {
        this.installPrompt = null;
        this.updateAvailable = false;
        this.registration = null;
        this.isStandalone = false;

        this.init();
    }

    async init() {
        // Check if running as PWA
        this.isStandalone = window.matchMedia('(display-mode: standalone)').matches ||
            window.navigator.standalone ||
            document.referrer.includes('android-app://');

        // Set up event listeners
        this.setupEventListeners();

        // Register service worker
        await this.registerServiceWorker();

        // Check for app updates periodically
        this.startUpdateChecker();

        // Show install banner after delay if not installed
        if (!this.isStandalone) {
            setTimeout(() => this.maybeShowInstallBanner(), 30000); // 30 seconds
        }

        console.log('🚀 PWA Manager initialized');
    }

    setupEventListeners() {
        // Install prompt event
        window.addEventListener('beforeinstallprompt', event => {
            event.preventDefault();
            this.installPrompt = event;
            this.showInstallButton();
        });

        // App installed event
        window.addEventListener('appinstalled', () => {
            console.log('📱 PWA installed successfully');
            this.hideInstallButton();
            this.showSuccessNotification('App installed successfully!');
        });

        // Standalone mode detection
        if (this.isStandalone) {
            document.body.classList.add('pwa-standalone');
            this.setupStandaloneFeatures();
        }

        // Network status
        window.addEventListener('online', () => {
            this.handleNetworkChange(true);
        });

        window.addEventListener('offline', () => {
            this.handleNetworkChange(false);
        });

        // Focus events for update checking
        window.addEventListener('focus', () => {
            this.checkForUpdates();
        });
    }

    async registerServiceWorker() {
        if ('serviceWorker' in navigator) {
            try {
                this.registration = await navigator.serviceWorker.register('/static/js/sw-enhanced.js', {
                    scope: '/'
                });

                console.log('✅ Service Worker registered:', this.registration.scope);

                // Listen for updates
                this.registration.addEventListener('updatefound', () => {
                    this.handleServiceWorkerUpdate();
                });

                // Handle active service worker
                if (this.registration.active) {
                    this.setupMessageChannel();
                }

                // Handle controlling service worker
                navigator.serviceWorker.addEventListener('controllerchange', () => {
                    window.location.reload();
                });

            } catch (error) {
                console.error('❌ Service Worker registration failed:', error);
            }
        }
    }

    handleServiceWorkerUpdate() {
        const newWorker = this.registration.installing;

        newWorker.addEventListener('statechange', () => {
            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                this.updateAvailable = true;
                this.showUpdateNotification();
            }
        });
    }

    setupMessageChannel() {
        navigator.serviceWorker.addEventListener('message', event => {
            const { data } = event;

            switch (data.type) {
                case 'CACHE_UPDATED':
                    this.showNotification('Content updated!', 'success');
                    break;

                case 'UPDATE_AVAILABLE':
                    this.showUpdateNotification();
                    break;

                case 'OFFLINE_READY':
                    this.showNotification('App ready for offline use', 'info');
                    break;
            }
        });
    }

    showInstallButton() {
        let installButton = document.getElementById('pwa-install-btn');

        if (!installButton) {
            installButton = this.createInstallButton();
            document.body.appendChild(installButton);
        }

        installButton.style.display = 'flex';
        installButton.addEventListener('click', () => this.promptInstall());
    }

    createInstallButton() {
        const button = document.createElement('button');
        button.id = 'pwa-install-btn';
        button.innerHTML = `
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                <path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/>
            </svg>
            <span>Install App</span>
        `;

        button.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #3b82f6;
            color: white;
            border: none;
            border-radius: 50px;
            padding: 12px 24px;
            display: flex;
            align-items: center;
            gap: 8px;
            font-weight: 500;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
            cursor: pointer;
            transition: all 0.3s ease;
            z-index: 1000;
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
        `;

        button.addEventListener('mouseenter', () => {
            button.style.transform = 'translateY(-2px)';
            button.style.boxShadow = '0 6px 16px rgba(59, 130, 246, 0.4)';
        });

        button.addEventListener('mouseleave', () => {
            button.style.transform = 'translateY(0)';
            button.style.boxShadow = '0 4px 12px rgba(59, 130, 246, 0.3)';
        });

        return button;
    }

    async promptInstall() {
        if (!this.installPrompt) { return; }

        const result = await this.installPrompt.prompt();
        console.log('📱 Install prompt result:', result.outcome);

        this.installPrompt = null;
        this.hideInstallButton();
    }

    hideInstallButton() {
        const installButton = document.getElementById('pwa-install-btn');
        if (installButton) {
            installButton.style.display = 'none';
        }
    }

    maybeShowInstallBanner() {
        // Show install banner if conditions are met
        if (this.installPrompt && !this.isStandalone) {
            const visits = parseInt(localStorage.getItem('pwa-visits') || '0', 10) + 1;
            localStorage.setItem('pwa-visits', visits.toString());

            // Show after 3 visits and user hasn't dismissed
            if (visits >= 3 && !localStorage.getItem('pwa-banner-dismissed')) {
                this.showInstallBanner();
            }
        }
    }

    showInstallBanner() {
        const banner = document.createElement('div');
        banner.id = 'pwa-install-banner';
        banner.innerHTML = `
            <div class="banner-content">
                <div class="banner-icon">📱</div>
                <div class="banner-text">
                    <strong>Install Portfolio App</strong>
                    <p>Get faster access and offline functionality</p>
                </div>
                <div class="banner-actions">
                    <button class="banner-btn banner-install">Install</button>
                    <button class="banner-btn banner-dismiss">×</button>
                </div>
            </div>
        `;

        banner.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            background: linear-gradient(135deg, #3b82f6, #1d4ed8);
            color: white;
            z-index: 1001;
            transform: translateY(-100%);
            transition: transform 0.3s ease;
        `;

        const style = document.createElement('style');
        style.textContent = `
            .banner-content {
                display: flex;
                align-items: center;
                padding: 12px 16px;
                max-width: 1200px;
                margin: 0 auto;
            }
            .banner-icon {
                font-size: 24px;
                margin-right: 12px;
            }
            .banner-text {
                flex: 1;
            }
            .banner-text strong {
                display: block;
                font-size: 14px;
            }
            .banner-text p {
                font-size: 12px;
                opacity: 0.9;
                margin: 2px 0 0;
            }
            .banner-actions {
                display: flex;
                gap: 8px;
            }
            .banner-btn {
                background: rgba(255, 255, 255, 0.2);
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 20px;
                cursor: pointer;
                font-weight: 500;
                transition: background 0.2s ease;
            }
            .banner-btn:hover {
                background: rgba(255, 255, 255, 0.3);
            }
            .banner-dismiss {
                width: 32px !important;
                padding: 8px !important;
                font-size: 18px;
            }
        `;

        document.head.appendChild(style);
        document.body.appendChild(banner);

        // Show banner with animation
        setTimeout(() => {
            banner.style.transform = 'translateY(0)';
        }, 100);

        // Event listeners
        banner.querySelector('.banner-install').addEventListener('click', () => {
            this.promptInstall();
            this.hideBanner(banner);
        });

        banner.querySelector('.banner-dismiss').addEventListener('click', () => {
            localStorage.setItem('pwa-banner-dismissed', 'true');
            this.hideBanner(banner);
        });

        // Auto-hide after 10 seconds
        setTimeout(() => {
            if (document.body.contains(banner)) {
                this.hideBanner(banner);
            }
        }, 10000);
    }

    hideBanner(banner) {
        banner.style.transform = 'translateY(-100%)';
        setTimeout(() => {
            if (document.body.contains(banner)) {
                document.body.removeChild(banner);
            }
        }, 300);
    }

    showUpdateNotification() {
        const notification = this.createNotification({
            title: 'Update Available',
            message: 'A new version of the app is ready',
            type: 'info',
            actions: [
                {
                    text: 'Update Now',
                    action: () => this.applyUpdate()
                },
                {
                    text: 'Later',
                    action: () => this.dismissUpdate()
                }
            ]
        });

        document.body.appendChild(notification);
    }

    async applyUpdate() {
        if (this.registration && this.registration.waiting) {
            this.registration.waiting.postMessage({ type: 'SKIP_WAITING' });
            this.showNotification('Updating app...', 'info');
        }
    }

    dismissUpdate() {
        // User chose to update later
        setTimeout(() => {
            this.showUpdateNotification();
        }, 600000); // Show again in 10 minutes
    }

    setupStandaloneFeatures() {
        // Add PWA-specific styles and behaviors
        document.documentElement.style.setProperty('--safe-area-inset-top', 'env(safe-area-inset-top, 0px)');
        document.documentElement.style.setProperty('--safe-area-inset-bottom', 'env(safe-area-inset-bottom, 0px)');

        // Handle back button in standalone mode
        if (window.history.length === 1) {
            // Add custom back button or handle navigation
            this.addStandaloneBackButton();
        }
    }

    addStandaloneBackButton() {
        // Only add if not on home page
        if (window.location.pathname !== '/') {
            const backButton = document.createElement('button');
            backButton.innerHTML = '← Back';
            backButton.style.cssText = `
                position: fixed;
                top: env(safe-area-inset-top, 10px);
                left: 10px;
                background: rgba(0, 0, 0, 0.1);
                border: none;
                padding: 8px 16px;
                border-radius: 20px;
                cursor: pointer;
                z-index: 1000;
            `;

            backButton.addEventListener('click', () => {
                if (window.history.length > 1) {
                    window.history.back();
                } else {
                    window.location.href = '/';
                }
            });

            document.body.appendChild(backButton);
        }
    }

    handleNetworkChange(isOnline) {
        const status = isOnline ? 'online' : 'offline';
        document.body.classList.toggle('app-offline', !isOnline);

        this.showNotification(
            isOnline ? 'Back online' : 'You\'re offline',
            isOnline ? 'success' : 'warning'
        );
    }

    startUpdateChecker() {
        // Check for updates every 30 minutes
        setInterval(() => {
            this.checkForUpdates();
        }, 30 * 60 * 1000);
    }

    async checkForUpdates() {
        if (this.registration) {
            try {
                await this.registration.update();
            } catch (error) {
                console.log('Update check failed:', error);
            }
        }
    }

    createNotification({ title, message, type = 'info', actions = [], duration = 5000 }) {
        const notification = document.createElement('div');
        notification.className = `pwa-notification pwa-notification-${type}`;

        const actionsHtml = actions.map((action, index) =>
            `<button class="notification-btn" data-action="${index}">${action.text}</button>`
        ).join('');

        notification.innerHTML = `
            <div class="notification-content">
                <strong>${title}</strong>
                <p>${message}</p>
                ${actionsHtml ? `<div class="notification-actions">${actionsHtml}</div>` : ''}
            </div>
            <button class="notification-close">×</button>
        `;

        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: white;
            border-radius: 8px;
            padding: 16px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            max-width: 300px;
            z-index: 1002;
            transform: translateX(100%);
            transition: transform 0.3s ease;
        `;

        // Apply type-specific styles
        const typeColors = {
            info: '#3b82f6',
            success: '#10b981',
            warning: '#f59e0b',
            error: '#ef4444'
        };

        notification.style.borderLeft = `4px solid ${typeColors[type]}`;

        // Add styles for notification content
        const style = document.createElement('style');
        style.textContent = `
            .notification-content strong {
                display: block;
                margin-bottom: 4px;
                color: #1f2937;
            }
            .notification-content p {
                margin: 0 0 8px 0;
                color: #6b7280;
                font-size: 14px;
            }
            .notification-actions {
                display: flex;
                gap: 8px;
                margin-top: 12px;
            }
            .notification-btn {
                background: #f3f4f6;
                border: none;
                padding: 4px 12px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 12px;
            }
            .notification-close {
                position: absolute;
                top: 8px;
                right: 8px;
                background: none;
                border: none;
                font-size: 18px;
                cursor: pointer;
                color: #9ca3af;
            }
        `;

        document.head.appendChild(style);

        // Event listeners
        actions.forEach((action, index) => {
            notification.querySelector(`[data-action="${index}"]`).addEventListener('click', () => {
                action.action();
                this.hideNotification(notification);
            });
        });

        notification.querySelector('.notification-close').addEventListener('click', () => {
            this.hideNotification(notification);
        });

        // Show notification
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 100);

        // Auto-hide
        if (duration > 0) {
            setTimeout(() => {
                this.hideNotification(notification);
            }, duration);
        }

        return notification;
    }

    hideNotification(notification) {
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            if (document.body.contains(notification)) {
                document.body.removeChild(notification);
            }
        }, 300);
    }

    showNotification(message, type = 'info') {
        const notification = this.createNotification({
            title: type.charAt(0).toUpperCase() + type.slice(1),
            message,
            type
        });

        document.body.appendChild(notification);
    }

    showSuccessNotification(message) {
        this.showNotification(message, 'success');
    }

    // Public API
    async getCacheInfo() {
        if (this.registration && this.registration.active) {
            return new Promise(resolve => {
                const messageChannel = new MessageChannel();
                messageChannel.port1.onmessage = event => {
                    resolve(event.data.cacheInfo);
                };

                this.registration.active.postMessage(
                    { type: 'GET_CACHE_INFO' },
                    [messageChannel.port2]
                );
            });
        }
        return null;
    }

    async clearCache() {
        if (this.registration && this.registration.active) {
            return new Promise(resolve => {
                const messageChannel = new MessageChannel();
                messageChannel.port1.onmessage = event => {
                    resolve(event.data.cleared);
                };

                this.registration.active.postMessage(
                    { type: 'CLEAR_CACHE' },
                    [messageChannel.port2]
                );
            });
        }
        return false;
    }
}

// Initialize PWA Manager when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.pwaManager = new PWAManager();
    });
} else {
    window.pwaManager = new PWAManager();
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PWAManager;
}
