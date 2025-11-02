# Secret Rotation Procedures

**Last Updated:** 2025-11-01
**Phase:** 20 - Security Hardening
**Status:** Production Ready

---

## Table of Contents

1. [Overview](#overview)
2. [Rotation Schedule](#rotation-schedule)
3. [Django SECRET_KEY Rotation](#django-secret_key-rotation)
4. [Database Credentials Rotation](#database-credentials-rotation)
5. [API Keys Rotation](#api-keys-rotation)
6. [SSL/TLS Certificate Renewal](#ssltls-certificate-renewal)
7. [VAPID Keys Rotation](#vapid-keys-rotation)
8. [Emergency Rotation](#emergency-rotation)
9. [Audit Trail](#audit-trail)

---

## Overview

**Purpose:** This document outlines procedures for rotating secrets and credentials to maintain security posture.

**Key Principles:**
- **Zero Downtime:** Rotate secrets without service interruption
- **Audit Trail:** Log all rotation activities
- **Validation:** Test new secrets before full deployment
- **Rollback Plan:** Have a plan to revert if rotation fails

**Responsibility:**
- **Security Team:** Approve and oversee rotations
- **DevOps Team:** Execute rotations
- **Development Team:** Update application code if needed

---

## Rotation Schedule

### Regular Rotations (Scheduled)

| Secret Type | Frequency | Responsible | Automated? |
|------------|-----------|-------------|------------|
| Django SECRET_KEY | Annually | DevOps | No |
| Database Passwords | Quarterly | DevOps | No |
| API Keys | As needed | DevOps | No |
| SSL/TLS Certificates | Auto-renew (90 days) | DevOps | Yes (Let's Encrypt) |
| VAPID Keys | Annually | DevOps | No |
| Redis Password | Quarterly | DevOps | No |
| SMTP Passwords | Quarterly | DevOps | No |

### Trigger Events (Immediate Rotation)

Rotate immediately if:
- ✅ Secret exposed in public repository
- ✅ Employee with access leaves company
- ✅ Suspected breach or compromise
- ✅ Vulnerability discovered in secret storage
- ✅ Compliance requirement triggered

---

## Django SECRET_KEY Rotation

**Risk Level:** HIGH
**Estimated Time:** 30 minutes
**Downtime:** None (if done correctly)

### What SECRET_KEY is Used For:
- Session signing
- CSRF token generation
- Password reset tokens
- Cryptographic signing

**⚠️ Impact of Rotation:**
- Active sessions invalidated (users logged out)
- CSRF tokens invalidated
- Password reset links invalidated
- Signed cookies invalidated

### Procedure

#### Step 1: Generate New SECRET_KEY

```bash
# Generate new key
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Example output:
# django-insecure-new-key-abc123xyz789...
```

**Store securely:** Add to password manager, vault, or secrets management service.

---

#### Step 2: Enable Multi-Key Support (Recommended)

Edit `project/settings/base.py` to support multiple keys:

```python
# Old way (single key)
SECRET_KEY = config("SECRET_KEY")

# New way (multiple keys for zero-downtime rotation)
SECRET_KEY = config("SECRET_KEY")  # Primary key
OLD_SECRET_KEYS = config(
    "OLD_SECRET_KEYS",
    default="",
    cast=lambda v: [s.strip() for s in v.split(",") if s.strip()]
)

# Django 4.2+ supports SECRET_KEY_FALLBACKS
# https://docs.djangoproject.com/en/5.1/ref/settings/#secret-key-fallbacks
SECRET_KEY_FALLBACKS = OLD_SECRET_KEYS
```

---

#### Step 3: Deploy New Key with Fallback

Update `.env` file:

```bash
# Primary key (new)
SECRET_KEY=django-insecure-new-key-abc123xyz789...

# Fallback keys (old keys, comma-separated)
OLD_SECRET_KEYS=django-insecure-old-key-previous-key,django-insecure-very-old-key
```

**Deploy:**
```bash
# Staging
git checkout staging
# Update .env on staging server
systemctl restart gunicorn-staging

# Production (after testing)
git checkout main
# Update .env on production server
systemctl restart gunicorn
```

---

#### Step 4: Monitor and Validate

```bash
# Check logs for errors
tail -f /var/log/django/django.log

# Test login
curl -X POST https://example.com/login/ -d "username=test&password=test"

# Test CSRF
curl -X GET https://example.com/contact/ | grep csrfmiddlewaretoken
```

**Wait period:** Keep fallback keys for 7-14 days to allow active sessions to expire.

---

#### Step 5: Remove Fallback Keys

After waiting period:

```bash
# Remove OLD_SECRET_KEYS from .env
SECRET_KEY=django-insecure-new-key-abc123xyz789...
# OLD_SECRET_KEYS removed
```

**Deploy again:**
```bash
systemctl restart gunicorn
```

---

### Rollback Plan

If rotation causes issues:

```bash
# Revert to old key
SECRET_KEY=django-insecure-old-key-previous-key
OLD_SECRET_KEYS=  # Empty

# Redeploy
systemctl restart gunicorn
```

---

## Database Credentials Rotation

**Risk Level:** CRITICAL
**Estimated Time:** 45-60 minutes
**Downtime:** None (with proper planning)

### Procedure

#### Step 1: Create New Database User

```sql
-- PostgreSQL
CREATE USER new_portfolio_user WITH PASSWORD 'new_strong_password_here';
GRANT ALL PRIVILEGES ON DATABASE portfolio_db TO new_portfolio_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO new_portfolio_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO new_portfolio_user;

-- MySQL
CREATE USER 'new_portfolio_user'@'%' IDENTIFIED BY 'new_strong_password_here';
GRANT ALL PRIVILEGES ON portfolio_db.* TO 'new_portfolio_user'@'%';
FLUSH PRIVILEGES;
```

---

#### Step 2: Test New Credentials

```bash
# Test connection
psql -h localhost -U new_portfolio_user -d portfolio_db -c "SELECT 1;"

# Update .env (staging first)
DATABASE_URL=postgresql://new_portfolio_user:new_password@localhost:5432/portfolio_db
```

---

#### Step 3: Deploy to Staging

```bash
# Update staging .env
DATABASE_URL=postgresql://new_portfolio_user:new_password@host/portfolio_db

# Restart services
systemctl restart gunicorn-staging
systemctl restart celery-staging

# Validate
python manage.py check --database default
python manage.py migrate --check
```

---

#### Step 4: Deploy to Production

```bash
# Update production .env
DATABASE_URL=postgresql://new_portfolio_user:new_password@host/portfolio_db

# Rolling restart (zero downtime)
for server in prod-1 prod-2 prod-3; do
    ssh $server "systemctl restart gunicorn"
    sleep 30  # Wait for health checks
done
```

---

#### Step 5: Revoke Old User (After Validation)

Wait 24-48 hours, then:

```sql
-- PostgreSQL
REVOKE ALL PRIVILEGES ON DATABASE portfolio_db FROM old_portfolio_user;
DROP USER old_portfolio_user;

-- MySQL
REVOKE ALL PRIVILEGES ON portfolio_db.* FROM 'old_portfolio_user'@'%';
DROP USER 'old_portfolio_user'@'%';
```

---

## API Keys Rotation

**Risk Level:** MEDIUM-HIGH
**Estimated Time:** 15-30 minutes per key

### Procedure

#### PageSpeed API Key

1. **Generate New Key:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - APIs & Services → Credentials
   - Create Credentials → API Key
   - Restrict key to PageSpeed Insights API

2. **Update Environment:**
   ```bash
   PAGESPEED_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXX
   ```

3. **Test:**
   ```bash
   python manage.py analyze_performance --url https://example.com
   ```

4. **Delete Old Key:**
   - Google Cloud Console → Credentials
   - Delete old API key

---

#### SendGrid/SMTP Credentials

1. **Generate New API Key:**
   - SendGrid Dashboard → Settings → API Keys
   - Create API Key → Full Access

2. **Update Environment:**
   ```bash
   EMAIL_HOST_PASSWORD=SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

3. **Test:**
   ```bash
   python manage.py sendtestemail admin@example.com
   ```

4. **Delete Old Key:**
   - SendGrid Dashboard → Delete old API key

---

## SSL/TLS Certificate Renewal

**Risk Level:** MEDIUM
**Estimated Time:** 5 minutes (automated)

### Let's Encrypt Auto-Renewal

**Setup (one-time):**

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d example.com -d www.example.com

# Auto-renewal cron job (already configured)
# Certificate renews automatically 30 days before expiry
sudo certbot renew --dry-run  # Test renewal
```

**Monitor Expiry:**

```bash
# Check expiry date
sudo certbot certificates

# Setup monitoring alert (30 days before expiry)
# Add to monitoring system (e.g., Sentry, Uptime Robot)
```

---

### Manual Certificate Renewal

If auto-renewal fails:

```bash
# Force renewal
sudo certbot renew --force-renewal

# Restart nginx
sudo systemctl reload nginx

# Verify
curl -I https://example.com | grep "HTTP/2 200"
openssl s_client -connect example.com:443 -servername example.com | grep "Verify return code"
```

---

## VAPID Keys Rotation

**Risk Level:** LOW-MEDIUM
**Estimated Time:** 20 minutes

**⚠️ Impact:** All existing push notification subscriptions will be invalidated. Users must re-subscribe.

### Procedure

#### Step 1: Generate New VAPID Keys

```bash
python manage.py generate_vapid_keys

# Output:
# VAPID_PUBLIC_KEY=BHxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# VAPID_PRIVATE_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

#### Step 2: Update Environment

```bash
# Update .env
VAPID_PUBLIC_KEY=BHxxxx-new-public-key-xxxx
VAPID_PRIVATE_KEY=xxxx-new-private-key-xxxx
VAPID_ADMIN_EMAIL=admin@example.com
```

---

#### Step 3: Update Service Worker

Edit `static/js/sw.js`:

```javascript
// Update public key
const applicationServerKey = 'BHxxxx-new-public-key-xxxx';
```

---

#### Step 4: Deploy and Clear Subscriptions

```bash
# Deploy
git add .
git commit -m "chore: Rotate VAPID keys"
git push

# Clear old subscriptions (they're invalid now)
python manage.py shell
>>> from apps.main.models import PushSubscription
>>> PushSubscription.objects.all().delete()
```

---

#### Step 5: Notify Users

Send email/notification:

> "We've upgraded our push notification system. Please visit Settings → Notifications and re-enable push notifications."

---

## Emergency Rotation

**Scenario:** Secret exposed in public GitHub repository

### Immediate Actions (within 1 hour)

1. **Revoke Exposed Secret:**
   - Database password: Create new user, revoke old
   - API key: Delete immediately from provider
   - SECRET_KEY: Generate new, deploy with fallback

2. **Deploy New Secrets:**
   ```bash
   # Staging (immediate)
   ./scripts/emergency_rotate.sh staging

   # Production (after 5-min validation)
   ./scripts/emergency_rotate.sh production
   ```

3. **Audit Access:**
   ```bash
   # Check database logs
   SELECT * FROM pg_stat_activity WHERE usename = 'compromised_user';

   # Check application logs
   grep "compromised_key" /var/log/django/*.log
   ```

4. **Notify Stakeholders:**
   - Security team
   - Management
   - Compliance (if required)

---

### Post-Incident (within 24 hours)

1. **Root Cause Analysis:**
   - How was secret exposed?
   - Who had access?
   - What data was accessed?

2. **Preventive Measures:**
   - Add secret scanning to CI/CD
   - Update `.gitignore`
   - Train team on secret management

3. **Documentation:**
   - Incident report
   - Lessons learned
   - Update procedures

---

## Audit Trail

### Logging Rotations

All secret rotations must be logged:

```python
# Django admin log
from django.contrib.admin.models import LogEntry, CHANGE

LogEntry.objects.create(
    user_id=request.user.id,
    content_type_id=ContentType.objects.get_for_model(User).id,
    object_id=1,
    object_repr="Secret Rotation",
    action_flag=CHANGE,
    change_message="Rotated Django SECRET_KEY - Ticket #12345"
)
```

---

### Rotation Log Template

File: `logs/secret_rotations.log`

```
Date: 2025-11-01 14:30:00 UTC
Type: Django SECRET_KEY
Performed By: devops@example.com
Reason: Scheduled quarterly rotation
Old Key Hash: sha256:abc123...
New Key Hash: sha256:xyz789...
Ticket: JIRA-12345
Rollback Plan: Documented in ticket
Status: SUCCESS
Validation: Login tested, CSRF tested, sessions working
```

---

## References

- [Django SECRET_KEY Documentation](https://docs.djangoproject.com/en/5.1/ref/settings/#secret-key)
- [Django SECRET_KEY_FALLBACKS](https://docs.djangoproject.com/en/5.1/ref/settings/#secret-key-fallbacks)
- [OWASP Key Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Key_Management_Cheat_Sheet.html)
- [PostgreSQL User Management](https://www.postgresql.org/docs/current/user-manag.html)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)

---

## Checklist: SECRET_KEY Rotation

- [ ] Generate new SECRET_KEY
- [ ] Store in password manager/vault
- [ ] Update staging `.env` with new key + fallback
- [ ] Deploy to staging
- [ ] Test login, CSRF, sessions
- [ ] Update production `.env` with new key + fallback
- [ ] Deploy to production
- [ ] Monitor for 7-14 days
- [ ] Remove fallback keys
- [ ] Update documentation
- [ ] Log rotation in audit trail

---

**Document Maintenance:**
- Review after each rotation
- Update procedures based on lessons learned
- Annual review for compliance
