from .base import *

# SECURITY WARNING: keep the secret key used in production secret!
# Consider loading from environment variables
DEBUG = False

# Replace with your actual domain name
ALLOWED_HOSTS = ['*.example.com'] # Daha güvenli bir başlangıç için

# Production Security Settings
# ============================

# HTTPS/SSL Configuration
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Secure Cookies
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# Additional Security Headers
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'

# Enable rate limiting in production
ENABLE_RATE_LIMIT_IN_DEBUG = False
