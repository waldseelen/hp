/**
 * PWA Manager - Progressive Web App functionality
 * Handles service worker registration, install prompts, and offline status
 */
class PWAManager {
    constructor() {
        this.init();
    }

    async init() {
        // Register service worker
        if ('serviceWorker' in navigator) {
            try {
                // Register from static root for full site scope
                const registration = await navigator.serviceWorker.register('/static/sw.js', {
                    scope: '/'
                });

                console.log('Service Worker registered successfully:', registration.scope);

                // Handle updates
                registration.addEventListener('updatefound', () => {
                    const newWorker = registration.installing;
                    newWorker.addEventListener('statechange', () => {
                        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                            this.showUpdateNotification();
                        }
                    });
                });

            } catch (error) {
                console.error('Service Worker registration failed:', error);
            }
        }

        // Handle install prompt
        this.handleInstallPrompt();

        // Handle network status
        this.handleNetworkStatus();
    }

    handleInstallPrompt() {
        let deferredPrompt;

        window.addEventListener('beforeinstallprompt', e => {
            // Prevent the mini-infobar from appearing on mobile
            e.preventDefault();
            // Stash the event so it can be triggered later.
            deferredPrompt = e;
            // Show install button
            this.showInstallButton(deferredPrompt);
        });

        window.addEventListener('appinstalled', () => {
            // Hide install button
            this.hideInstallButton();
        });
    }

    showInstallButton(deferredPrompt) {
        const installBtn = document.createElement('button');
        installBtn.className = 'pwa-install-btn';
        installBtn.innerHTML = `
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <polyline points="7,10 12,15 17,10"/>
                <line x1="12" y1="15" x2="12" y2="3"/>
            </svg>
            Uygulamayı Yükle
        `;

        installBtn.addEventListener('click', async () => {
            // Show the prompt
            deferredPrompt.prompt();
            // Wait for the user to respond to the prompt
            const { outcome } = await deferredPrompt.userChoice;
            // We no longer need the prompt. Clear it up.
            deferredPrompt = null;
        });

        // Style the button
        installBtn.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: linear-gradient(135deg, #4f46e5, #7c3aed);
            color: white;
            border: none;
            padding: 12px 20px;
            border-radius: 50px;
            font-weight: 600;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(79, 70, 229, 0.3);
            z-index: 1000;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: transform 0.2s ease;
        `;

        installBtn.addEventListener('mouseenter', () => {
            installBtn.style.transform = 'translateY(-2px)';
        });

        installBtn.addEventListener('mouseleave', () => {
            installBtn.style.transform = 'translateY(0)';
        });

        document.body.appendChild(installBtn);
    }

    hideInstallButton() {
        const installBtn = document.querySelector('.pwa-install-btn');
        if (installBtn) {
            installBtn.remove();
        }
    }

    showUpdateNotification() {
        const notification = document.createElement('div');
        notification.className = 'pwa-update-notification';
        notification.innerHTML = `
            <div class="update-content">
                <div class="update-icon">🔄</div>
                <div class="update-text">
                    <strong>Yeni güncelleme mevcut!</strong>
                    <p>Uygulamayı yenilemek için tıklayın</p>
                </div>
                <button class="update-btn" onclick="window.location.reload()">Yenile</button>
                <button class="dismiss-btn" onclick="this.parentElement.parentElement.remove()">×</button>
            </div>
        `;

        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: white;
            border-radius: 12px;
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
            z-index: 1001;
            max-width: 350px;
            animation: slideIn 0.3s ease;
        `;

        // Add animation styles
        const style = document.createElement('style');
        style.textContent = `
            @keyframes slideIn {
                from { transform: translateX(100%); }
                to { transform: translateX(0); }
            }
            .update-content {
                padding: 20px;
                display: flex;
                align-items: center;
                gap: 15px;
            }
            .update-icon {
                font-size: 24px;
            }
            .update-text strong {
                color: #1f2937;
                font-size: 14px;
            }
            .update-text p {
                margin: 4px 0 0 0;
                color: #6b7280;
                font-size: 12px;
            }
            .update-btn {
                background: #4f46e5;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 12px;
                cursor: pointer;
                margin-left: auto;
            }
            .dismiss-btn {
                background: none;
                border: none;
                font-size: 20px;
                cursor: pointer;
                color: #9ca3af;
                margin-left: 8px;
            }
        `;
        document.head.appendChild(style);
        document.body.appendChild(notification);

        // Auto dismiss after 10 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 10000);
    }

    handleNetworkStatus() {
        const updateNetworkStatus = isOnline => {
            const statusBar = document.querySelector('.network-status') || document.createElement('div');
            statusBar.className = 'network-status';

            statusBar.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                padding: 8px 16px;
                text-align: center;
                font-size: 14px;
                font-weight: 600;
                z-index: 1002;
                transition: transform 0.3s ease;
                ${isOnline
        ? 'background: #10b981; color: white; transform: translateY(-100%);'
        : 'background: #ef4444; color: white; transform: translateY(0);'
}
            `;

            statusBar.textContent = isOnline
                ? 'Bağlantı geri geldi!'
                : 'İnternet bağlantısı yok - Offline modda çalışıyor';

            if (!document.querySelector('.network-status')) {
                document.body.appendChild(statusBar);
            }

            if (isOnline) {
                setTimeout(() => {
                    statusBar.style.transform = 'translateY(-100%)';
                    setTimeout(() => statusBar.remove(), 300);
                }, 2000);
            }
        };

        window.addEventListener('online', () => updateNetworkStatus(true));
        window.addEventListener('offline', () => updateNetworkStatus(false));
    }
}

// Initialize PWA Manager when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new PWAManager();
    });
} else {
    new PWAManager();
}
