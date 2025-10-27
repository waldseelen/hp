# Security Setup Guide

This project uses environment-based authentication and secure credential management. **No passwords should ever be committed to the repository.**

## Quick Start

1. **Copy the environment template:**
   ```bash
   cp .env.example .env
   ```

2. **Generate a secure Django SECRET_KEY:**
   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

3. **Generate your admin password hash:**
   ```bash
   python -c "from django.contrib.auth.hashers import make_password; print(make_password('your-secure-password-here'))"
   ```

4. **Update `.env` with your credentials:**
   ```bash
   # Required Settings
   SECRET_KEY=<generated-secret-key>
   ALLOWED_ADMIN_EMAIL=your-email@example.com
   ALLOWED_ADMIN_PASSWORD_HASH=<generated-password-hash>
   ```

## Environment Variables Explained

### Core Authentication

- **`ALLOWED_ADMIN_EMAIL`**: Email address authorized to access the admin panel
- **`ALLOWED_ADMIN_PASSWORD_HASH`**: Hashed password for admin authentication
- **`SECRET_KEY`**: Django's secret key (must be unique and secret)

### Optional Testing Variables

These are only needed when running tests:

- **`TEST_ADMIN_EMAIL`**: Test email for authentication tests (default: `test@example.com`)
- **`TEST_ADMIN_PASSWORD`**: Test password for authentication tests (default: `test-password-change-me`)

### Optional Script Variables

These are only needed when running data management scripts:

- **`ADMIN_PASSWORD`**: Plain password for setup scripts
- **`STAGING_PASSWORD`**: Password for staging environment setup
- **`TEST_PASSWORD`**: Password for test data creation

## How Authentication Works

This project uses `RestrictedAdminBackend` which:

1. Reads `ALLOWED_ADMIN_EMAIL` and `ALLOWED_ADMIN_PASSWORD_HASH` from environment variables
2. Only allows login for the configured email address
3. Verifies the password against the stored hash
4. Creates/updates the user automatically on successful authentication
5. Sets user permissions (superuser, staff, active)

**Important:** Users created this way have no usable password in the database - authentication only works via environment variables.

## Password Hash Generation

To generate a password hash for `.env`:

```python
from django.contrib.auth.hashers import make_password
password_hash = make_password('your-password-here')
print(password_hash)
```

Or use this one-liner:

```bash
python -c "from django.contrib.auth.hashers import make_password; import sys; print(make_password(input('Password: ')))"
```

## Security Best Practices

### ✅ DO:

- Store all credentials in `.env` (never commit this file)
- Use strong, unique passwords
- Generate a new `SECRET_KEY` for each environment
- Rotate credentials periodically
- Use different passwords for development, staging, and production
- Review `.env.example` when adding new secret variables

### ❌ DON'T:

- Commit `.env` to version control
- Hardcode passwords in Python files
- Share your `.env` file via email/chat
- Use simple passwords like "admin123"
- Use the same password across environments
- Include the default Django insecure secret key in production

## Testing

When running tests, you can either:

1. **Set environment variables before running tests:**
   ```bash
   export TEST_ADMIN_EMAIL="test@example.com"
   export TEST_ADMIN_PASSWORD="test-password"
   python manage.py test
   ```

2. **Tests will use default values** if variables are not set (safe defaults are configured)

## Deployment

### Railway / Heroku / Cloud Platforms:

Set environment variables in your platform's dashboard:

```bash
ALLOWED_ADMIN_EMAIL=your-production-email@example.com
ALLOWED_ADMIN_PASSWORD_HASH=<production-password-hash>
SECRET_KEY=<production-secret-key>
DEBUG=False
```

### Docker:

Pass environment variables when running containers:

```bash
docker run -e ALLOWED_ADMIN_EMAIL="admin@example.com" \
           -e ALLOWED_ADMIN_PASSWORD_HASH="<hash>" \
           -e SECRET_KEY="<key>" \
           your-image
```

Or use `docker-compose.yml`:

```yaml
environment:
  - ALLOWED_ADMIN_EMAIL=admin@example.com
  - ALLOWED_ADMIN_PASSWORD_HASH=${ALLOWED_ADMIN_PASSWORD_HASH}
  - SECRET_KEY=${SECRET_KEY}
```

## Troubleshooting

### "Yetkisiz giris" Error

This means unauthorized login. Check:

1. Is `ALLOWED_ADMIN_EMAIL` set correctly in `.env`?
2. Is `ALLOWED_ADMIN_PASSWORD_HASH` a valid hash?
3. Are you using the correct password?
4. Did you restart the server after updating `.env`?

### Generating a New Hash

If you need to reset your password:

```bash
python -c "from django.contrib.auth.hashers import make_password; print(make_password('new-password'))"
```

Then update `ALLOWED_ADMIN_PASSWORD_HASH` in `.env` and restart the server.

### Test Authentication

Verify your authentication setup:

```bash
python -c "
from django.contrib.auth.hashers import check_password
import os
from decouple import config

password_hash = config('ALLOWED_ADMIN_PASSWORD_HASH')
test_password = input('Enter password to test: ')
if check_password(test_password, password_hash):
    print('✅ Password matches!')
else:
    print('❌ Password does not match')
"
```

## File Checklist

Ensure these files are configured correctly:

- [ ] `.env` - Contains your actual credentials (NEVER commit)
- [ ] `.env.example` - Template with placeholder values (safe to commit)
- [ ] `.gitignore` - Includes `.env` to prevent commits
- [ ] `SECURITY_SETUP.md` - This file (safe to commit)

## Support

If you encounter issues:

1. Check this document first
2. Verify your `.env` file matches `.env.example` structure
3. Ensure all required environment variables are set
4. Check server logs for detailed error messages

## License

This security setup is part of the open-source portfolio project. All sensitive credentials must be managed through environment variables.
