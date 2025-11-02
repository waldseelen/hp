# Authentication & Authorization Security - Phase 2 Week 1

## 🔐 Overview

This document outlines the security improvements implemented in Phase 2 Week 1 to protect authentication and authorization mechanisms against OWASP Top 10 threats.

## ✅ Implemented Security Measures

### 1. Rate Limiting for Brute-Force Protection

**Threat Mitigated:** A07:2021 – Identification and Authentication Failures

**Implementation:**
- **Middleware:** `apps/core/middleware/rate_limiting.py`
- **Configuration:** `project/settings.py` → `RATE_LIMIT_CONFIG`

**Features:**
- Per-IP rate limiting (tracks failed login attempts by IP address)
- Per-username rate limiting (tracks failed attempts by username)
- Configurable thresholds:
  - `MAX_LOGIN_ATTEMPTS`: 5 attempts
  - `LOCKOUT_DURATION`: 900 seconds (15 minutes)
  - `ATTEMPT_WINDOW`: 300 seconds (5 minutes)
- Automatic lockout after threshold breach
- Exponential backoff (future enhancement)
- Exempt IPs for localhost/testing

**Protected Endpoints:**
- `/admin/login/`
- `/api/auth/login/`
- `/api/auth/token/`
- `/accounts/login/`
- `/password-reset/`
- `/api/auth/register/`

**Example Configuration (.env):**
```bash
RATE_LIMIT_MAX_ATTEMPTS=5
RATE_LIMIT_LOCKOUT_DURATION=900
RATE_LIMIT_ATTEMPT_WINDOW=300
```

**Usage:**
```python
from apps.core.middleware.rate_limiting import AuthenticationRateLimiter

rate_limiter = AuthenticationRateLimiter()

# Check rate limit
is_allowed, error_message = rate_limiter.check_rate_limit(ip_address, username)

if not is_allowed:
    return JsonResponse({'error': error_message}, status=429)

# Record failed attempt
rate_limiter.record_failed_attempt(ip_address, username)

# Reset after successful login
rate_limiter.reset_attempts(ip_address, username)
```

---

### 2. Enhanced Session Security

**Threat Mitigated:** A01:2021 – Broken Access Control, A07:2021 – Identification and Authentication Failures

**Implementation:**
- **File:** `project/settings.py`

**Settings:**
```python
# Prevent JavaScript access to session cookies (XSS protection)
SESSION_COOKIE_HTTPONLY = True

# Require HTTPS for session cookies (production)
SESSION_COOKIE_SECURE = True  # Enable in production

# CSRF protection via SameSite attribute
SESSION_COOKIE_SAMESITE = 'Lax'

# Session timeout
SESSION_COOKIE_AGE = 3600  # 1 hour
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
```

**Benefits:**
- **HTTPOnly:** Prevents XSS attacks from stealing session cookies
- **Secure:** Ensures cookies only transmitted over HTTPS
- **SameSite=Lax:** Prevents CSRF attacks by restricting cross-site cookie sending
- **Short Session Lifetime:** Reduces window for session hijacking

---

### 3. Enhanced Password Policy

**Threat Mitigated:** A07:2021 – Identification and Authentication Failures

**Implementation:**
- **File:** `project/settings.py`

**Password Requirements:**
- Minimum length: 12 characters (up from Django default 8)
- Must not be too similar to username/email
- Cannot be a common password (e.g., "password123")
- Cannot be entirely numeric

**Configuration:**
```python
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {
            "min_length": 12,
        },
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]
```

**Example Strong Password:**
```
MyVeryStr0ng!P@ssw0rd123
```

---

### 4. CSRF Protection (Enhanced)

**Threat Mitigated:** A01:2021 – Broken Access Control

**Implementation:**
- **File:** `project/settings.py`

**Settings:**
```python
# CSRF cookie security
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = True  # Enable in production
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_AGE = 31449600  # 1 year
```

**Built-in Django Protection:**
- All POST/PUT/DELETE requests require valid CSRF token
- Middleware: `django.middleware.csrf.CsrfViewMiddleware`
- Automatic token generation in forms

---

### 5. SSL/HTTPS Enforcement (Production)

**Threat Mitigated:** A02:2021 – Cryptographic Failures

**Implementation:**
- **File:** `project/settings.py`

**Settings:**
```python
# Redirect HTTP to HTTPS
SECURE_SSL_REDIRECT = os.environ.get("SECURE_SSL_REDIRECT", "False") == "True"

# Trust X-Forwarded-Proto header from proxy (Railway, Vercel)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# HTTP Strict Transport Security (HSTS)
SECURE_HSTS_SECONDS = 31536000  # 1 year in production
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

**Production .env:**
```bash
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
```

**What HSTS Does:**
- Forces browsers to always use HTTPS for your domain
- Prevents SSL stripping attacks
- `includeSubDomains`: Applies to all subdomains
- `preload`: Submit to browser HSTS preload list

---

### 6. Clickjacking Protection

**Threat Mitigated:** A05:2021 – Security Misconfiguration

**Implementation:**
- **File:** `project/settings.py`

**Settings:**
```python
# Prevent site from being embedded in iframes
X_FRAME_OPTIONS = 'DENY'
```

**What it Does:**
- Blocks your site from being loaded in `<iframe>`, `<frame>`, `<embed>`, or `<object>` tags
- Prevents clickjacking attacks where attackers trick users into clicking hidden elements

---

### 7. XSS Protection Headers

**Threat Mitigated:** A03:2021 – Injection (XSS)

**Implementation:**
- **File:** `project/settings.py`

**Settings:**
```python
# Enable browser XSS filter
SECURE_BROWSER_XSS_FILTER = True

# Prevent MIME-sniffing
SECURE_CONTENT_TYPE_NOSNIFF = True
```

---

### 8. Admin URL Obfuscation

**Threat Mitigated:** A05:2021 – Security Misconfiguration

**Implementation:**
- **File:** `project/settings.py`

**Settings:**
```python
# Configurable admin URL
ADMIN_URL = os.environ.get("ADMIN_URL", "admin/")
```

**Production .env:**
```bash
# Use non-standard admin URL
ADMIN_URL=my-secret-admin-panel-2024/
```

**Benefits:**
- Reduces automated bot attacks on `/admin/`
- Security through obscurity (not primary defense, but helpful)

---

## 📊 Security Test Coverage

**Test File:** `tests/security/test_authentication_security.py`

**Test Categories:**
1. **Rate Limiting Tests:**
   - Initial requests allowed
   - Exempt IPs bypass limiting
   - Lockout after max attempts
   - Per-username tracking
   - Reset after successful login
   - Lockout expiration

2. **Middleware Tests:**
   - Non-protected paths allowed
   - GET requests ignored
   - POST to protected path rate limited
   - Client IP extraction
   - Username extraction

3. **Session Security Tests:**
   - HTTPOnly flag
   - SameSite attribute
   - Secure flag (production)

4. **Password Policy Tests:**
   - Minimum length enforcement
   - Common password rejection
   - Strong password acceptance

5. **CSRF Protection Tests:**
   - Middleware active
   - POST without token rejected

6. **Clickjacking Tests:**
   - X-Frame-Options header

7. **Authentication Backend Tests:**
   - Restricted admin backend
   - Rate limiting integration

**Run Tests:**
```bash
# All security tests
pytest tests/security/test_authentication_security.py -v

# Specific test class
pytest tests/security/test_authentication_security.py::TestAuthenticationRateLimiter -v

# With coverage
pytest tests/security/ --cov=apps.core.middleware --cov-report=html
```

---

## 🚀 Deployment Checklist

### Development Environment
- [x] Rate limiting configured with development settings
- [x] Session/CSRF cookies configured (Secure=False)
- [x] Admin URL at default `/admin/`

### Production Environment
- [ ] Enable SSL/HTTPS enforcement:
  ```bash
  SECURE_SSL_REDIRECT=True
  SECURE_HSTS_SECONDS=31536000
  ```
- [ ] Enable secure cookies:
  ```bash
  SESSION_COOKIE_SECURE=True
  CSRF_COOKIE_SECURE=True
  ```
- [ ] Configure custom admin URL:
  ```bash
  ADMIN_URL=your-secret-admin-url/
  ```
- [ ] Set strong admin credentials:
  ```bash
  ALLOWED_ADMIN_EMAIL=your-email@domain.com
  ALLOWED_ADMIN_PASSWORD_HASH=pbkdf2_sha256$...
  ```
- [ ] Configure rate limiting for production:
  ```bash
  RATE_LIMIT_MAX_ATTEMPTS=3  # Stricter in prod
  RATE_LIMIT_LOCKOUT_DURATION=1800  # 30 minutes
  ```

---

## 🔍 Security Audit Checklist

- [x] **A01: Broken Access Control**
  - [x] CSRF protection enabled
  - [x] Session management secure
  - [x] Proper authentication required

- [x] **A02: Cryptographic Failures**
  - [x] HTTPS enforcement configured
  - [x] HSTS headers configured
  - [x] Secure cookie flags

- [x] **A03: Injection**
  - [x] XSS filter enabled
  - [x] Content-Type nosniff
  - [ ] CSP headers (Phase 2 Week 2)

- [x] **A05: Security Misconfiguration**
  - [x] Clickjacking protection
  - [x] Admin URL obfuscation
  - [x] Security headers configured

- [x] **A07: Identification and Authentication Failures**
  - [x] Rate limiting implemented
  - [x] Strong password policy
  - [x] Session security hardened
  - [x] Lockout mechanism

- [ ] **A08: Software and Data Integrity Failures**
  - [ ] (Phase 2 Week 2)

- [ ] **A09: Security Logging and Monitoring Failures**
  - [ ] (Phase 2 Week 2)

- [ ] **A10: Server-Side Request Forgery (SSRF)**
  - [ ] (Phase 2 Week 2)

---

## 📈 Performance Impact

**Estimated Overhead:**
- Rate limiting middleware: <1ms per request (cache lookups)
- Session security: 0ms (header-only changes)
- Password validation: <10ms during registration/password change

**Cache Usage:**
- Rate limiting stores attempts in Django cache
- Memory footprint: ~100 bytes per IP/username combination
- TTL: 300-900 seconds (automatic cleanup)

---

## 🔄 Next Steps (Phase 2 Week 2)

1. **Input Validation & Sanitization**
   - Review all forms and APIs
   - Add XSS protection for user inputs
   - Sanitize database queries

2. **API Security**
   - JWT authentication
   - API key management
   - Throttling per user/token

3. **Security Headers & CSP**
   - Content Security Policy implementation
   - Additional security headers
   - Subresource Integrity (SRI)

---

## 📚 References

- [OWASP Top 10 2021](https://owasp.org/Top10/)
- [Django Security Documentation](https://docs.djangoproject.com/en/5.0/topics/security/)
- [Mozilla Web Security Guidelines](https://infosec.mozilla.org/guidelines/web_security)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/)

---

**Last Updated:** November 2, 2025
**Status:** ✅ Phase 2 Week 1 Task 1 Complete
