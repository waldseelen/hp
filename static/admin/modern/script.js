/**
 * Modern Admin Panel Scripts
 * Handles sidebar toggling and form validation
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Sidebar Toggle Logic
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');

    if (sidebar && sidebarToggle) {
        sidebarToggle.addEventListener('click', () => {
            sidebar.classList.toggle('collapsed');

            // Save state to localStorage
            const isCollapsed = sidebar.classList.contains('collapsed');
            localStorage.setItem('sidebarCollapsed', isCollapsed);
        });

        // Restore state
        const savedState = localStorage.getItem('sidebarCollapsed');
        if (savedState === 'true') {
            sidebar.classList.add('collapsed');
        }
    }

    // 2. Form Validation Logic
    const loginForm = document.getElementById('loginForm');

    if (loginForm) {
        loginForm.addEventListener('submit', (e) => {
            e.preventDefault();
            let isValid = true;

            // Reset errors
            const inputs = loginForm.querySelectorAll('.form-input');
            inputs.forEach(input => {
                input.classList.remove('error');
            });

            // Validate Email
            const emailInput = document.getElementById('email');
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

            if (!emailRegex.test(emailInput.value)) {
                emailInput.classList.add('error');
                isValid = false;
            }

            // Validate Password
            const passwordInput = document.getElementById('password');
            if (passwordInput.value.length < 6) {
                passwordInput.classList.add('error');
                isValid = false;
            }

            // Simulate Login
            if (isValid) {
                const btn = loginForm.querySelector('button[type="submit"]');
                const originalText = btn.innerHTML;

                btn.disabled = true;
                btn.innerHTML = 'Giriş Yapılıyor...';

                setTimeout(() => {
                    alert('Giriş Başarılı! (Demo)');
                    btn.disabled = false;
                    btn.innerHTML = originalText;
                    // Redirect logic would go here
                }, 1500);
            }
        });

        // Real-time validation removal
        const inputs = loginForm.querySelectorAll('.form-input');
        inputs.forEach(input => {
            input.addEventListener('input', () => {
                if (input.classList.contains('error')) {
                    input.classList.remove('error');
                }
            });
        });
    }
});
