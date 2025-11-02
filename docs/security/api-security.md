# API Security Documentation

## 📋 Overview

Comprehensive API security implementation for Django REST Framework with JWT authentication, API key management, and advanced rate limiting.

## 🔐 Security Components

### 1. JWT Authentication

JSON Web Token (JWT) authentication for user-facing APIs.

#### Token Types

**Access Token**
- Lifetime: 15 minutes
- Used for API authentication
- Short-lived for security

**Refresh Token**
- Lifetime: 7 days
- Used to obtain new access tokens
- Rotated on each refresh (one-time use)
- Blacklisted on logout

#### Endpoints

**Obtain Tokens (Login)**
```http
POST /api/v1/auth/token/
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "SecurePassword123!"
}
```

Response:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "access_expires_in": 900,
  "refresh_expires_in": 604800
}
```

**Refresh Access Token**
```http
POST /api/v1/auth/refresh/
Content-Type: application/json

{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Logout (Blacklist Token)**
```http
POST /api/v1/auth/logout/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Verify Token**
```http
GET /api/v1/auth/verify/
Authorization: Bearer <access_token>
```

### 2. API Key Authentication

Server-to-server authentication using API keys.

#### API Key Features

- **Secure Generation**: SHA-256 hashed, 40-character random keys
- **Scoped Permissions**: Read, Write, Admin levels
- **Rate Limiting**: Per-key rate limits (default: 1000 req/hour)
- **Usage Tracking**: Track requests per key
- **Expiration**: Optional expiration dates

#### API Key Endpoints

**Create API Key**
```http
POST /api/v1/api-keys/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "Production Server",
  "permissions": "write",
  "rate_limit": 5000,
  "expires_days": 90
}
```

Response:
```json
{
  "key": "sk_a1b2c3d4e5f6...",
  "api_key": {
    "id": 1,
    "name": "Production Server",
    "key_prefix": "sk_a1b2c",
    "permissions": "write",
    "rate_limit_per_hour": 5000,
    "expires_at": "2026-02-01T00:00:00Z"
  },
  "warning": "Save this key securely! It will not be shown again."
}
```

⚠️ **Important**: The raw key is shown only once during creation. Store it securely!

**List API Keys**
```http
GET /api/v1/api-keys/
Authorization: Bearer <access_token>
```

**Get API Key Details**
```http
GET /api/v1/api-keys/<id>/
Authorization: Bearer <access_token>
```

**Revoke API Key**
```http
DELETE /api/v1/api-keys/<id>/
Authorization: Bearer <access_token>
```

**Get API Key Usage**
```http
GET /api/v1/api-keys/<id>/usage/
Authorization: Bearer <access_token>
```

#### Using API Keys

**Header Method** (Recommended):
```http
GET /api/v1/endpoint/
X-API-Key: sk_a1b2c3d4e5f6...
```

**Query Parameter Method**:
```http
GET /api/v1/endpoint/?api_key=sk_a1b2c3d4e5f6...
```

### 3. API Rate Limiting

Multi-layered rate limiting to prevent abuse.

#### Rate Limit Tiers

**Anonymous Users**
- 20 requests per minute
- IP-based tracking

**Authenticated Users (JWT)**
- 60 requests per minute
- User ID-based tracking

**API Keys**
- Configurable per key (default: 1000 requests per hour)
- Key hash-based tracking

#### Per-Endpoint Limits

```python
'/api/v1/search/': 30/min
'/api/v1/analytics/': 100/min
'/api/v1/performance/': 120/min
'/api/v1/auth/token/': 5 per 5 minutes
'/api/v1/auth/refresh/': 10 per 5 minutes
```

#### Rate Limit Headers

All API responses include rate limit headers:

```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1704110400
```

#### Rate Limit Exceeded Response

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 42
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1704110400

{
  "error": "Rate limit exceeded",
  "message": "Too many requests. Please try again later.",
  "retry_after": 42
}
```

### 4. DDoS Protection

Additional protection layer against distributed attacks.

#### DDoS Thresholds

- **Detection Threshold**: 200 requests per minute
- **Block Duration**: 15 minutes
- **Automatic IP Blocking**: Yes

#### Blocked IP Response

```http
HTTP/1.1 403 Forbidden

{
  "error": "Access denied",
  "message": "Your IP has been temporarily blocked due to suspicious activity."
}
```

## 🔧 Configuration

### JWT Settings (settings.py)

```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,

    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,

    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',

    'TOKEN_TYPE_CLAIM': 'token_type',
    'JTI_CLAIM': 'jti',
}
```

### REST Framework Authentication

```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'apps.core.auth.jwt_backend.CustomJWTAuthentication',
        'apps.core.auth.jwt_backend.APIKeyAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}
```

### Middleware Configuration

```python
MIDDLEWARE = [
    # ... other middleware
    'apps.core.middleware.api_rate_limiting.DDoSProtectionMiddleware',
    'apps.core.middleware.api_rate_limiting.APIRateLimitMiddleware',
    # ... other middleware
]
```

## 📊 Usage Examples

### Client Example (Python)

```python
import requests

# Login to get tokens
response = requests.post('https://api.example.com/api/v1/auth/token/', json={
    'username': 'user@example.com',
    'password': 'SecurePassword123!'
})
tokens = response.json()

# Use access token for authenticated requests
headers = {
    'Authorization': f"Bearer {tokens['access']}"
}
response = requests.get('https://api.example.com/api/v1/data/', headers=headers)

# Refresh token when access token expires
response = requests.post('https://api.example.com/api/v1/auth/refresh/', json={
    'refresh': tokens['refresh']
})
new_tokens = response.json()
```

### Using API Keys

```python
import requests

API_KEY = 'sk_a1b2c3d4e5f6...'

# Use API key in header
headers = {
    'X-API-Key': API_KEY
}
response = requests.get('https://api.example.com/api/v1/data/', headers=headers)
```

### JavaScript Example

```javascript
// Login
const response = await fetch('https://api.example.com/api/v1/auth/token/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    username: 'user@example.com',
    password: 'SecurePassword123!'
  })
});
const tokens = await response.json();

// Store tokens securely
localStorage.setItem('access_token', tokens.access);
localStorage.setItem('refresh_token', tokens.refresh);

// Use access token
const dataResponse = await fetch('https://api.example.com/api/v1/data/', {
  headers: {
    'Authorization': `Bearer ${tokens.access}`
  }
});
```

## 🔒 Security Best Practices

### Token Storage

**✅ DO:**
- Store tokens in httpOnly cookies (server-side)
- Use secure, encrypted storage on mobile apps
- Clear tokens on logout

**❌ DON'T:**
- Store tokens in localStorage (XSS vulnerable)
- Expose tokens in URLs
- Share tokens between users

### API Key Management

**✅ DO:**
- Rotate API keys regularly (every 90 days recommended)
- Use different keys for different environments (dev, staging, prod)
- Revoke compromised keys immediately
- Monitor API key usage for anomalies

**❌ DON'T:**
- Commit API keys to version control
- Share API keys in public channels
- Use admin-level keys for read-only operations
- Hardcode API keys in client-side code

### Rate Limiting Strategy

**For Public APIs:**
- Start with conservative limits
- Monitor usage patterns
- Gradually increase for trusted users
- Provide clear error messages

**For Internal APIs:**
- Higher limits for authenticated users
- Per-user tracking instead of per-IP
- Exponential backoff for retries

## 🧪 Testing

Run API security tests:

```bash
# All API security tests
pytest tests/security/test_jwt_authentication.py -v

# Specific test class
pytest tests/security/test_jwt_authentication.py::TestJWTAuthentication -v

# With coverage
pytest tests/security/test_jwt_authentication.py --cov=apps.core.auth --cov=apps.core.models --cov-report=html
```

## 📈 Monitoring

### Metrics to Track

1. **Authentication Metrics**
   - Token generation rate
   - Failed login attempts
   - Token refresh rate
   - Token blacklist size

2. **Rate Limiting Metrics**
   - Rate limit hits per endpoint
   - Blocked requests
   - DDoS attempts

3. **API Key Metrics**
   - Active keys
   - Key usage distribution
   - Revoked keys
   - Expired keys

### Logging

All security events are logged:

```python
# Successful authentication
logger.info("JWT tokens issued for user {username}")

# Failed authentication
logger.warning("Failed login attempt for username: {username}")

# Rate limit exceeded
logger.warning("API rate limit exceeded for {ip} on {endpoint}")

# DDoS detected
logger.error("DDoS detected from {ip} - IP blocked")
```

## 🚀 Deployment Checklist

- [ ] Configure `SIMPLE_JWT` settings
- [ ] Set up token blacklist app
- [ ] Enable API rate limiting middleware
- [ ] Configure DDoS protection thresholds
- [ ] Set up Redis for caching (rate limits)
- [ ] Enable HTTPS (required for secure tokens)
- [ ] Configure CORS for allowed origins
- [ ] Set up monitoring and alerting
- [ ] Document API authentication for consumers
- [ ] Test rate limits in staging
- [ ] Rotate initial API keys after deployment

## 📚 References

- [JWT.io](https://jwt.io/) - JWT documentation
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [djangorestframework-simplejwt](https://django-rest-framework-simplejwt.readthedocs.io/)
- [Django REST Framework Authentication](https://www.django-rest-framework.org/api-guide/authentication/)
