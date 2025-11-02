# GDPR Compliance Guide

## Overview

This guide covers GDPR (General Data Protection Regulation) compliance implementation including cookie consent, privacy preferences, data export, and data deletion.

**GDPR Articles Covered:**
- Article 6: Lawfulness of processing
- Article 7: Conditions for consent
- Article 13-14: Information to be provided (transparency)
- Article 15: Right of access
- Article 17: Right to erasure ("right to be forgotten")
- Article 20: Right to data portability
- Article 21: Right to object
- Article 30: Records of processing activities

## Features

1. **Cookie Consent Management**
   - 4-tier consent system (necessary, functional, analytics, marketing)
   - 13-month consent expiry per GDPR guidelines
   - Automatic cookie filtering based on consent

2. **Privacy Preferences**
   - Data retention period control
   - Profiling consent
   - Third-party data sharing control
   - Communication preferences (email, SMS, push)

3. **Data Portability (Article 20)**
   - Export user data in JSON/CSV/XML
   - Async processing with email notification
   - 7-day download link expiry

4. **Right to Erasure (Article 17)**
   - Account and data deletion
   - Verification code system (6-digit)
   - 30-day grace period
   - Deletion audit log

## Quick Start

### 1. Add Middleware

```python
# project/settings.py

MIDDLEWARE = [
    # ... other middleware ...
    'apps.core.middleware.gdpr_compliance.CookieConsentMiddleware',
    'apps.core.middleware.gdpr_compliance.DataCollectionLoggingMiddleware',
    'apps.core.middleware.gdpr_compliance.PrivacyPreferencesMiddleware',
]
```

### 2. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. Configure URLs

```python
# project/urls.py

urlpatterns = [
    # ... other patterns ...
    path('gdpr/', include('apps.core.urls.gdpr')),
]
```

## Cookie Consent

### Implementation

**Frontend (JavaScript):**

```javascript
// Save consent
fetch('/gdpr/cookie-consent/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken')
    },
    body: JSON.stringify({
        categories: {
            necessary: true,   // Always true
            functional: true,
            analytics: false,
            marketing: false
        }
    })
});

// Revoke consent
fetch('/gdpr/revoke-consent/', {
    method: 'POST',
    headers: {'X-CSRFToken': getCookie('csrftoken')}
});
```

**Backend (Django):**

```python
from apps.core.middleware.gdpr_compliance import has_consent_for

def my_view(request):
    if has_consent_for(request, 'analytics'):
        # Track analytics
        pass
```

### Cookie Categories

| Category | Description | Required |
|----------|-------------|----------|
| necessary | Essential cookies (sessionid, csrftoken) | Yes |
| functional | Preferences (language, theme) | No |
| analytics | Performance tracking (_ga, _gid) | No |
| marketing | Advertising (_fbp, _gcl_au) | No |

## Privacy Preferences

### Update Preferences

```javascript
// Update privacy preferences
fetch('/gdpr/privacy-preferences/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken')
    },
    body: JSON.stringify({
        data_retention_period: 180,  // days (30-3650)
        allow_profiling: false,
        allow_third_party: false,
        allow_analytics: true,
        communication_preferences: {
            email: true,
            sms: false,
            push: false
        }
    })
});
```

### Check Preferences in Code

```python
def my_view(request):
    prefs = request.privacy_preferences

    if prefs['allow_profiling']:
        # Perform user profiling
        pass

    if prefs['allow_analytics']:
        # Track analytics
        pass
```

## Data Export (Article 20)

### Request Data Export

```javascript
// Request data export
fetch('/gdpr/data-export/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken')
    },
    body: JSON.stringify({
        format: 'json',  // json, csv, or xml
        categories: [
            'profile',
            'content',
            'activity',
            'preferences'
        ]
    })
})
.then(response => response.json())
.then(data => {
    const requestId = data.request_id;
    // Poll for status or wait for email
});
```

### Check Export Status

```javascript
// Check export status
fetch(`/gdpr/data-export/${requestId}/status/`)
.then(response => response.json())
.then(data => {
    if (data.status === 'completed') {
        window.location.href = data.download_url;
    }
});
```

### Data Export Format

**JSON Example:**
```json
{
    "export_date": "2025-11-02T10:30:00Z",
    "user": {
        "username": "johndoe",
        "email": "john@example.com",
        "date_joined": "2024-01-15T09:00:00Z"
    },
    "profile": {
        "first_name": "John",
        "last_name": "Doe",
        "bio": "Software developer"
    },
    "content": [
        {
            "type": "blog_post",
            "title": "My First Post",
            "created_at": "2024-02-01T12:00:00Z"
        }
    ],
    "activity": [
        {
            "action": "login",
            "timestamp": "2025-11-02T09:15:00Z"
        }
    ]
}
```

## Data Deletion (Article 17)

### Request Data Deletion

```javascript
// Request data deletion
fetch('/gdpr/data-deletion/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken')
    },
    body: JSON.stringify({
        delete_account: true,  // Full account deletion
        categories: []  // Or specific categories
    })
})
.then(response => response.json())
.then(data => {
    alert('Verification code sent to your email');
    const requestId = data.request_id;
});
```

### Verify Deletion

```javascript
// Verify deletion with code from email
fetch(`/gdpr/data-deletion/${requestId}/verify/`, {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken')
    },
    body: JSON.stringify({
        code: '1A2B3C'  // 6-digit code from email
    })
})
.then(response => response.json())
.then(data => {
    alert(`Deletion confirmed. Data will be deleted on ${data.scheduled_deletion_at}`);
});
```

### Cancel Deletion

```javascript
// Cancel deletion (within 30-day grace period)
fetch(`/gdpr/data-deletion/${requestId}/cancel/`, {
    method: 'POST',
    headers: {'X-CSRFToken': getCookie('csrftoken')}
});
```

## Models

### PrivacyPreferences

```python
from apps.core.models.gdpr import PrivacyPreferences

# Get or create preferences
prefs, created = PrivacyPreferences.objects.get_or_create(user=request.user)

# Update preferences
prefs.data_retention_period = 180
prefs.allow_analytics = True
prefs.save()
```

### ConsentRecord

```python
from apps.core.models.gdpr import ConsentRecord

# Log consent
ConsentRecord.objects.create(
    user=request.user,
    consent_type='cookie_consent',
    consented=True,
    consent_text='User accepted analytics cookies',
    consent_version='1.0'
)

# Get consent history
history = ConsentRecord.objects.filter(user=request.user)
```

## Testing

```bash
# Run GDPR tests
pytest tests/security/test_gdpr_compliance.py -v

# Test specific class
pytest tests/security/test_gdpr_compliance.py::TestCookieConsentMiddleware -v

# Test with coverage
pytest tests/security/test_gdpr_compliance.py --cov=apps.core.middleware.gdpr_compliance
```

## Best Practices

1. **Consent Management**
   - Always log consent changes
   - Store consent version
   - Keep consent history for audit
   - Expire consent after 13 months

2. **Data Retention**
   - Respect user retention preferences
   - Automatically delete data after retention period
   - Keep deletion logs for compliance

3. **Data Export**
   - Process exports asynchronously
   - Include all personal data
   - Expire download links (7 days recommended)
   - Send email notification

4. **Data Deletion**
   - Require verification (prevent accidents)
   - 30-day grace period
   - Keep deletion audit trail
   - Anonymize instead of delete where required

5. **Privacy by Design**
   - Collect minimum necessary data
   - Default to privacy-friendly settings
   - Provide clear privacy controls
   - Regular privacy audits

## Compliance Checklist

- [ ] Cookie consent banner implemented
- [ ] 4-tier consent system (necessary, functional, analytics, marketing)
- [ ] Consent expiry after 13 months
- [ ] Privacy preferences page
- [ ] Data export functionality (JSON/CSV/XML)
- [ ] Data deletion with verification
- [ ] 30-day deletion grace period
- [ ] Consent audit trail
- [ ] Data processing records (Article 30)
- [ ] Privacy policy updated
- [ ] Cookie policy documented
- [ ] GDPR-compliant email templates
- [ ] Data retention policies configured
- [ ] Regular privacy audits scheduled

## Troubleshooting

**Consent not saving:**
- Check CSRF token
- Verify cookie settings (httponly, secure, samesite)
- Check browser console for errors

**Export not completing:**
- Check async task queue (Celery)
- Verify file permissions
- Check disk space

**Deletion verification failing:**
- Verify code hasn't expired (24 hours)
- Check email delivery
- Verify code is uppercase

## References

- [GDPR Official Text](https://gdpr-info.eu/)
- [ICO Guide to GDPR](https://ico.org.uk/for-organisations/guide-to-data-protection/guide-to-the-general-data-protection-regulation-gdpr/)
- [Cookie Consent Best Practices](https://www.cookiebot.com/en/gdpr-cookies/)
- [Data Portability Guidelines](https://ec.europa.eu/info/law/law-topic/data-protection/reform/rights-citizens/my-rights/what-are-my-rights_en)
