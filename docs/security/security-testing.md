# Security Testing Guide

## Overview

Comprehensive security testing guide covering:
- Automated security scanning (Bandit, Safety)
- Manual security testing
- Penetration testing guidelines
- Security audit process

## Quick Start

### Install Security Tools

```bash
# Install security testing tools
pip install bandit safety pytest-security

# Or using requirements
pip install -r requirements/security.txt
```

### Run Security Tests

```bash
# Run all security tests
python scripts/security_test.py

# Verbose output
python scripts/security_test.py --verbose

# Run individual tools
bandit -r . -ll
safety check
pytest tests/security/ -v
```

## Automated Security Testing

### 1. Bandit (Python Code Security)

**What it checks:**
- Hardcoded passwords
- SQL injection vulnerabilities
- Shell injection
- Insecure deserialization
- XML vulnerabilities
- Assert usage in production

**Run Bandit:**

```bash
# Basic scan
bandit -r .

# Only medium/high severity
bandit -r . -ll

# Generate JSON report
bandit -r . -f json -o bandit-report.json

# Exclude directories
bandit -r . --exclude ./venv,./env,./node_modules
```

**Example output:**
```
>> Issue: [B105:hardcoded_password_string] Possible hardcoded password: 'secret123'
   Severity: Low   Confidence: Medium
   Location: ./config/settings.py:15
```

**Common issues and fixes:**

| Issue | Fix |
|-------|-----|
| Hardcoded password | Use environment variables |
| SQL injection | Use parameterized queries |
| Shell injection | Use subprocess with list arguments |
| Assert in production | Use explicit exceptions |

### 2. Safety (Dependency Vulnerabilities)

**What it checks:**
- Known vulnerabilities in dependencies
- Outdated packages with security fixes
- CVE database matching

**Run Safety:**

```bash
# Check dependencies
safety check

# JSON output
safety check --json

# Check specific file
safety check --file requirements.txt

# Continue on error
safety check --continue-on-error
```

**Example output:**
```
╒══════════════════════════════════════════════════════════════════════════════╕
│                                                                              │
│                               /$$$$$$            /$$                         │
│                              /$$__  $$          | $$                         │
│           /$$$$$$$  /$$$$$$ | $$  \__//$$$$$$  /$$$$$$   /$$   /$$          │
│          /$$_____/ |____  $$| $$$$   /$$__  $$|_  $$_/  | $$  | $$          │
│         |  $$$$$$   /$$$$$$$| $$_/  | $$$$$$$$  | $$    | $$  | $$          │
│          \____  $$ /$$__  $$| $$    | $$_____/  | $$ /$$| $$  | $$          │
│          /$$$$$$$/|  $$$$$$$| $$    |  $$$$$$$  |  $$$$/|  $$$$$$$          │
│         |_______/  \_______/|__/     \_______/   \___/   \____  $$          │
│                                                          /$$  | $$          │
│                                                          |  $$$$$$/          │
│  by pyup.io                                              \______/           │
│                                                                              │
╞══════════════════════════════════════════════════════════════════════════════╡
│ REPORT                                                                       │
│ checked 45 packages, using free DB (updated once a month)                   │
╞════════════════════════════╤═══════════╤══════════════════════════╤══════════╡
│ package                    │ installed │ affected                 │ ID       │
╞════════════════════════════╧═══════════╧══════════════════════════╧══════════╡
│ django                     │ 4.1.0     │ <4.1.13                  │ 58755    │
╘══════════════════════════════════════════════════════════════════════════════╛
```

**Fix vulnerabilities:**
```bash
# Upgrade affected packages
pip install --upgrade django

# Or update requirements.txt and reinstall
pip install -r requirements.txt --upgrade
```

### 3. Security Test Suite

**Run security tests:**

```bash
# All security tests
pytest tests/security/ -v

# Specific test file
pytest tests/security/test_authentication.py -v

# With coverage
pytest tests/security/ --cov=apps --cov-report=html

# Stop on first failure
pytest tests/security/ -x
```

**Test categories:**
- Authentication security
- Authorization checks
- Input validation
- Session security
- CSRF protection
- XSS prevention
- SQL injection prevention
- File upload security
- Rate limiting
- JWT authentication
- API security
- Security headers
- GDPR compliance

## Manual Security Testing

### 1. Authentication Testing

**Test cases:**

```bash
# Test weak passwords
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "password": "123"}'
# Expected: 400 - Password too weak

# Test brute force protection
for i in {1..100}; do
  curl -X POST http://localhost:8000/api/auth/login/ \
    -H "Content-Type: application/json" \
    -d '{"username": "admin", "password": "wrong"}'
done
# Expected: 429 - Too many requests after 5 attempts

# Test session fixation
# 1. Get session ID before login
# 2. Login
# 3. Verify session ID changed
```

### 2. Authorization Testing

**Test cases:**

```bash
# Test unauthorized access
curl -X GET http://localhost:8000/api/admin/users/
# Expected: 401 - Unauthorized

# Test privilege escalation
curl -X GET http://localhost:8000/api/admin/users/ \
  -H "Authorization: Bearer <user_token>"
# Expected: 403 - Forbidden

# Test horizontal privilege escalation
curl -X GET http://localhost:8000/api/users/999/profile/ \
  -H "Authorization: Bearer <user1_token>"
# Expected: 403 - Can only access own profile
```

### 3. Input Validation Testing

**XSS Testing:**

```bash
# Test XSS in form input
curl -X POST http://localhost:8000/api/contact/ \
  -H "Content-Type: application/json" \
  -d '{"message": "<script>alert(1)</script>"}'
# Expected: 400 - Invalid input or sanitized

# Test XSS in URL parameters
curl "http://localhost:8000/search?q=<script>alert(1)</script>"
# Expected: Sanitized output or blocked
```

**SQL Injection Testing:**

```bash
# Test SQL injection in search
curl "http://localhost:8000/api/search?q=' OR '1'='1"
# Expected: No SQL error, sanitized query

# Test SQL injection in authentication
curl -X POST http://localhost:8000/api/auth/login/ \
  -d '{"username": "admin", "password": "' OR '1'='1"}'
# Expected: 401 - Invalid credentials
```

### 4. Security Headers Testing

```bash
# Test security headers
curl -I https://yourdomain.com/

# Expected headers:
# Strict-Transport-Security: max-age=31536000; includeSubDomains
# Content-Security-Policy: default-src 'self'
# X-Content-Type-Options: nosniff
# X-Frame-Options: DENY
# Referrer-Policy: strict-origin-when-cross-origin
```

**Online tools:**
- https://securityheaders.com/
- https://observatory.mozilla.org/

### 5. CSRF Testing

```bash
# Test CSRF protection
curl -X POST http://localhost:8000/api/profile/update/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Hacker"}'
# Expected: 403 - CSRF token missing

# Test CSRF with wrong token
curl -X POST http://localhost:8000/api/profile/update/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: wrong_token" \
  -d '{"name": "Hacker"}'
# Expected: 403 - CSRF token invalid
```

## Penetration Testing

### OWASP ZAP

**Install OWASP ZAP:**
```bash
# Download from https://www.zaproxy.org/download/
# Or use Docker
docker pull owasp/zap2docker-stable
```

**Run automated scan:**

```bash
# Basic scan
docker run -t owasp/zap2docker-stable zap-baseline.py \
  -t http://localhost:8000

# Full scan
docker run -t owasp/zap2docker-stable zap-full-scan.py \
  -t http://localhost:8000

# API scan
docker run -t owasp/zap2docker-stable zap-api-scan.py \
  -t http://localhost:8000/api/openapi.json \
  -f openapi
```

**ZAP checks:**
- SQL injection
- XSS (reflected, stored, DOM-based)
- CSRF
- Insecure authentication
- Session management
- Security misconfigurations
- Sensitive data exposure
- XML external entities (XXE)
- Broken access control
- Security headers

### Manual Penetration Testing

**1. Reconnaissance:**
```bash
# Check robots.txt
curl http://localhost:8000/robots.txt

# Check for exposed files
curl http://localhost:8000/.git/
curl http://localhost:8000/.env
curl http://localhost:8000/admin/

# Port scanning
nmap -sV localhost
```

**2. Vulnerability Assessment:**
```bash
# Test for open redirects
curl "http://localhost:8000/redirect?url=https://evil.com"

# Test for SSRF
curl -X POST http://localhost:8000/api/fetch/ \
  -d '{"url": "http://localhost:22"}'

# Test for file inclusion
curl "http://localhost:8000/download?file=../../etc/passwd"
```

**3. Exploitation:**
- Attempt to exploit found vulnerabilities
- Document proof of concept
- Assess impact and severity
- Provide remediation steps

## Security Audit Checklist

### Pre-Deployment

- [ ] All dependencies updated to latest secure versions
- [ ] No critical/high vulnerabilities in Bandit report
- [ ] No vulnerabilities in Safety report
- [ ] All security tests passing
- [ ] SSL/TLS properly configured
- [ ] Security headers implemented
- [ ] CSRF protection enabled
- [ ] XSS protection implemented
- [ ] SQL injection protection verified
- [ ] Rate limiting configured
- [ ] Authentication secure (password policy, MFA)
- [ ] Authorization properly enforced
- [ ] Session management secure
- [ ] File upload restrictions in place
- [ ] Logging and monitoring configured
- [ ] Error messages don't leak sensitive info
- [ ] Debug mode disabled in production
- [ ] Secrets in environment variables
- [ ] .env file in .gitignore
- [ ] GDPR compliance implemented

### Post-Deployment

- [ ] Penetration test completed
- [ ] No critical issues in pen test report
- [ ] Security headers verified (securityheaders.com)
- [ ] SSL/TLS configuration verified (ssllabs.com)
- [ ] Monitoring and alerting active
- [ ] Incident response plan in place
- [ ] Security training completed
- [ ] Regular security audits scheduled

## Continuous Security

### CI/CD Integration

```yaml
# .github/workflows/security.yml
name: Security Tests

on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install bandit safety pytest
          pip install -r requirements.txt

      - name: Run Bandit
        run: bandit -r . -ll --exclude ./venv,./env

      - name: Run Safety
        run: safety check

      - name: Run Security Tests
        run: pytest tests/security/ -v
```

### Monthly Security Tasks

1. **Week 1:**
   - Update all dependencies
   - Run security scan
   - Review access controls

2. **Week 2:**
   - Review security logs
   - Check for new CVEs
   - Update security documentation

3. **Week 3:**
   - Penetration testing
   - Security training
   - Incident response drill

4. **Week 4:**
   - Security audit
   - Policy review
   - Generate security report

## Reporting Security Issues

### Internal Process

1. **Discovery:**
   - Document issue details
   - Assess severity (CVSS)
   - Determine impact

2. **Triage:**
   - Assign priority
   - Assign owner
   - Set deadline

3. **Remediation:**
   - Develop fix
   - Test fix
   - Deploy fix

4. **Verification:**
   - Verify fix works
   - Retest vulnerability
   - Update documentation

### External Reporting

If you discover a security vulnerability:

1. **DO NOT** create a public GitHub issue
2. Email security@yourdomain.com
3. Include:
   - Description of vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (optional)

## References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)
- [OWASP ZAP](https://www.zaproxy.org/)
- [Bandit Documentation](https://bandit.readthedocs.io/)
- [Safety Documentation](https://pyup.io/safety/)
- [Django Security](https://docs.djangoproject.com/en/stable/topics/security/)
- [CWE Database](https://cwe.mitre.org/)
- [CVE Database](https://cve.mitre.org/)
