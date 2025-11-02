# Security Headers Configuration Guide

## Overview

This guide covers the configuration and usage of security headers in the application, including Content Security Policy (CSP), HTTP Strict Transport Security (HSTS), and Subresource Integrity (SRI).

**OWASP Coverage**: A05 (Security Misconfiguration), A06 (Vulnerable and Outdated Components)

## Table of Contents

1. [Security Headers Overview](#security-headers-overview)
2. [Configuration](#configuration)
3. [Content Security Policy (CSP)](#content-security-policy-csp)
4. [HTTP Strict Transport Security (HSTS)](#http-strict-transport-security-hsts)
5. [Subresource Integrity (SRI)](#subresource-integrity-sri)
6. [Template Tags](#template-tags)
7. [Testing](#testing)
8. [Monitoring](#monitoring)
9. [Deployment Checklist](#deployment-checklist)

## Security Headers Overview

### Headers Implemented

| Header | Purpose | OWASP Coverage |
|--------|---------|----------------|
| Content-Security-Policy | Prevent XSS attacks | A03 (Injection) |
| Strict-Transport-Security | Enforce HTTPS | A05 (Security Misconfiguration) |
| X-Frame-Options | Prevent clickjacking | A05 |
| X-Content-Type-Options | Prevent MIME sniffing | A05 |
| Referrer-Policy | Control referrer information | A05 |
| Permissions-Policy | Restrict browser features | A05 |
| X-XSS-Protection | Legacy XSS protection | A03 |

### Architecture

```
Request Flow:
1. Request arrives
2. ContentSecurityPolicyMiddleware generates CSP nonce
3. View processes request
4. SecurityHeadersMiddleware adds security headers
5. HSTSMiddleware adds HSTS header (HTTPS only)
6. ContentSecurityPolicyMiddleware adds CSP header with nonce
7. Response sent to client
```

## Configuration

### settings.py

Add middleware to `MIDDLEWARE`:

```python
MIDDLEWARE = [
    # ... other middleware ...
    'apps.core.middleware.security_headers.SecurityHeadersMiddleware',
    'apps.core.middleware.security_headers.HSTSMiddleware',
    'apps.core.middleware.security_headers.ContentSecurityPolicyMiddleware',
    # ... other middleware ...
]
```

### Security Headers Settings

```python
# X-Frame-Options
X_FRAME_OPTIONS = 'DENY'  # or 'SAMEORIGIN'

# Referrer-Policy
REFERRER_POLICY = 'strict-origin-when-cross-origin'

# Permissions-Policy
PERMISSIONS_POLICY = (
    "accelerometer=(), "
    "camera=(), "
    "geolocation=(), "
    "gyroscope=(), "
    "magnetometer=(), "
    "microphone=(), "
    "payment=(), "
    "usb=()"
)
```

### HSTS Settings

```python
# HSTS Configuration
HSTS_MAX_AGE = 31536000  # 1 year in seconds
HSTS_INCLUDE_SUBDOMAINS = True
HSTS_PRELOAD = False  # Set to True when ready for preload list

# For production with HSTS preload:
# HSTS_MAX_AGE = 63072000  # 2 years (required for preload)
# HSTS_INCLUDE_SUBDOMAINS = True  # Required for preload
# HSTS_PRELOAD = True
```

### CSP Settings

```python
# Content Security Policy
CSP_REPORT_ONLY = False  # Set to True for testing
CSP_REPORT_URI = '/api/csp-report/'  # Optional: CSP violation reporting

CSP_DIRECTIVES = {
    'default-src': ["'self'"],
    'script-src': [
        "'self'",
        # Add trusted CDNs:
        # 'https://cdn.jsdelivr.net',
    ],
    'style-src': [
        "'self'",
        # Add trusted style sources:
        # 'https://fonts.googleapis.com',
    ],
    'img-src': ["'self'", "data:", "https:"],
    'font-src': ["'self'", "data:"],
    'connect-src': ["'self'"],
    'frame-ancestors': ["'none'"],
    'base-uri': ["'self'"],
    'form-action': ["'self'"],
    'upgrade-insecure-requests': [],
}
```

## Content Security Policy (CSP)

### What is CSP?

Content Security Policy is a security layer that helps detect and mitigate certain types of attacks, including Cross-Site Scripting (XSS) and data injection attacks.

### CSP Directives Explained

| Directive | Description | Example |
|-----------|-------------|---------|
| `default-src` | Fallback for other directives | `'self'` |
| `script-src` | Valid sources for JavaScript | `'self' 'nonce-{random}'` |
| `style-src` | Valid sources for CSS | `'self' 'nonce-{random}'` |
| `img-src` | Valid sources for images | `'self' data: https:` |
| `font-src` | Valid sources for fonts | `'self' data:` |
| `connect-src` | Valid sources for XHR, WebSocket | `'self'` |
| `frame-ancestors` | Who can embed this page | `'none'` |
| `base-uri` | Valid URLs for `<base>` element | `'self'` |
| `form-action` | Valid form submission targets | `'self'` |

### Using CSP Nonces

CSP nonces allow inline scripts and styles while maintaining security.

**In templates:**

```django
{% load security_tags %}

<!DOCTYPE html>
<html>
<head>
    {% csp_nonce as nonce %}
    <script nonce="{{ nonce }}">
        console.log('This inline script is allowed!');
    </script>
</head>
</html>
```

**In views:**

```python
from apps.core.middleware.security_headers import get_csp_nonce

def my_view(request):
    nonce = get_csp_nonce(request)
    return render(request, 'template.html', {'nonce': nonce})
```

### CSP Report-Only Mode

For testing CSP without breaking functionality:

```python
CSP_REPORT_ONLY = True
CSP_REPORT_URI = '/api/csp-report/'
```

Create a view to receive CSP reports:

```python
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
import logging

logger = logging.getLogger(__name__)

@csrf_exempt
def csp_report(request):
    """Receive and log CSP violation reports."""
    if request.method == 'POST':
        try:
            report = json.loads(request.body)
            logger.warning(f"CSP Violation: {report}")
            # Optionally store in database for analysis
        except Exception as e:
            logger.error(f"Failed to process CSP report: {e}")

    return JsonResponse({'status': 'ok'})
```

## HTTP Strict Transport Security (HSTS)

### What is HSTS?

HSTS tells browsers to only access the site via HTTPS, preventing protocol downgrade attacks.

### HSTS Configuration Levels

**Development:**
```python
HSTS_MAX_AGE = 300  # 5 minutes for testing
HSTS_INCLUDE_SUBDOMAINS = False
HSTS_PRELOAD = False
```

**Staging:**
```python
HSTS_MAX_AGE = 86400  # 1 day
HSTS_INCLUDE_SUBDOMAINS = True
HSTS_PRELOAD = False
```

**Production:**
```python
HSTS_MAX_AGE = 31536000  # 1 year
HSTS_INCLUDE_SUBDOMAINS = True
HSTS_PRELOAD = False
```

**Production with Preload:**
```python
HSTS_MAX_AGE = 63072000  # 2 years (required)
HSTS_INCLUDE_SUBDOMAINS = True  # Required
HSTS_PRELOAD = True
```

### HSTS Preload List

To submit your domain to the HSTS preload list:

1. Serve a valid certificate
2. Redirect from HTTP to HTTPS
3. Serve all subdomains over HTTPS
4. Set HSTS header with:
   - `max-age` of at least 31536000 seconds (1 year)
   - `includeSubDomains` directive
   - `preload` directive
5. Submit to: https://hstspreload.org/

**Warning**: Preload is a one-way process. Removal can take months!

## Subresource Integrity (SRI)

### What is SRI?

SRI allows browsers to verify that files fetched from CDNs haven't been tampered with.

### Using SRI with Template Tags

**Load CSS with SRI:**
```django
{% load security_tags %}

{% sri_style 'css/style.css' %}
{% sri_style 'css/print.css' media='print' %}
```

**Load JavaScript with SRI:**
```django
{% load security_tags %}

{% sri_script 'js/app.js' %}
{% sri_script 'js/vendor.js' async='async' %}
```

**Get integrity value only:**
```django
{% load security_tags %}

<script src="{% static 'js/app.js' %}"
        integrity="{% sri_integrity 'js/app.js' %}"
        crossorigin="anonymous"></script>
```

### Using SRI Programmatically

```python
from apps.core.middleware.security_headers import SubresourceIntegrityHelper

# Initialize helper
sri = SubresourceIntegrityHelper(algorithm='sha384')

# Generate hash for a file
integrity = sri.generate_hash('static/js/app.js')
# Returns: 'sha384-oqVuAfXRKap7fdgcCY5uykM6+R9GqQ8K/uxy9rx7HNQlGYl1kPzQho1wx4JwY8wC'

# Generate hashes for multiple files
files = ['static/js/app.js', 'static/css/style.css']
hashes = sri.generate_hashes_for_files(files)
# Returns: {'static/js/app.js': 'sha384-...', 'static/css/style.css': 'sha384-...'}

# Use different algorithm
sri_512 = SubresourceIntegrityHelper(algorithm='sha512')
integrity_512 = sri_512.generate_hash('static/js/app.js')
```

### SRI for CDN Resources

When using CDN resources, always use SRI:

```html
<script src="https://cdn.jsdelivr.net/npm/jquery@3.6.0/dist/jquery.min.js"
        integrity="sha384-vtXRMe3mGCbOeY7l30aIg8H9p3GdeSe4IFlP6G8JMa7o7lXvnz3GFKzPxzJdPfGK"
        crossorigin="anonymous"></script>
```

Get integrity hashes from:
- https://www.srihash.org/
- CDN documentation
- Generate manually with `SubresourceIntegrityHelper`

## Template Tags

### Available Tags

**Load the tags:**
```django
{% load security_tags %}
```

**Get CSP nonce:**
```django
{% csp_nonce as nonce %}
<script nonce="{{ nonce }}">...</script>
```

**Secure inline script:**
```django
{% secure_script %}
    console.log('Secure inline script');
{% endsecure_script %}
```

**Secure inline style:**
```django
{% secure_style %}
    body { background: #fff; }
{% endsecure_style %}
```

**Load script with SRI:**
```django
{% sri_script 'js/app.js' %}
{% sri_script 'js/vendor.js' async='async' defer='defer' %}
```

**Load style with SRI:**
```django
{% sri_style 'css/style.css' %}
{% sri_style 'css/print.css' media='print' %}
```

**Get integrity value:**
```django
{% sri_integrity 'js/app.js' %}
```

## Testing

### Test Security Headers

**Using curl:**
```bash
# Test all security headers
curl -I https://yourdomain.com

# Test HSTS (HTTPS only)
curl -I https://yourdomain.com | grep -i strict-transport

# Test CSP
curl -I https://yourdomain.com | grep -i content-security-policy
```

**Using online tools:**
- https://securityheaders.com/ - Comprehensive header analysis
- https://observatory.mozilla.org/ - Mozilla Observatory
- https://csp-evaluator.withgoogle.com/ - CSP evaluation

### Run Test Suite

```bash
# Run all security header tests
pytest tests/security/test_security_headers.py -v

# Run specific test class
pytest tests/security/test_security_headers.py::TestSecurityHeadersMiddleware -v

# Run with coverage
pytest tests/security/test_security_headers.py --cov=apps.core.middleware.security_headers
```

### Manual Testing

**Test CSP nonce generation:**
```python
from django.test import RequestFactory
from apps.core.middleware.security_headers import ContentSecurityPolicyMiddleware

factory = RequestFactory()
middleware = ContentSecurityPolicyMiddleware(lambda r: None)

request = factory.get('/')
middleware.process_request(request)

print(f"CSP Nonce: {request.csp_nonce}")
```

**Test SRI hash generation:**
```python
from apps.core.middleware.security_headers import SubresourceIntegrityHelper

sri = SubresourceIntegrityHelper()
integrity = sri.generate_hash('static/js/app.js')
print(f"Integrity: {integrity}")
```

## Monitoring

### Metrics to Track

1. **CSP Violations**
   - Count of violations
   - Most common violation types
   - Blocked URIs

2. **HSTS Usage**
   - HTTPS vs HTTP requests
   - HSTS header presence
   - Preload status

3. **Security Header Coverage**
   - Percentage of responses with all headers
   - Missing headers
   - Header value consistency

### Logging

```python
import logging

logger = logging.getLogger('security.headers')

# Configure logging in settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'security_file': {
            'class': 'logging.FileHandler',
            'filename': 'logs/security.log',
        },
    },
    'loggers': {
        'security.headers': {
            'handlers': ['security_file'],
            'level': 'INFO',
        },
    },
}
```

### CSP Violation Monitoring

Create a dashboard to track CSP violations:

```python
from django.db import models

class CSPViolation(models.Model):
    """Store CSP violation reports."""

    document_uri = models.URLField()
    violated_directive = models.CharField(max_length=255)
    blocked_uri = models.URLField()
    source_file = models.URLField(blank=True)
    line_number = models.IntegerField(null=True)
    column_number = models.IntegerField(null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['violated_directive', '-timestamp']),
        ]
```

## Deployment Checklist

### Pre-Deployment

- [ ] Configure all security headers in settings.py
- [ ] Set `CSP_REPORT_ONLY = True` for initial testing
- [ ] Set HSTS with low max-age (300 seconds) for testing
- [ ] Test CSP in report-only mode
- [ ] Generate SRI hashes for all static files
- [ ] Review CSP violation reports
- [ ] Test on staging environment

### Initial Deployment

- [ ] Set `CSP_REPORT_ONLY = False` (enforce CSP)
- [ ] Increase HSTS max-age to 1 day (86400)
- [ ] Monitor for issues
- [ ] Review security headers with online tools
- [ ] Verify SRI hashes are working

### Production Hardening

- [ ] Increase HSTS max-age to 1 year (31536000)
- [ ] Enable HSTS includeSubDomains
- [ ] Review and tighten CSP directives
- [ ] Remove unnecessary trusted sources from CSP
- [ ] Set up CSP violation monitoring
- [ ] Configure security header monitoring

### HSTS Preload (Optional)

- [ ] Set HSTS max-age to 2 years (63072000)
- [ ] Verify all subdomains support HTTPS
- [ ] Set `HSTS_PRELOAD = True`
- [ ] Submit to https://hstspreload.org/
- [ ] Monitor preload status

## Best Practices

### CSP Best Practices

1. **Start with report-only mode**
2. **Use nonces instead of 'unsafe-inline'**
3. **Avoid 'unsafe-eval' if possible**
4. **Use specific sources instead of wildcards**
5. **Monitor violations regularly**
6. **Update directives as needed**

### HSTS Best Practices

1. **Start with short max-age**
2. **Test thoroughly before long max-age**
3. **Enable includeSubDomains only when all subdomains support HTTPS**
4. **Consider preload implications carefully**
5. **Have a rollback plan**

### SRI Best Practices

1. **Use SRI for all CDN resources**
2. **Use SHA-384 or SHA-512 algorithms**
3. **Regenerate hashes on file changes**
4. **Include crossorigin="anonymous" attribute**
5. **Cache integrity hashes for performance**

## Troubleshooting

### Common Issues

**CSP blocks inline scripts:**
```
Solution: Use CSP nonces for inline scripts
{% load security_tags %}
{% csp_nonce as nonce %}
<script nonce="{{ nonce }}">...</script>
```

**HSTS not working:**
```
Check: Request must be HTTPS
Verify: curl -I https://yourdomain.com | grep -i strict-transport
```

**SRI hash mismatch:**
```
Solution: Regenerate hash after file changes
sri = SubresourceIntegrityHelper()
sri.clear_cache()
new_hash = sri.generate_hash('file.js')
```

**CSP violations from third-party scripts:**
```
Solution: Add trusted source to CSP directives
CSP_DIRECTIVES = {
    'script-src': ["'self'", 'https://trusted-cdn.com'],
}
```

## References

- [Content Security Policy Reference](https://content-security-policy.com/)
- [OWASP Secure Headers Project](https://owasp.org/www-project-secure-headers/)
- [MDN Web Security](https://developer.mozilla.org/en-US/docs/Web/Security)
- [HSTS Preload List](https://hstspreload.org/)
- [SRI Hash Generator](https://www.srihash.org/)
- [Security Headers Checker](https://securityheaders.com/)

## Support

For questions or issues:
- Review this documentation
- Check test files in `tests/security/test_security_headers.py`
- Review middleware code in `apps/core/middleware/security_headers.py`
- Check security logs in `logs/security.log`
