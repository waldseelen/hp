# Validation Contract Specification

**Version:** 1.0
**Date:** November 5, 2025
**Status:** Draft
**Purpose:** Define standard interface and behavior for all validators in the framework

---

## 1. CORE CONTRACT

All validators MUST adhere to this contract:

### 1.1 Input/Output Signature

```python
def validate(value: Any, **kwargs) -> ValidationResult:
    """
    Validate input value according to validator rules.

    Args:
        value: The value to validate (type depends on validator)
        **kwargs: Optional validator-specific parameters

    Returns:
        ValidationResult with:
          - is_valid (bool): True if validation passed
          - error (Optional[str]): Human-readable error message if invalid
          - metadata (dict): Optional validation metadata (e.g., stats, details)

    Raises:
        Never raises ValidationError - returns ValidationResult(False, error_msg)
        May raise TypeError if value type is completely wrong
    """
```

### 1.2 ValidationResult Structure

```python
@dataclass
class ValidationResult:
    is_valid: bool
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __bool__(self) -> bool:
        """Allow if result: ... checks"""
        return self.is_valid

    def __str__(self) -> str:
        """Human-readable representation"""
        return f"Valid" if self.is_valid else f"Invalid: {self.error}"
```

---

## 2. VALIDATOR BEHAVIOR CONTRACTS

### 2.1 Empty/Null Input

**Contract:** Validators MUST explicitly handle empty/null inputs.

**Standard behavior:**
- `None` → `ValidationResult(False, "Value is required")`
- `""` (empty string) → Depends on validator (often invalid)
- `[]` (empty list) → Often valid (unless min_length specified)
- `{}` (empty dict) → Often valid (unless required_keys specified)

**Example:**
```python
def validate(self, value, **kwargs):
    if value is None:
        return ValidationResult(False, "Value is required")
    if not value and self.allow_empty is False:
        return ValidationResult(False, "Empty value not allowed")
    # ... rest of validation
```

### 2.2 Type Coercion

**Contract:** Validators SHOULD accept flexible types where reasonable.

**Examples:**
- `TagsValidator`: Accept both `List[str]` and `"comma,separated,string"`
- `IntegerValidator`: Accept `"123"` (string) and coerce to `int`
- `BooleanValidator`: Accept `"true"`, `"1"`, `True`, `1`

**Anti-pattern:** Strict type checking that rejects reasonable inputs.

```python
# ❌ BAD: Too strict
if not isinstance(value, list):
    return ValidationResult(False, "Must be a list")

# ✅ GOOD: Flexible
if isinstance(value, str):
    value = [tag.strip() for tag in value.split(",")]
elif not isinstance(value, list):
    return ValidationResult(False, "Must be list or comma-separated string")
```

### 2.3 Error Messages

**Contract:** Error messages MUST be:
1. **User-friendly:** No technical jargon or tracebacks
2. **Actionable:** Tell user what's wrong and how to fix it
3. **Specific:** Not generic "Invalid input"
4. **Consistent format:** Follow project style

**Error Message Template:**
```
"[What's wrong]. [Expected format/value]. [Example if helpful]"
```

**Examples:**
```python
# ❌ BAD
"Invalid"
"Error in validation"
"Tag validation failed"

# ✅ GOOD
"Tag exceeds maximum length of 50 characters"
"Email format invalid. Expected: user@domain.com"
"File size too large. Maximum: 10MB"
"Missing required fields: name, email"
```

### 2.4 Performance Contract

**Contract:** Validators MUST complete within acceptable time limits.

**Performance Targets:**
- **Simple validators** (string format, length): <0.1ms per call
- **Medium validators** (regex, multiple checks): <1ms per call
- **Complex validators** (file I/O, network): <100ms per call
- **Database validators** (uniqueness checks): <500ms per call

**Implementation:**
- Use `@lru_cache` for expensive computations
- Avoid I/O in tight loops
- Fail fast (check cheapest conditions first)

```python
# ✅ GOOD: Fail fast pattern
def validate(self, value):
    # Check cheap conditions first
    if not value:
        return ValidationResult(False, "Value required")
    if len(value) > self.max_length:
        return ValidationResult(False, f"Too long (max: {self.max_length})")

    # Expensive checks last
    if self.check_uniqueness and self._exists_in_db(value):
        return ValidationResult(False, "Value already exists")
```

### 2.5 Thread Safety

**Contract:** Validators MUST be thread-safe for concurrent usage.

**Requirements:**
- No shared mutable state across calls
- Instance variables READ-ONLY after `__init__`
- Use `threading.Lock` if mutable state unavoidable

```python
# ✅ GOOD: Thread-safe (immutable config)
class MyValidator(BaseValidator):
    def __init__(self, max_length: int = 100):
        self.max_length = max_length  # Immutable after init

    def validate(self, value):
        # No shared state
        return ValidationResult(len(value) <= self.max_length)

# ❌ BAD: Not thread-safe (mutable state)
class BadValidator(BaseValidator):
    def __init__(self):
        self.count = 0  # Shared mutable state

    def validate(self, value):
        self.count += 1  # Race condition!
        return ValidationResult(True)
```

---

## 3. VALIDATOR TYPES & CONTRACTS

### 3.1 Format Validators

**Purpose:** Validate string format (email, URL, phone, etc.)

**Contract:**
- Input type: `str`
- Return: `ValidationResult(is_valid, error_msg)`
- No side effects
- Fast (<1ms)

**Example:**
```python
class EmailValidator(BaseValidator):
    def validate(self, email: str) -> ValidationResult:
        if not isinstance(email, str):
            return ValidationResult(False, "Email must be a string")

        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
            return ValidationResult(False, "Invalid email format")

        return ValidationResult(True)
```

### 3.2 Range Validators

**Purpose:** Validate numeric ranges, lengths, counts

**Contract:**
- Input type: `int`, `float`, or `len()`-able
- Parameters: `min`, `max` (optional)
- Inclusive ranges: `min <= value <= max`

**Example:**
```python
class RangeValidator(BaseValidator):
    def __init__(self, min_val=None, max_val=None):
        self.min_val = min_val
        self.max_val = max_val

    def validate(self, value: Union[int, float]) -> ValidationResult:
        if self.min_val is not None and value < self.min_val:
            return ValidationResult(False, f"Minimum value: {self.min_val}")

        if self.max_val is not None and value > self.max_val:
            return ValidationResult(False, f"Maximum value: {self.max_val}")

        return ValidationResult(True, metadata={'value': value})
```

### 3.3 File Validators

**Purpose:** Validate file uploads (type, size, content)

**Contract:**
- Input type: `UploadedFile` or file-like object
- Check: extension, MIME type, size, content
- Return: `ValidationResult` with metadata (file info)
- **MUST** reset file pointer: `file.seek(0)` after reading

**Example:**
```python
class FileValidator(BaseValidator):
    def validate(self, uploaded_file: UploadedFile) -> ValidationResult:
        # Read for validation
        uploaded_file.seek(0)
        content = uploaded_file.read(2048)

        # Validate MIME type
        mime_type = magic.from_buffer(content, mime=True)

        # MUST reset pointer for subsequent use
        uploaded_file.seek(0)

        if mime_type not in self.allowed_types:
            return ValidationResult(False, f"File type not allowed: {mime_type}")

        return ValidationResult(True, metadata={'mime_type': mime_type})
```

### 3.4 Business Logic Validators

**Purpose:** Validate domain-specific rules (uniqueness, relationships)

**Contract:**
- Input type: Varies (model instance, dict, etc.)
- May query database (use connection pooling)
- Return: `ValidationResult` with business context
- **MUST** use transactions if modifying data

**Example:**
```python
class UniquenessValidator(BaseValidator):
    def __init__(self, model, field_name):
        self.model = model
        self.field_name = field_name

    def validate(self, value: Any, exclude_id=None) -> ValidationResult:
        queryset = self.model.objects.filter(**{self.field_name: value})

        if exclude_id:
            queryset = queryset.exclude(id=exclude_id)

        if queryset.exists():
            return ValidationResult(
                False,
                f"{self.field_name.title()} already exists",
                metadata={'existing_count': queryset.count()}
            )

        return ValidationResult(True)
```

---

## 4. METADATA USAGE

**Contract:** `metadata` dict provides additional context about validation.

### 4.1 Standard Metadata Keys

**Common keys:**
- `field_name`: Name of validated field
- `value`: Sanitized/normalized value
- `original_value`: Original input (if transformed)
- `validation_time`: Time taken (seconds)
- `warnings`: Non-fatal issues (list)

**Example:**
```python
return ValidationResult(
    True,
    metadata={
        'field_name': 'email',
        'value': normalized_email,
        'original_value': raw_input,
        'validation_time': 0.0012,
        'warnings': ['Email domain has low reputation']
    }
)
```

### 4.2 Validator-Specific Metadata

Validators MAY include custom metadata:

```python
# TagsValidator metadata
metadata = {
    'tag_count': 5,
    'normalized_tags': ['python', 'django', 'web'],
    'removed_duplicates': 2
}

# FileValidator metadata
metadata = {
    'file_size': 1024000,
    'mime_type': 'image/jpeg',
    'dimensions': (1920, 1080),
    'has_exif': True
}
```

---

## 5. ERROR HANDLING CONTRACT

### 5.1 Exception Handling

**Contract:** Validators MUST catch exceptions and return `ValidationResult`.

**Never raise to caller except:**
- `TypeError`: Completely wrong type (e.g., validator expects string, got database connection)
- `AttributeError`: Missing required attribute
- System errors (out of memory, disk full)

**Example:**
```python
def validate(self, value):
    try:
        # Validation logic
        result = self._complex_check(value)
        return ValidationResult(result)

    except ValueError as e:
        # Expected error → ValidationResult
        return ValidationResult(False, f"Invalid value: {e}")

    except Exception as e:
        # Unexpected error → Log and return safe error
        logger.exception(f"Validation error: {e}")
        return ValidationResult(False, "Validation failed unexpectedly")
```

### 5.2 Logging Contract

**Contract:** Validators SHOULD log at appropriate levels.

**Logging levels:**
- `DEBUG`: Validation passed/failed details
- `INFO`: Performance warnings (slow validation)
- `WARNING`: Unexpected input patterns
- `ERROR`: Validation system errors
- `CRITICAL`: Never (validation errors are not critical)

**Example:**
```python
import logging
logger = logging.getLogger(__name__)

def validate(self, value):
    start = time.time()

    # ... validation logic ...

    elapsed = time.time() - start
    if elapsed > 0.1:  # 100ms threshold
        logger.warning(f"{self.name} took {elapsed:.3f}s to validate")

    logger.debug(f"{self.name} validation: {result.is_valid}")
    return result
```

---

## 6. TESTING CONTRACT

**Contract:** Every validator MUST have comprehensive tests.

### 6.1 Required Test Cases

**Minimum test coverage:**
1. **Happy path:** Valid inputs return `True`
2. **Boundary conditions:** Min/max values
3. **Invalid inputs:** Each error condition tested
4. **Type errors:** Wrong types handled gracefully
5. **Edge cases:** Empty, null, extreme values
6. **Performance:** Validators complete within time budget

**Example test structure:**
```python
class TestMyValidator(TestCase):
    def setUp(self):
        self.validator = MyValidator(max_length=100)

    def test_valid_input(self):
        result = self.validator.validate("valid input")
        self.assertTrue(result.is_valid)

    def test_too_long(self):
        result = self.validator.validate("x" * 101)
        self.assertFalse(result.is_valid)
        self.assertIn("maximum length", result.error.lower())

    def test_null_input(self):
        result = self.validator.validate(None)
        self.assertFalse(result.is_valid)

    def test_performance(self):
        start = time.time()
        for _ in range(1000):
            self.validator.validate("test")
        elapsed = time.time() - start
        self.assertLess(elapsed, 0.1, "Validator too slow")
```

### 6.2 Test Coverage Target

**Contract:** Validators MUST achieve ≥90% test coverage.

**Measure with:**
```bash
pytest tests/validators/ --cov=apps.core.validators --cov-report=html
```

---

## 7. DOCUMENTATION CONTRACT

**Contract:** Every validator MUST have complete docstrings.

### 7.1 Class Docstring

```python
class MyValidator(BaseValidator):
    """
    One-line summary of what this validator does.

    Longer description explaining:
    - What is being validated
    - What makes input valid/invalid
    - Common use cases

    Args:
        param1: Description of parameter 1
        param2: Description of parameter 2

    Attributes:
        attr1: Description of attribute 1

    Example:
        >>> validator = MyValidator(max_length=50)
        >>> result = validator.validate("hello")
        >>> result.is_valid
        True

        >>> result = validator.validate("x" * 100)
        >>> result.error
        'Exceeds maximum length of 50 characters'

    Raises:
        TypeError: If value is completely wrong type
    """
```

### 7.2 Method Docstring

```python
def validate(self, value: str, **kwargs) -> ValidationResult:
    """
    Validate string value against defined rules.

    Args:
        value: String to validate
        **kwargs: Optional parameters:
            - strict (bool): Enable strict mode (default: False)
            - context (dict): Additional validation context

    Returns:
        ValidationResult with:
            - is_valid: True if valid
            - error: Error message if invalid
            - metadata: Validation details (length, normalized value)

    Example:
        >>> result = self.validate("hello world")
        >>> result.is_valid
        True
        >>> result.metadata['length']
        11
    """
```

---

## 8. MIGRATION CONTRACT

**Contract:** Migrating to new validator framework MUST maintain backward compatibility.

### 8.1 Compatibility Layer

**Provide wrapper for old function-based validators:**

```python
# Old function signature
def validate_tags(tags: List[str], max_tags: int = 10) -> Tuple[bool, str]:
    # ... old implementation
    pass

# New validator
validator = TagsValidator(max_tags=10)

# Compatibility wrapper
def validate_tags(tags: List[str], max_tags: int = 10) -> Tuple[bool, str]:
    """
    DEPRECATED: Use TagsValidator instead.

    This function will be removed in version 2.0.
    """
    warnings.warn(
        "validate_tags() is deprecated, use TagsValidator",
        DeprecationWarning,
        stacklevel=2
    )
    result = validator.validate(tags, max_tags=max_tags)
    return (result.is_valid, result.error or "")
```

### 8.2 Migration Timeline

1. **Phase 1:** Introduce new validators, keep old functions
2. **Phase 2:** Add deprecation warnings to old functions
3. **Phase 3:** Update all call sites to use new validators
4. **Phase 4:** Remove old functions (next major version)

---

## 9. PERFORMANCE MONITORING CONTRACT

**Contract:** Validators MUST expose performance metrics.

### 9.1 Metrics to Track

```python
class BaseValidator:
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get validator performance metrics.

        Returns:
            Dict with:
                - call_count: Total number of validations
                - total_time: Total time spent (seconds)
                - avg_time: Average time per validation
                - error_count: Number of validation failures
                - error_rate: Percentage of failures
        """
        return {
            'call_count': self._metrics['call_count'],
            'total_time': self._metrics['total_time'],
            'avg_time': self._metrics['total_time'] / max(self._metrics['call_count'], 1),
            'error_count': self._metrics['error_count'],
            'error_rate': self._metrics['error_count'] / max(self._metrics['call_count'], 1)
        }
```

### 9.2 Metrics Reporting

**Expose metrics endpoint:**
```python
# Management command
python manage.py validator_stats

# Output:
Validator Statistics:
=====================
TagsValidator:
  - Calls: 15,234
  - Avg time: 0.0012s
  - Error rate: 8.3%

EmailValidator:
  - Calls: 45,678
  - Avg time: 0.0008s
  - Error rate: 2.1%
```

---

## 10. CONTRACT COMPLIANCE CHECKLIST

Before marking validator complete, verify:

- [ ] Implements `validate(value, **kwargs) -> ValidationResult`
- [ ] Handles `None` and empty inputs gracefully
- [ ] Error messages are user-friendly and actionable
- [ ] Performance within budget (<1ms for simple, <100ms for complex)
- [ ] Thread-safe (no shared mutable state)
- [ ] Comprehensive tests (≥90% coverage)
- [ ] Complete docstrings with examples
- [ ] Exposes performance metrics
- [ ] Logged at appropriate levels
- [ ] Type hints on all public methods

---

**Document Status:** Draft v1.0
**Next Review:** After BaseValidator implementation
**Feedback:** Email team@project.com with suggestions
