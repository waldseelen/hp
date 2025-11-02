# Input Validation & Sanitization Framework

## 📋 Overview

Comprehensive input validation and sanitization framework for Django application security. Provides defense-in-depth protection against common vulnerabilities including XSS, SQL injection, and malicious file uploads.

## 🎯 OWASP Coverage

- **A03: Injection** - SQL injection prevention, XSS protection, command injection mitigation
- **A04: Insecure Design** - Validation pipeline architecture, defense-in-depth strategy
- **A05: Security Misconfiguration** - Comprehensive input validation, secure defaults

## 🏗️ Architecture

```
apps/core/validation/
├── __init__.py              # Package exports
├── input_sanitizer.py       # Input sanitization & validation (550+ lines)
├── file_upload.py           # File upload security (360+ lines)
└── sql_protection.py        # SQL injection protection (300+ lines)
```

## 📦 Components

### 1. InputSanitizer

Provides comprehensive input sanitization methods for various data types.

#### Methods

**`sanitize_text(text, max_length=1000)`**
- Strips HTML tags
- Escapes special characters
- Removes null bytes
- Enforces maximum length

```python
from apps.core.validation import InputSanitizer

# Sanitize user input
clean_text = InputSanitizer.sanitize_text(
    user_input,
    max_length=500
)
```

**`sanitize_html(html, allowed_tags=None, allowed_attributes=None)`**
- Allows only safe HTML tags
- Removes dangerous tags (script, iframe, object, embed)
- Removes dangerous attributes (onclick, onerror, onload)
- Blocks javascript:, data:, vbscript: protocols

```python
# Sanitize HTML content
safe_html = InputSanitizer.sanitize_html(
    user_html,
    allowed_tags={'p', 'br', 'strong', 'em'},
    allowed_attributes={'href', 'class'}
)
```

**`sanitize_url(url)`**
- Validates URL format
- Allows only http:// and https:// protocols
- Blocks javascript:, data:, file: protocols

```python
# Sanitize URL
safe_url = InputSanitizer.sanitize_url(user_url)
if safe_url is None:
    # Invalid URL - reject
```

**`sanitize_email(email)`**
- Validates email format using Django's EmailValidator
- Normalizes to lowercase

```python
# Sanitize email
clean_email = InputSanitizer.sanitize_email(user_email)
```

**`sanitize_filename(filename, max_length=255)`**
- Prevents path traversal attacks (../, \)
- Removes dangerous characters (<, >, :, ", |, ?, *)
- Removes null bytes
- Enforces maximum length

```python
# Sanitize filename
safe_filename = InputSanitizer.sanitize_filename(
    uploaded_file.name
)
```

**`sanitize_integer(value, min_value=None, max_value=None)`**
**`sanitize_float(value, min_value=None, max_value=None)`**
- Type conversion with error handling
- Enforces min/max bounds

```python
# Sanitize numeric input
age = InputSanitizer.sanitize_integer(
    user_input,
    min_value=0,
    max_value=120
)
```

### 2. InputValidator

Provides comprehensive validation methods.

#### Methods

**`validate_required_fields(data, required_fields)`**
- Checks for presence of required fields

```python
from apps.core.validation import InputValidator

is_valid, error = InputValidator.validate_required_fields(
    request_data,
    ['name', 'email', 'message']
)
if not is_valid:
    return JsonResponse({'error': error}, status=400)
```

**`validate_field_type(data, field_name, expected_type)`**
- Validates field type

```python
is_valid, error = InputValidator.validate_field_type(
    data, 'age', int
)
```

**`validate_string_length(data, field_name, min_length=None, max_length=None)`**
- Validates string length constraints

```python
is_valid, error = InputValidator.validate_string_length(
    data, 'username', min_length=3, max_length=50
)
```

**`validate_number_range(data, field_name, min_value=None, max_value=None)`**
- Validates numeric ranges

```python
is_valid, error = InputValidator.validate_number_range(
    data, 'quantity', min_value=1, max_value=100
)
```

**`validate_choice(data, field_name, allowed_values)`**
- Validates against whitelist

```python
is_valid, error = InputValidator.validate_choice(
    data, 'status', ['active', 'inactive', 'pending']
)
```

**`validate_pattern(data, field_name, pattern, pattern_name)`**
- Validates using regex pattern

```python
is_valid, error = InputValidator.validate_pattern(
    data, 'phone', r'^\d{3}-\d{3}-\d{4}$', 'phone format'
)
```

### 3. ValidationPipeline

Chains multiple validators for complex validation scenarios.

```python
from apps.core.validation import ValidationPipeline

pipeline = ValidationPipeline()
pipeline.add_validator(
    lambda d: InputValidator.validate_required_fields(d, ['name', 'email'])
)
pipeline.add_validator(
    lambda d: InputValidator.validate_string_length(d, 'name', min_length=2)
)
pipeline.add_validator(
    lambda d: InputValidator.validate_pattern(
        d, 'email', r'^[\w\.-]+@[\w\.-]+\.\w+$', 'email format'
    )
)

is_valid, errors = pipeline.validate(request_data)
if not is_valid:
    return JsonResponse({'errors': errors}, status=400)
```

### 4. FileUploadValidator

Comprehensive file upload security validation.

#### Methods

**`validate_file(uploaded_file, category='general')`**
- Comprehensive file validation
- Filename security check
- Extension validation
- File size validation
- MIME type validation (requires python-magic)

```python
from apps.core.validation.file_upload import FileUploadValidator

validator = FileUploadValidator()
is_valid, errors = validator.validate_file(
    request.FILES['document'],
    category='document'
)
if not is_valid:
    return JsonResponse({'errors': errors}, status=400)
```

**Supported Categories:**
- `image` - 10MB limit, extensions: jpg, jpeg, png, gif, webp, svg
- `document` - 25MB limit, extensions: pdf, doc, docx, txt, rtf, odt
- `archive` - 50MB limit, extensions: zip, tar, gz, rar, 7z
- `code` - 1MB limit, extensions: py, js, ts, html, css, json, xml, yml
- `general` - 10MB limit

**`validate_extension(filename, category='general')`**
- Extension whitelist validation
- Dangerous extension blacklist (.exe, .bat, .cmd, .vbs, .dll, etc.)

**`validate_file_size(uploaded_file, category='general')`**
- Enforces size limits by category

**`validate_mime_type(uploaded_file)`**
- MIME type validation using magic numbers (requires python-magic)
- Prevents file type confusion attacks

**`sanitize_filename(filename)`**
- Generates safe filename

### 5. ImageUploadValidator

Specialized image validation (extends FileUploadValidator).

```python
from apps.core.validation.file_upload import ImageUploadValidator

validator = ImageUploadValidator()
is_valid, errors = validator.validate_file(
    request.FILES['avatar'],
    category='image'
)
```

#### Additional Methods

**`validate_image_dimensions(uploaded_file, max_width=4000, max_height=4000)`**
- Validates image dimensions (requires Pillow)

**`validate_image_format(uploaded_file)`**
- Verifies actual image format using PIL

### 6. SQLInjectionProtection

SQL injection detection and prevention utilities.

#### Methods

**`is_suspicious_input(input_str)`**
- Detects SQL keywords (DROP, DELETE, UNION, EXEC, etc.)
- Detects SQL comments (--, /*, #)
- Detects injection patterns (' OR '1'='1, '; --, etc.)

```python
from apps.core.validation.sql_protection import SQLInjectionProtection

is_suspicious, reason = SQLInjectionProtection.is_suspicious_input(
    user_search_term
)
if is_suspicious:
    logger.warning(f"Suspicious input detected: {reason}")
    return JsonResponse({'error': 'Invalid search term'}, status=400)
```

**`sanitize_search_term(search_term, max_length=500)`**
- Removes SQL wildcards (%, _)
- Removes null bytes
- Enforces maximum length

```python
safe_term = SQLInjectionProtection.sanitize_search_term(
    request.GET.get('q')
)
```

**`build_safe_filter_dict(user_input, allowed_fields)`**
- Whitelists allowed fields for ORM queries

```python
user_filters = {
    'status': 'active',
    'password': 'hack',  # Attacker trying to filter by password
    'category': 'tech'
}
allowed_fields = ['status', 'category']

safe_filters, warnings = SQLInjectionProtection.build_safe_filter_dict(
    user_filters,
    allowed_fields
)
# safe_filters = {'status': 'active', 'category': 'tech'}
# warnings = ["Field 'password' not allowed"]
```

**`validate_order_by_field(field, allowed_fields)`**
- Validates ORDER BY field against whitelist

```python
order_field = request.GET.get('order_by', 'created_at')
is_valid, error = SQLInjectionProtection.validate_order_by_field(
    order_field,
    allowed_fields=['created_at', 'updated_at', 'title']
)
```

### 7. SafeRawQueryBuilder

Safe raw query construction (use sparingly - prefer Django ORM).

```python
from apps.core.validation.sql_protection import SafeRawQueryBuilder

# Escape identifier
table_name = SafeRawQueryBuilder.escape_identifier(user_input)
if table_name is None:
    # Invalid identifier - reject

# Build parameterized query
query = "SELECT * FROM users WHERE id = %s AND status = %s"
params = (user_id, status)
is_valid, error = SafeRawQueryBuilder.build_parameterized_query(
    query, params
)
```

### 8. DatabaseQueryValidator

Database query parameter validation.

```python
from apps.core.validation.sql_protection import DatabaseQueryValidator

# Validate LIMIT/OFFSET
limit = request.GET.get('limit', 20)
offset = request.GET.get('offset', 0)
safe_limit, safe_offset, error = DatabaseQueryValidator.validate_limit_offset(
    limit, offset
)
# safe_limit clamped to max 1000
# safe_offset reset to 0 if negative

# Validate ID list (for IN queries)
id_list = request.GET.getlist('ids')
is_valid, error = DatabaseQueryValidator.validate_id_list(id_list)
# Max 100 items to prevent DoS
```

## 🔒 Usage Examples

### Example 1: API Endpoint Validation

```python
from django.http import JsonResponse
from apps.core.validation import InputSanitizer, InputValidator

def performance_api(request):
    if request.method == 'POST':
        data = json.loads(request.body)

        # Validate required fields
        is_valid, error = InputValidator.validate_required_fields(
            data, ['metric_type', 'value']
        )
        if not is_valid:
            return JsonResponse({'error': error}, status=400)

        # Validate metric type
        is_valid, error = InputValidator.validate_choice(
            data, 'metric_type', ['lcp', 'fid', 'cls', 'fcp', 'ttfb']
        )
        if not is_valid:
            return JsonResponse({'error': error}, status=400)

        # Sanitize and validate value
        value = InputSanitizer.sanitize_float(
            data['value'],
            min_value=0.0,
            max_value=1000000.0
        )
        if value is None:
            return JsonResponse({'error': 'Invalid value'}, status=400)

        # Process validated data...
        return JsonResponse({'status': 'ok'})
```

### Example 2: Form Validation

```python
from django import forms
from apps.core.validation import InputSanitizer, InputValidator

class ContactForm(forms.Form):
    name = forms.CharField(max_length=100)
    email = forms.EmailField()
    message = forms.CharField(widget=forms.Textarea)

    def clean_name(self):
        name = self.cleaned_data.get('name')

        # Sanitize input
        clean_name = InputSanitizer.sanitize_text(name, max_length=100)

        # Validate length
        is_valid, error = InputValidator.validate_string_length(
            {'name': clean_name}, 'name', min_length=2
        )
        if not is_valid:
            raise forms.ValidationError(error)

        return clean_name

    def clean_email(self):
        email = self.cleaned_data.get('email')

        # Sanitize email
        clean_email = InputSanitizer.sanitize_email(email)
        if clean_email is None:
            raise forms.ValidationError('Invalid email format')

        return clean_email
```

### Example 3: File Upload Validation

```python
from django.http import JsonResponse
from apps.core.validation.file_upload import ImageUploadValidator

def upload_avatar(request):
    if request.method == 'POST' and request.FILES.get('avatar'):
        validator = ImageUploadValidator()

        # Validate uploaded file
        is_valid, errors = validator.validate_file(
            request.FILES['avatar'],
            category='image'
        )

        if not is_valid:
            return JsonResponse({'errors': errors}, status=400)

        # File is safe - process upload
        # ...
        return JsonResponse({'status': 'ok'})
```

### Example 4: Search Query Validation

```python
from django.http import JsonResponse
from apps.core.validation.sql_protection import (
    SQLInjectionProtection,
    DatabaseQueryValidator
)

def search_api(request):
    # Get search term
    search_term = request.GET.get('q', '')

    # Check for SQL injection
    is_suspicious, reason = SQLInjectionProtection.is_suspicious_input(
        search_term
    )
    if is_suspicious:
        logger.warning(f"Suspicious search term: {reason}")
        return JsonResponse({'error': 'Invalid search term'}, status=400)

    # Sanitize search term
    safe_term = SQLInjectionProtection.sanitize_search_term(search_term)

    # Validate ORDER BY field
    order_by = request.GET.get('order_by', 'created_at')
    is_valid, error = SQLInjectionProtection.validate_order_by_field(
        order_by,
        allowed_fields=['created_at', 'title', 'author']
    )
    if not is_valid:
        return JsonResponse({'error': error}, status=400)

    # Validate LIMIT/OFFSET
    limit = request.GET.get('limit', 20)
    offset = request.GET.get('offset', 0)
    safe_limit, safe_offset, error = DatabaseQueryValidator.validate_limit_offset(
        limit, offset
    )

    # Perform safe search
    results = MyModel.objects.filter(
        Q(title__icontains=safe_term) | Q(content__icontains=safe_term)
    ).order_by(order_by)[:safe_limit]

    return JsonResponse({'results': list(results)})
```

## 🧪 Testing

Comprehensive test suite covering all validation scenarios:

### Test Files

1. **`tests/security/test_input_validation.py`** (330+ lines)
   - InputSanitizer tests
   - InputValidator tests
   - ValidationPipeline tests
   - XSS protection tests

2. **`tests/security/test_file_upload_security.py`** (310+ lines)
   - File upload validation tests
   - Malicious file detection tests
   - Image validation tests

3. **`tests/security/test_sql_protection.py`** (260+ lines)
   - SQL injection detection tests
   - Safe query building tests
   - Database query validation tests

### Running Tests

```bash
# Run all validation tests
pytest tests/security/test_input_validation.py -v
pytest tests/security/test_file_upload_security.py -v
pytest tests/security/test_sql_protection.py -v

# Run specific test class
pytest tests/security/test_input_validation.py::TestInputSanitizer -v

# Run with coverage
pytest tests/security/ --cov=apps.core.validation --cov-report=html
```

## 📦 Dependencies

### Required
- Django 5.2.5+
- Python 3.14+

### Optional (for enhanced functionality)
- `python-magic` - MIME type validation using magic numbers
- `Pillow` - Image validation and format verification

```bash
# Install optional dependencies
pip install python-magic Pillow
```

## ⚠️ Security Best Practices

### 1. Defense-in-Depth
Always apply multiple validation layers:
- Input sanitization (remove dangerous content)
- Input validation (enforce constraints)
- Business logic validation (application-specific rules)

### 2. Whitelist Over Blacklist
Prefer whitelisting allowed values over blacklisting dangerous ones:
```python
# GOOD: Whitelist
is_valid = InputValidator.validate_choice(
    data, 'status', ['active', 'inactive', 'pending']
)

# BAD: Blacklist (incomplete)
if value not in ['hack', 'exploit', 'attack']:
    # Missing many attack vectors
```

### 3. Django ORM Over Raw SQL
Always prefer Django ORM over raw SQL queries:
```python
# GOOD: Django ORM (automatic parameterization)
results = User.objects.filter(username=user_input)

# BAD: Raw SQL (even with validation)
cursor.execute(f"SELECT * FROM users WHERE username = '{user_input}'")
```

### 4. Validate Before Sanitize
Reject invalid input early, don't try to "fix" malicious input:
```python
# GOOD: Validate first
is_valid, error = InputValidator.validate_pattern(
    data, 'email', r'^[\w\.-]+@[\w\.-]+\.\w+$', 'email format'
)
if not is_valid:
    return JsonResponse({'error': error}, status=400)

# Only sanitize valid input
clean_email = InputSanitizer.sanitize_email(data['email'])
```

### 5. Log Suspicious Activity
Always log suspicious input for security monitoring:
```python
is_suspicious, reason = SQLInjectionProtection.is_suspicious_input(user_input)
if is_suspicious:
    logger.warning(
        f"Suspicious input from {request.META.get('REMOTE_ADDR')}: {reason}"
    )
    return JsonResponse({'error': 'Invalid input'}, status=400)
```

## 🚀 Performance Considerations

1. **Caching Validators**: Compiled regex patterns are cached automatically
2. **Batch Validation**: Use `ValidationPipeline` for multiple validators
3. **Lazy Evaluation**: Validators stop on first error (fail-fast)
4. **MIME Type Checks**: Optional - skip if python-magic not installed

## 📝 TODO / Future Enhancements

- [ ] Rate limiting integration for validation failures
- [ ] JSON schema validation support
- [ ] Custom validator registration system
- [ ] Async validation support
- [ ] Validation metrics and monitoring
- [ ] SAST tool integration (bandit, safety)

## 📚 References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Django Security Best Practices](https://docs.djangoproject.com/en/stable/topics/security/)
- [OWASP Input Validation Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html)
- [OWASP File Upload Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html)
- [OWASP SQL Injection Prevention](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html)
