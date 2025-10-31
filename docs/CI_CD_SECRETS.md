# CI/CD Secrets Configuration Guide

## Required GitHub Secrets

To enable automated testing and deployment, configure these secrets in your GitHub repository:

**Settings → Secrets and variables → Actions → New repository secret**

---

## 1. Railway Deployment Secrets

### `RAILWAY_TOKEN`
**Purpose:** Authenticate with Railway for automated deployments

**How to get:**
```bash
# 1. Install Railway CLI
npm install -g @railway/cli

# 2. Login to Railway
railway login

# 3. Get project token
railway whoami
```

Or from Railway Dashboard:
1. Visit https://railway.app/account/tokens
2. Click "Create New Token"
3. Name: "GitHub Actions CI/CD"
4. Copy token

**Value format:** `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`

---

### `RAILWAY_PROJECT_ID`
**Purpose:** Identify which Railway project to deploy to

**How to get:**
```bash
# From CLI
railway status

# Or from URL
# https://railway.app/project/{PROJECT_ID}/service/...
```

**Value format:** `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`

---

### `RAILWAY_ENVIRONMENT`
**Purpose:** Specify deployment environment (staging/production)

**Staging:**
```
staging
```

**Production:**
```
production
```

---

## 2. Django Application Secrets

### `DJANGO_SECRET_KEY`
**Purpose:** Django SECRET_KEY for production

**How to generate:**
```python
# Python
import secrets
print(secrets.token_urlsafe(50))
```

Or:
```bash
# Bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

**Value format:** `long-random-string-at-least-50-characters`

**Security note:** NEVER commit this to git or share publicly

---

### `ALLOWED_HOSTS`
**Purpose:** Django ALLOWED_HOSTS setting

**Value format:**
```
yoursite.com,www.yoursite.com,.railway.app
```

---

## 3. MeiliSearch Secrets

### `MEILI_MASTER_KEY`
**Purpose:** MeiliSearch admin authentication key

**How to generate:**
```bash
# Generate secure 32-byte key
openssl rand -base64 32
```

Or:
```python
import secrets
print(secrets.token_urlsafe(32))
```

**Value format:** `secure-random-string-32-chars-minimum`

**Security note:** Used for all admin operations (indexing, settings)

---

### `MEILI_HOST`
**Purpose:** MeiliSearch server URL

**Staging:**
```
https://staging-search.yoursite.com
```

**Production:**
```
https://search.yoursite.com
```

Or Railway internal URL:
```
https://meilisearch.railway.internal:7700
```

---

### `MEILI_INDEX_NAME`
**Purpose:** Name of the search index

**Value:**
```
portfolio_search
```

---

## 4. Database Secrets (if external)

### `DATABASE_URL`
**Purpose:** PostgreSQL connection URL

**Format:**
```
postgresql://user:password@host:5432/database
```

**Railway auto-provides this:** If using Railway PostgreSQL, this is automatically available as `$DATABASE_URL`

---

## 5. Redis Secrets (for caching/monitoring)

### `REDIS_URL`
**Purpose:** Redis connection URL

**Format:**
```
redis://default:password@host:6379/0
```

**Railway auto-provides this:** If using Railway Redis, available as `$REDIS_URL`

---

## 6. Monitoring & Error Tracking

### `SENTRY_DSN` (Optional)
**Purpose:** Sentry error tracking integration

**How to get:**
1. Create account at https://sentry.io
2. Create new project (Django)
3. Copy DSN from project settings

**Value format:**
```
https://xxxxx@oXXXXX.ingest.sentry.io/XXXXXXX
```

---

## 7. Testing Secrets

### `CODECOV_TOKEN` (Optional)
**Purpose:** Upload test coverage reports

**How to get:**
1. Visit https://codecov.io
2. Connect GitHub repository
3. Copy upload token

**Value format:** `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`

---

## Security Best Practices

### 1. Secret Rotation
- Rotate all secrets every 90 days
- Use different keys for staging/production
- Never reuse keys across environments

### 2. Access Control
- Limit secret access to essential personnel
- Use environment-specific secrets
- Enable GitHub Actions secret scanning

### 3. Secret Management
```bash
# Check for leaked secrets (run locally)
pip install detect-secrets
detect-secrets scan --all-files

# GitHub automatically scans for leaked secrets
# Enable push protection in Settings → Code security
```

### 4. Emergency Response
If a secret is leaked:
```bash
# 1. Immediately rotate the leaked secret
# 2. Update GitHub secret value
# 3. Redeploy application
# 4. Check logs for unauthorized access
# 5. Review audit logs
```

---

## GitHub Secrets Setup Checklist

### Required Secrets (Minimum)
- [ ] `RAILWAY_TOKEN`
- [ ] `DJANGO_SECRET_KEY`
- [ ] `MEILI_MASTER_KEY`
- [ ] `MEILI_HOST`

### Recommended Secrets
- [ ] `RAILWAY_PROJECT_ID`
- [ ] `RAILWAY_ENVIRONMENT`
- [ ] `ALLOWED_HOSTS`
- [ ] `DATABASE_URL` (if external DB)
- [ ] `REDIS_URL` (if external Redis)

### Optional Secrets
- [ ] `SENTRY_DSN` (error tracking)
- [ ] `CODECOV_TOKEN` (coverage reports)
- [ ] `SLACK_WEBHOOK_URL` (deployment notifications)

---

## Testing Secret Configuration

### Validate Locally
```bash
# Create .env.test file (DO NOT COMMIT)
RAILWAY_TOKEN=your-token
DJANGO_SECRET_KEY=your-key
MEILI_MASTER_KEY=your-key
MEILI_HOST=http://localhost:7700

# Test deployment
railway up --environment staging
```

### Validate in CI
Push to feature branch and check GitHub Actions:
```bash
git checkout -b test-secrets
git commit --allow-empty -m "Test CI secrets"
git push origin test-secrets
```

Check Actions tab: https://github.com/YOUR-USERNAME/YOUR-REPO/actions

---

## Troubleshooting

### Issue: "Secret not found" error
```bash
# Verify secret name matches exactly
# GitHub secrets are case-sensitive!

# ❌ Wrong
django_secret_key

# ✅ Correct
DJANGO_SECRET_KEY
```

### Issue: Railway deployment fails
```bash
# Check Railway token permissions
railway whoami

# Verify project ID
railway status

# Test manual deployment
railway up
```

### Issue: MeiliSearch authentication fails
```bash
# Test master key locally
curl -H "Authorization: Bearer ${MEILI_MASTER_KEY}" \
     "${MEILI_HOST}/health"

# Response should be: {"status":"available"}
```

---

## Secret Values Template

Copy this template and fill in your values:

```bash
# DO NOT COMMIT THIS FILE
# Save as .env.secrets (add to .gitignore)

# Railway
RAILWAY_TOKEN=
RAILWAY_PROJECT_ID=
RAILWAY_ENVIRONMENT=production

# Django
DJANGO_SECRET_KEY=
ALLOWED_HOSTS=yoursite.com,www.yoursite.com

# MeiliSearch
MEILI_MASTER_KEY=
MEILI_HOST=https://search.yoursite.com
MEILI_INDEX_NAME=portfolio_search

# Database (if external)
DATABASE_URL=

# Redis (if external)
REDIS_URL=

# Monitoring (optional)
SENTRY_DSN=
CODECOV_TOKEN=
```

---

## Automated Secret Rotation Script

```bash
#!/bin/bash
# rotate_secrets.sh

echo "🔐 Rotating production secrets..."

# Generate new Django secret
NEW_DJANGO_SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(50))")
echo "New Django secret: $NEW_DJANGO_SECRET"

# Generate new MeiliSearch key
NEW_MEILI_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
echo "New MeiliSearch key: $NEW_MEILI_KEY"

# Update GitHub secrets via CLI (requires gh CLI)
gh secret set DJANGO_SECRET_KEY --body "$NEW_DJANGO_SECRET"
gh secret set MEILI_MASTER_KEY --body "$NEW_MEILI_KEY"

# Update Railway environment variables
railway variables set DJANGO_SECRET_KEY="$NEW_DJANGO_SECRET"
railway variables set MEILI_MASTER_KEY="$NEW_MEILI_KEY"

echo "✅ Secrets rotated successfully!"
echo "⚠️  Redeploy required for changes to take effect"
```

---

**Last Updated:** 2024
**Maintained By:** DevOps Team
**Review Schedule:** Quarterly
