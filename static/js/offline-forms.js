/**
 * OFFLINE FORMS - Background Sync Support
 * ======================================
 * 
 * Handles offline form submissions with background sync support.
 * Works with service worker to queue failed submissions and retry
 * when connectivity is restored.
 */

class OfflineFormsManager {
    constructor() {
        this.isOnline = navigator.onLine;
        this.init();
    }

    init() {
        this.bindEvents();
        this.checkOnlineStatus();
        this.registerForNotifications();
    }

    bindEvents() {
        // Online/offline status changes
        window.addEventListener('online', () => this.handleOnline());
        window.addEventListener('offline', () => this.handleOffline());

        // Form submissions
        document.addEventListener('submit', (event) => this.handleFormSubmit(event));

        // Service worker messages
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.addEventListener('message', (event) => {
                this.handleServiceWorkerMessage(event);
            });
        }
    }

    handleOnline() {
        this.isOnline = true;
        this.showConnectionStatus('online');
        this.triggerBackgroundSync();
    }

    handleOffline() {
        this.isOnline = false;
        this.showConnectionStatus('offline');
    }

    showConnectionStatus(status) {
        // Remove existing status indicators
        const existing = document.querySelector('.connection-status');
        if (existing) existing.remove();

        // Create status indicator
        const statusElement = document.createElement('div');
        statusElement.className = `connection-status connection-status--${status}`;
        
        if (status === 'offline') {
            statusElement.innerHTML = `
                <div class="connection-status__content">
                    <svg width="16" height="16" fill="currentColor">
                        <path d="M8 0C3.58 0 0 3.58 0 8s3.58 8 8 8 8-3.58 8-8-3.58-8-8-8zM7 11V9h2v2H7zm0-8v6h2V3H7z"/>
                    </svg>
                    <span>You're offline. Forms will be saved and submitted when connection is restored.</span>
                </div>
            `;
        } else {
            statusElement.innerHTML = `
                <div class="connection-status__content">
                    <svg width="16" height="16" fill="currentColor">
                        <path d="M8 0C3.58 0 0 3.58 0 8s3.58 8 8 8 8-3.58 8-8-3.58-8-8-8zM6.5 12L2 7.5l1.4-1.4L6.5 9.2l4.1-4.1L12 6.5 6.5 12z"/>
                    </svg>
                    <span>Connection restored! Submitting queued forms...</span>
                </div>
            `;
            // Auto-hide online status after 3 seconds
            setTimeout(() => {
                if (statusElement.parentNode) {
                    statusElement.remove();
                }
            }, 3000);
        }

        document.body.appendChild(statusElement);
    }

    async handleFormSubmit(event) {
        const form = event.target;
        
        // Only handle forms with offline-sync class or data attribute
        if (!form.classList.contains('offline-sync') && !form.dataset.offlineSync) {
            return;
        }

        event.preventDefault();

        const formData = new FormData(form);
        const submitButton = form.querySelector('[type="submit"]');
        const originalText = submitButton.textContent;

        try {
            // Show loading state
            this.setFormState(form, 'loading');
            submitButton.textContent = 'Submitting...';
            submitButton.disabled = true;

            // Add CSRF token for POST requests
            if ((form.method || 'POST').toUpperCase() === 'POST') {
                const csrfToken = this.getCSRFToken();
                if (csrfToken && !formData.has('csrfmiddlewaretoken')) {
                    formData.append('csrfmiddlewaretoken', csrfToken);
                }
            }

            // Attempt submission
            const response = await fetch(form.action || window.location.href, {
                method: form.method || 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });

            if (response.ok) {
                const result = await response.json();
                
                if (result.offline) {
                    // Form was queued for background sync
                    this.showMessage('Form saved! It will be submitted when you\'re back online.', 'info');
                    this.setFormState(form, 'queued');
                } else {
                    // Form submitted successfully
                    this.showMessage('Form submitted successfully!', 'success');
                    this.setFormState(form, 'success');
                    form.reset();
                }
            } else {
                throw new Error(`HTTP ${response.status}`);
            }

        } catch (error) {
            console.error('Form submission error:', error);
            
            if (!this.isOnline) {
                this.showMessage('You\'re offline. Form will be submitted when connection is restored.', 'info');
                this.setFormState(form, 'queued');
            } else {
                this.showMessage('Submission failed. Please try again.', 'error');
                this.setFormState(form, 'error');
            }
        } finally {
            submitButton.textContent = originalText;
            submitButton.disabled = false;
        }
    }

    setFormState(form, state) {
        form.classList.remove('form-loading', 'form-success', 'form-error', 'form-queued');
        form.classList.add(`form-${state}`);
    }

    showMessage(message, type = 'info') {
        // Remove existing messages
        const existing = document.querySelectorAll('.form-message');
        existing.forEach(el => el.remove());

        // Create message element
        const messageElement = document.createElement('div');
        messageElement.className = `form-message form-message--${type}`;
        messageElement.innerHTML = `
            <div class="form-message__content">
                <span>${message}</span>
                <button class="form-message__close" onclick="this.parentElement.parentElement.remove()">
                    <svg width="14" height="14" fill="currentColor">
                        <path d="M14 1.41L12.59 0 7 5.59 1.41 0 0 1.41 5.59 7 0 12.59 1.41 14 7 8.41 12.59 14 14 12.59 8.41 7z"/>
                    </svg>
                </button>
            </div>
        `;

        document.body.appendChild(messageElement);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (messageElement.parentNode) {
                messageElement.remove();
            }
        }, 5000);
    }

    checkOnlineStatus() {
        // Initial status check
        if (!this.isOnline) {
            this.showConnectionStatus('offline');
        }
    }

    async triggerBackgroundSync() {
        if ('serviceWorker' in navigator && 'sync' in window.ServiceWorkerRegistration.prototype) {
            try {
                const registration = await navigator.serviceWorker.ready;
                await registration.sync.register('form-sync');
                console.log('Background sync registered for forms');
            } catch (error) {
                console.error('Failed to register background sync:', error);
            }
        }
    }

    async registerForNotifications() {
        if ('serviceWorker' in navigator && 'Notification' in window) {
            const registration = await navigator.serviceWorker.ready;
            
            // Listen for form sync success notifications
            registration.addEventListener('notificationclick', (event) => {
                if (event.notification.data?.type === 'form-success') {
                    event.notification.close();
                    // Optionally redirect user somewhere
                }
            });
        }
    }

    handleServiceWorkerMessage(event) {
        const { type, payload } = event.data || {};
        
        switch (type) {
            case 'form-sync-success':
                this.showMessage('Queued form submitted successfully!', 'success');
                break;
            case 'form-sync-failed':
                this.showMessage('Failed to submit queued form. Will retry later.', 'warning');
                break;
        }
    }

    getCSRFToken() {
        // Try multiple ways to get CSRF token
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
               document.querySelector('[name=csrf-token]')?.getAttribute('content') || 
               document.querySelector('meta[name=csrf-token]')?.getAttribute('content') || 
               '';
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new OfflineFormsManager();
});

// Auto-enable for contact forms
document.addEventListener('DOMContentLoaded', () => {
    const contactForms = document.querySelectorAll('form[action*="/contact/"]');
    contactForms.forEach(form => {
        form.classList.add('offline-sync');
    });
});