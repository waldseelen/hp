// ==========================================================================
// ZERO-BASED MODERN ADMIN PANEL - JAVASCRIPT
// Marka Kimliği: Altın (Gold) + Koyu Tema (Dark)
// Versiyon: 1.0.0
// ==========================================================================

// ========== 1. SIDEBAR TOGGLE FUNCTIONALITY ==========
document.addEventListener('DOMContentLoaded', function () {
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');

    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function () {
            sidebar.classList.toggle('sidebar--collapsed');

            // LocalStorage'a tercih kaydet
            const isCollapsed = sidebar.classList.contains('sidebar--collapsed');
            localStorage.setItem('sidebarCollapsed', isCollapsed);
        });

        // Sayfa yüklendiğinde önceki tercihi kontrol et
        const savedState = localStorage.getItem('sidebarCollapsed');
        if (savedState === 'true') {
            sidebar.classList.add('sidebar--collapsed');
        }
    }

    // Mobile: Sidebar dışına tıklanınca kapat
    if (window.innerWidth <= 768) {
        document.addEventListener('click', function (event) {
            if (sidebar && !sidebar.contains(event.target) && !sidebarToggle.contains(event.target)) {
                sidebar.classList.remove('sidebar--open');
            }
        });

        // Mobile toggle için farklı davranış
        if (sidebarToggle) {
            sidebarToggle.addEventListener('click', function () {
                sidebar.classList.toggle('sidebar--open');
            });
        }
    }
});

// ========== 2. LOGIN FORM VALIDATION ==========
const loginForm = document.getElementById('loginForm');

if (loginForm) {
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');
    const emailError = document.getElementById('email-error');
    const passwordError = document.getElementById('password-error');

    // Email validation
    function validateEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    // Show error function
    function showError(input, errorElement, message) {
        input.classList.add('form-input--error');
        errorElement.style.display = 'flex';
        errorElement.querySelector('span').textContent = message;
    }

    // Hide error function
    function hideError(input, errorElement) {
        input.classList.remove('form-input--error');
        errorElement.style.display = 'none';
    }

    // Email input - real-time validation
    if (emailInput && emailError) {
        emailInput.addEventListener('blur', function () {
            const email = emailInput.value.trim();

            if (email === '') {
                showError(emailInput, emailError, 'E-posta adresi gereklidir');
            } else if (!validateEmail(email)) {
                showError(emailInput, emailError, 'Geçerli bir e-posta adresi giriniz');
            } else {
                hideError(emailInput, emailError);
            }
        });

        // Yazarken hatayı temizle
        emailInput.addEventListener('input', function () {
            if (emailInput.classList.contains('form-input--error')) {
                const email = emailInput.value.trim();
                if (email !== '' && validateEmail(email)) {
                    hideError(emailInput, emailError);
                }
            }
        });
    }

    // Password input - real-time validation
    if (passwordInput && passwordError) {
        passwordInput.addEventListener('blur', function () {
            const password = passwordInput.value;

            if (password === '') {
                showError(passwordInput, passwordError, 'Şifre gereklidir');
            } else if (password.length < 6) {
                showError(passwordInput, passwordError, 'Şifre en az 6 karakter olmalıdır');
            } else {
                hideError(passwordInput, passwordError);
            }
        });

        // Yazarken hatayı temizle
        passwordInput.addEventListener('input', function () {
            if (passwordInput.classList.contains('form-input--error')) {
                const password = passwordInput.value;
                if (password.length >= 6) {
                    hideError(passwordInput, passwordError);
                }
            }
        });
    }

    // Form submit
    loginForm.addEventListener('submit', function (e) {
        e.preventDefault();

        let isValid = true;
        const email = emailInput.value.trim();
        const password = passwordInput.value;

        // Email validation
        if (email === '') {
            showError(emailInput, emailError, 'E-posta adresi gereklidir');
            isValid = false;
        } else if (!validateEmail(email)) {
            showError(emailInput, emailError, 'Geçerli bir e-posta adresi giriniz');
            isValid = false;
        } else {
            hideError(emailInput, emailError);
        }

        // Password validation
        if (password === '') {
            showError(passwordInput, passwordError, 'Şifre gereklidir');
            isValid = false;
        } else if (password.length < 6) {
            showError(passwordInput, passwordError, 'Şifre en az 6 karakter olmalıdır');
            isValid = false;
        } else {
            hideError(passwordInput, passwordError);
        }

        // If valid, proceed with login
        if (isValid) {
            // Form submit animation
            const submitBtn = loginForm.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            submitBtn.innerHTML = `
                <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor" style="animation: spin 1s linear infinite;">
                    <path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z"/>
                </svg>
                Giriş yapılıyor...
            `;

            // Simulate API call
            setTimeout(function () {
                // Redirect to dashboard
                window.location.href = 'dashboard.html';
            }, 1500);
        }
    });
}

// ========== 3. SMOOTH SCROLL FOR ANCHOR LINKS ==========
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));

        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// ========== 4. KEYBOARD NAVIGATION IMPROVEMENTS ==========
// ESC key to close mobile sidebar
document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
        const sidebar = document.getElementById('sidebar');
        if (sidebar && sidebar.classList.contains('sidebar--open')) {
            sidebar.classList.remove('sidebar--open');
        }
    }
});

// Tab trap in sidebar on mobile
const sidebar = document.getElementById('sidebar');
if (sidebar && window.innerWidth <= 768) {
    const focusableElements = sidebar.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );

    if (focusableElements.length > 0) {
        const firstFocusable = focusableElements[0];
        const lastFocusable = focusableElements[focusableElements.length - 1];

        sidebar.addEventListener('keydown', function (e) {
            if (e.key === 'Tab' && sidebar.classList.contains('sidebar--open')) {
                if (e.shiftKey) {
                    if (document.activeElement === firstFocusable) {
                        e.preventDefault();
                        lastFocusable.focus();
                    }
                } else {
                    if (document.activeElement === lastFocusable) {
                        e.preventDefault();
                        firstFocusable.focus();
                    }
                }
            }
        });
    }
}

// ========== 5. UTILITY FUNCTIONS ==========

// Debounce function for performance
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Toast notification (for future use)
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast--${type}`;
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed;
        bottom: 24px;
        right: 24px;
        padding: 16px 24px;
        background: var(--bg-surface);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-lg);
        box-shadow: var(--shadow-lg);
        color: var(--text-primary);
        z-index: 1000;
        animation: slideIn 0.3s ease;
    `;

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// CSS for toast animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }

    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }

    @keyframes spin {
        from {
            transform: rotate(0deg);
        }
        to {
            transform: rotate(360deg);
        }
    }
`;
document.head.appendChild(style);

// ========== 6. ACCESSIBILITY: Focus Visible Polyfill ==========
// Modern browsers already support :focus-visible, but this ensures compatibility
document.addEventListener('mousedown', function () {
    document.body.classList.add('using-mouse');
});

document.addEventListener('keydown', function (e) {
    if (e.key === 'Tab') {
        document.body.classList.remove('using-mouse');
    }
});

// ========== 7. PERFORMANCE: Lazy Loading for Images (if needed) ==========
if ('IntersectionObserver' in window) {
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.remove('lazy');
                imageObserver.unobserve(img);
            }
        });
    });

    const lazyImages = document.querySelectorAll('img.lazy');
    lazyImages.forEach(img => imageObserver.observe(img));
}

// ========== 8. CONSOLE WELCOME MESSAGE ==========
console.log(
    '%c🎨 Zero-Based Admin Panel',
    'font-size: 20px; font-weight: bold; color: #e6c547; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);'
);
console.log(
    '%cModern • Accessible • Performant',
    'font-size: 14px; color: #94a3b8; font-style: italic;'
);
console.log(
    '%cPowered by Pure HTML, CSS & JavaScript',
    'font-size: 12px; color: #64748b;'
);
