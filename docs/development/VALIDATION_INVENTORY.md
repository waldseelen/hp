# Validation Functions Inventory & Refactoring Plan

**Generated:** November 5, 2025
**Status:** Phase 16 - Validation Consolidation
**Target:** 6 validation functions with complexity 15-16 → ≤7

---

## Executive Summary

### Current State
- **6 primary validation functions identified** (complexity range: 11-16)
- **3 validator classes** requiring consolidation
- **Test coverage:** Existing (FileUploadValidator has comprehensive tests)
- **Usage:** Scattered across apps/core, apps/portfolio, apps/main

### Target State
- **Single validation framework** with BaseValidator abstract class
- **Complexity ≤7** per validation method
- **Unified contract:** validate() → (bool, Optional[str])
- **90%+ test coverage** for all validators
- **Performance:** Current level or better

---

## 1. IDENTIFIED VALIDATION FUNCTIONS (Priority Order)

### 🔴 HIGH PRIORITY - High Complexity (11+)

#### V1: `validate_tags` (apps/core/utils/validation.py)
- **Location:** `apps/core/utils/validation.py:139-188`
- **Current Complexity:** C (11)
- **Lines:** 50 lines
- **Signature:** `validate_tags(tags: Union[List[str], str], max_tags: int = 10, max_length: int = 50) -> tuple[bool, str]`
- **Purpose:** Validate tag lists or comma-separated strings
- **Issues:**
  - Complex type handling (list vs string)
  - Multiple validation layers (count, length, format)
  - Error message generation inline
- **Refactor Strategy:**
  - Extract `_normalize_tags_input(tags) -> List[str]`
  - Extract `_validate_tag_count(tags, max_tags) -> (bool, str)`
  - Extract `_validate_individual_tag(tag, max_length) -> (bool, str)`
- **Usage Points:** Unknown (needs grep analysis)
- **Test Status:** Has docstring examples, needs unit tests
- **Target Complexity:** ≤6

---

#### V2: `FileUploadValidator.validate_file` (apps/core/validation/file_upload.py)
- **Location:** `apps/core/validation/file_upload.py:104-147`
- **Current Complexity:** B (6) - *Actually OK, but part of larger class*
- **Parent Class Complexity:** FileUploadValidator (overall B-6)
- **Signature:** `validate_file(uploaded_file: UploadedFile, allowed_category: str = "image", custom_max_size: Optional[int] = None) -> Tuple[bool, Optional[str]]`
- **Purpose:** Comprehensive file upload validation
- **Sub-validators:**
  1. `validate_filename` (B-9) ⚠️
  2. `validate_extension` (A-4)
  3. `validate_file_size` (A-3)
  4. `validate_mime_type` (A-5)
- **Refactor Strategy:**
  - Keep class structure but inherit from BaseValidator
  - Reduce `validate_filename` complexity from 9 to ≤7
  - Add performance timing/metrics
- **Usage Points:** `tests/security/test_file_upload_security.py` (20+ test cases)
- **Test Status:** ✅ Excellent (comprehensive security tests)
- **Target Complexity:** ≤5 (main), ≤7 (sub-validators)

---

#### V3: `DatabaseQueryValidator.validate_limit_offset` (apps/core/validation/sql_protection.py)
- **Location:** `apps/core/validation/sql_protection.py:240-277`
- **Current Complexity:** B (8)
- **Signature:** `validate_limit_offset(limit: Optional[int] = None, offset: Optional[int] = None, max_limit: int = 1000) -> tuple`
- **Purpose:** Validate LIMIT/OFFSET for pagination queries
- **Issues:**
  - Try/except blocks increase complexity
  - Dual validation logic for limit and offset
  - Type coercion inline
- **Refactor Strategy:**
  - Extract `_coerce_to_int(value, default, min_val, max_val) -> int`
  - Separate limit and offset validation
- **Usage Points:** Unknown (needs analysis)
- **Test Status:** No tests found ⚠️
- **Target Complexity:** ≤5

---

### 🟡 MEDIUM PRIORITY - Moderate Complexity (8-10)

#### V4: `SQLInjectionProtection.is_suspicious_input` (apps/core/validation/sql_protection.py)
- **Location:** `apps/core/validation/sql_protection.py:54-94`
- **Current Complexity:** B (8)
- **Signature:** `is_suspicious_input(input_string: str) -> bool`
- **Purpose:** Defense-in-depth SQL injection pattern detection
- **Issues:**
  - Multiple loops and conditionals
  - Pattern matching complexity
- **Refactor Strategy:**
  - Extract `_check_sql_keywords(input_string) -> bool`
  - Extract `_check_comment_patterns(input_string) -> bool`
  - Extract `_check_injection_patterns(input_string) -> bool`
- **Usage Points:**
  - `apps/portfolio/api_views.py:270`
  - `apps/portfolio/api_views.py:375`
- **Test Status:** No tests found ⚠️
- **Target Complexity:** ≤6

---

#### V5: `FileUploadValidator.validate_filename` (apps/core/validation/file_upload.py)
- **Location:** `apps/core/validation/file_upload.py:147-178`
- **Current Complexity:** B (9)
- **Signature:** `validate_filename(filename: str) -> Tuple[bool, Optional[str]]`
- **Purpose:** Validate filename for path traversal and dangerous characters
- **Issues:**
  - Multiple sequential checks
  - Inline error string construction
  - List comprehension in conditional
- **Refactor Strategy:**
  - Extract `_check_path_traversal(filename) -> (bool, str)`
  - Extract `_check_dangerous_chars(filename, chars) -> (bool, str)`
  - Use constant for error messages
- **Usage Points:** Called by V2 (FileUploadValidator.validate_file)
- **Test Status:** Covered via parent tests ✅
- **Target Complexity:** ≤7

---

#### V6: `validate_json_structure` (apps/core/utils/validation.py)
- **Location:** `apps/core/utils/validation.py:216-240`
- **Current Complexity:** B (6) - *Borderline but included for framework*
- **Signature:** `validate_json_structure(data: Any, required_keys: Optional[List[str]] = None) -> tuple[bool, str]`
- **Purpose:** Validate JSON structure against required keys
- **Issues:**
  - Simple but inconsistent with framework pattern
  - Missing detailed validation options
- **Refactor Strategy:**
  - Migrate to BaseValidator subclass
  - Add schema validation support (optional)
- **Usage Points:** Unknown (needs analysis)
- **Test Status:** Has docstring examples, needs unit tests
- **Target Complexity:** ≤5

---

## 2. SUPPORTING VALIDATORS (Lower Priority)

These are already simple (A/B ≤5) but should be migrated to framework:

- `validate_url_format` (A-3)
- `validate_email_format` (A-3)
- `validate_phone_number` (A-3)
- `is_valid_slug` (A-2)
- `sanitize_html` (A-3)

---

## 3. VALIDATION FRAMEWORK DESIGN

### BaseValidator Abstract Class

```python
# apps/core/validators/base.py

from abc import ABC, abstractmethod
from typing import Any, Optional, Tuple
import time
import logging

logger = logging.getLogger(__name__)

class ValidationResult:
    """Validation result container"""
    def __init__(self, is_valid: bool, error: Optional[str] = None, metadata: dict = None):
        self.is_valid = is_valid
        self.error = error
        self.metadata = metadata or {}

    def __bool__(self):
        return self.is_valid

class BaseValidator(ABC):
    """
    Base validator with logging, timing, and standardized interface.

    All validators must implement validate() method.
    """

    def __init__(self, name: Optional[str] = None):
        self.name = name or self.__class__.__name__
        self._metrics = {
            'call_count': 0,
            'total_time': 0.0,
            'error_count': 0
        }

    @abstractmethod
    def validate(self, value: Any, **kwargs) -> ValidationResult:
        """
        Validate input value.

        Args:
            value: Value to validate
            **kwargs: Additional validator-specific parameters

        Returns:
            ValidationResult with is_valid, error, and optional metadata
        """
        pass

    def __call__(self, value: Any, **kwargs) -> ValidationResult:
        """Callable interface with metrics tracking"""
        start_time = time.perf_counter()

        try:
            result = self.validate(value, **kwargs)
            self._metrics['call_count'] += 1

            if not result.is_valid:
                self._metrics['error_count'] += 1
                logger.debug(f"{self.name} validation failed: {result.error}")

            return result

        except Exception as e:
            logger.exception(f"{self.name} validation error: {e}")
            self._metrics['error_count'] += 1
            return ValidationResult(False, f"Validation error: {str(e)}")

        finally:
            elapsed = time.perf_counter() - start_time
            self._metrics['total_time'] += elapsed

    def get_metrics(self) -> dict:
        """Get validator performance metrics"""
        return {
            **self._metrics,
            'avg_time': self._metrics['total_time'] / max(self._metrics['call_count'], 1),
            'error_rate': self._metrics['error_count'] / max(self._metrics['call_count'], 1)
        }
```

### Validator Registry

```python
# apps/core/validators/registry.py

from typing import Dict, Type
from .base import BaseValidator

class ValidatorRegistry:
    """Central registry for all validators"""

    _validators: Dict[str, Type[BaseValidator]] = {}

    @classmethod
    def register(cls, name: str):
        """Decorator to register validator"""
        def decorator(validator_class: Type[BaseValidator]):
            cls._validators[name] = validator_class
            return validator_class
        return decorator

    @classmethod
    def get(cls, name: str) -> Type[BaseValidator]:
        """Get validator by name"""
        return cls._validators.get(name)

    @classmethod
    def list_validators(cls) -> list:
        """List all registered validators"""
        return list(cls._validators.keys())
```

### Example Migration: TagsValidator

```python
# apps/core/validators/tags.py

from typing import List, Union
from .base import BaseValidator, ValidationResult
from .registry import ValidatorRegistry

@ValidatorRegistry.register('tags')
class TagsValidator(BaseValidator):
    """Validate tag lists or comma-separated strings"""

    def __init__(self, max_tags: int = 10, max_length: int = 50):
        super().__init__()
        self.max_tags = max_tags
        self.max_length = max_length

    def validate(self, tags: Union[List[str], str], **kwargs) -> ValidationResult:
        """Validate tags with ≤6 complexity"""
        # Override defaults from kwargs if provided
        max_tags = kwargs.get('max_tags', self.max_tags)
        max_length = kwargs.get('max_length', self.max_length)

        # Step 1: Normalize input
        tag_list = self._normalize_input(tags)
        if tag_list is None:
            return ValidationResult(False, "Tags must be a list or comma-separated string")

        # Step 2: Validate count
        count_result = self._validate_count(tag_list, max_tags)
        if not count_result.is_valid:
            return count_result

        # Step 3: Validate individual tags
        for tag in tag_list:
            tag_result = self._validate_individual_tag(tag, max_length)
            if not tag_result.is_valid:
                return tag_result

        return ValidationResult(True, metadata={'tag_count': len(tag_list)})

    def _normalize_input(self, tags: Union[List[str], str]) -> List[str]:
        """Extract helper: normalize tags input"""
        if not tags:
            return []

        if isinstance(tags, str):
            return [tag.strip() for tag in tags.split(",") if tag.strip()]

        if isinstance(tags, list):
            return tags

        return None

    def _validate_count(self, tags: List[str], max_tags: int) -> ValidationResult:
        """Extract helper: validate tag count"""
        if len(tags) > max_tags:
            return ValidationResult(False, f"Maximum {max_tags} tags allowed")
        return ValidationResult(True)

    def _validate_individual_tag(self, tag: str, max_length: int) -> ValidationResult:
        """Extract helper: validate single tag"""
        if not isinstance(tag, str):
            return ValidationResult(False, "Each tag must be a string")

        if not tag.strip():
            return ValidationResult(False, "Empty tags are not allowed")

        if len(tag) > max_length:
            return ValidationResult(False, f"Tag exceeds maximum length of {max_length} characters")

        return ValidationResult(True)
```

**Complexity Analysis:**
- `validate()`: 4 (sequential checks)
- `_normalize_input()`: 3 (if-elif chain)
- `_validate_count()`: 2 (single conditional)
- `_validate_individual_tag()`: 4 (sequential conditionals)
- **Maximum:** 4 ✅ (well under target of 7)

---

## 4. IMPLEMENTATION ROADMAP

### Phase 1: Framework Setup (Days 1-2)
- [ ] Create `apps/core/validators/` package
- [ ] Implement `BaseValidator` abstract class
- [ ] Implement `ValidationResult` container
- [ ] Implement `ValidatorRegistry`
- [ ] Write framework unit tests (≥90% coverage)
- [ ] Document framework API

### Phase 2: Migrate High Priority (Days 3-5)
- [ ] V1: TagsValidator (complexity 11 → ≤6)
- [ ] V2: FileUploadValidator (refactor validate_filename 9 → ≤7)
- [ ] V3: QueryValidator.validate_limit_offset (8 → ≤5)
- [ ] Write migration tests
- [ ] Benchmark performance (no regression)

### Phase 3: Migrate Medium Priority (Days 6-7)
- [ ] V4: SQLInjectionValidator (8 → ≤6)
- [ ] V5: Already covered in V2
- [ ] V6: JSONStructureValidator (6 → ≤5)
- [ ] Write migration tests

### Phase 4: Integration & Migration (Days 8-9)
- [ ] Update all call sites to use new validators
- [ ] Deprecation warnings for old functions
- [ ] Update imports across codebase
- [ ] Run full test suite
- [ ] Performance benchmarks

### Phase 5: Documentation & CI (Day 10)
- [ ] Complete `docs/development/validation_framework.md`
- [ ] Add examples and migration guide
- [ ] Update pre-commit hooks (complexity checks)
- [ ] Update CI workflows
- [ ] Final review and sign-off

---

## 5. COMPLEXITY TARGETS & VERIFICATION

| Validator | Current | Target | Strategy |
|-----------|---------|--------|----------|
| validate_tags | 11 | ≤6 | Extract 3 helpers |
| validate_filename | 9 | ≤7 | Extract 2 helpers |
| validate_limit_offset | 8 | ≤5 | Extract coercion helper |
| is_suspicious_input | 8 | ≤6 | Extract 3 pattern checkers |
| validate_json_structure | 6 | ≤5 | Simplify with framework |

**Verification Command:**
```bash
radon cc apps/core/validators/ -s -n C
```

**Success Criteria:**
- ✅ No functions with complexity >7
- ✅ Average complexity ≤5
- ✅ Test coverage ≥90%
- ✅ No performance regression (benchmark within 5%)

---

## 6. TESTING STRATEGY

### Unit Tests (per validator)
1. **Happy path:** Valid inputs return True
2. **Boundary conditions:** Max/min values, edge cases
3. **Invalid inputs:** Each error condition tested
4. **Type errors:** Wrong input types handled gracefully
5. **Performance:** Validators complete within acceptable time

### Integration Tests
1. **Framework:** Registry, BaseValidator lifecycle
2. **Migration:** Old and new validators produce same results
3. **Metrics:** Tracking and reporting works correctly

### Regression Tests
1. **Existing behavior:** All current tests still pass
2. **Performance:** No slowdown in critical paths

---

## 7. CALL SITE ANALYSIS (TODO)

Need to run comprehensive grep to find all usage points:

```bash
# Find all validation function calls
git grep -n "validate_tags\|validate_file\|validate_limit_offset\|is_suspicious_input" -- apps/

# Find all validator class instantiations
git grep -n "FileUploadValidator\|DatabaseQueryValidator\|SQLInjectionProtection" -- apps/
```

**Estimated call sites:** 15-30 locations
**Migration strategy:** Feature branch with backward compatibility layer

---

## 8. PERFORMANCE BASELINE

Before refactoring, establish performance baseline:

```python
# Performance test script
import timeit
from apps.core.utils.validation import validate_tags

# Test cases
test_inputs = [
    ["python", "django", "react"],
    "python,django,react,vue,angular",
    ["a" * 50] * 10,  # Maximum allowed
]

for test_input in test_inputs:
    time_taken = timeit.timeit(
        lambda: validate_tags(test_input),
        number=1000
    )
    print(f"Input: {test_input[:50]}... - {time_taken:.6f}s per 1000 calls")
```

**Expected baseline:** <0.001s per call (1ms)
**Target:** Maintain or improve performance

---

## 9. RISKS & MITIGATION

| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking changes in call sites | High | Maintain backward compatibility wrapper for 1 release |
| Performance regression | Medium | Benchmark before/after, optimize if needed |
| Incomplete test coverage | Medium | Require ≥90% coverage before merge |
| Complex migration path | Low | Phased rollout, feature flags if needed |

---

## 10. SUCCESS METRICS

- ✅ All 6 validators refactored with complexity ≤7
- ✅ Test coverage ≥90% for validators module
- ✅ Zero flake8 violations in validators/
- ✅ Mypy type coverage 100% in validators/
- ✅ Performance within 5% of baseline
- ✅ Zero regressions in existing tests
- ✅ Documentation complete with examples

---

## NEXT ACTIONS

1. ✅ Inventory complete (this document)
2. 🔄 **IN PROGRESS:** Define validator contract (todo #2)
3. ⏳ Design validation framework (todo #3)
4. ⏳ Implement BaseValidator (todo #4)
5. ⏳ Migrate V1 (validate_tags) as proof of concept

---

**Document Status:** Draft v1.0
**Last Updated:** November 5, 2025
**Next Review:** After BaseValidator implementation
