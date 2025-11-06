# View/Middleware Refactoring Inventory

**Generated:** November 5, 2025
**Status:** Phase 16 - View Logic & Middleware Refactoring
**Target:** 17 view/middleware functions (C: 11-14 range) → ≤10 (preferably ≤7)

---

## Executive Summary

### Complexity Distribution (from radon analysis)
- **Total C+ complexity functions:** 59 functions
- **View/middleware specific:** 17 functions identified
- **Range:** Complexity 11-18 (plus 2 outliers at 27)
- **Average complexity:** ~12.5

### Refactoring Goals
- Reduce all 17 functions to complexity ≤10 (stretch goal: ≤7)
- Extract helper functions for common patterns
- Apply design patterns (Strategy, Template Method, Helper extraction)
- Zero functional regressions
- Maintain or improve performance

---

## 1. HIGH PRIORITY - Views & APIs (Complexity 11-14)

### 🔴 Batch A: Core Public-Facing Views

#### A1: `search_view` (apps/portfolio/views.py)
- **Location:** Line 467-545
- **Complexity:** 11
- **Type:** Function (view)
- **Purpose:** Main search functionality
- **Traffic:** HIGH (user-facing search)
- **Issues:**
  - Multiple conditional branches for filters
  - Query building logic inline
  - Response formatting embedded
- **Refactor Strategy:**
  - Extract `_build_search_query(request) -> Q`
  - Extract `_apply_search_filters(queryset, filters) -> queryset`
  - Extract `_format_search_results(results) -> dict`
- **Target Complexity:** ≤7
- **Priority:** 🔴 HIGH (high traffic)

---

#### A2: `projects_view` (apps/portfolio/views.py)
- **Location:** Line 617-684
- **Complexity:** 11
- **Type:** Function (view)
- **Purpose:** Projects listing/filtering
- **Traffic:** HIGH (portfolio showcase)
- **Issues:**
  - Filter logic mixed with query building
  - Pagination logic inline
  - Multiple conditional paths
- **Refactor Strategy:**
  - Extract `_get_project_filters(request) -> dict`
  - Extract `_build_projects_query(filters) -> queryset`
  - Extract `_paginate_results(queryset, page) -> paginated`
- **Target Complexity:** ≤7
- **Priority:** 🔴 HIGH

---

#### A3: `breadcrumbs` (apps/main/context_processors.py)
- **Location:** Line 144-187
- **Complexity:** 12
- **Type:** Function (context processor)
- **Purpose:** Generate navigation breadcrumbs
- **Traffic:** HIGH (every page load)
- **Issues:**
  - Complex path parsing logic
  - Multiple nested conditionals
  - URL pattern matching inline
- **Refactor Strategy:**
  - Extract `_parse_url_path(path) -> List[PathSegment]`
  - Extract `_build_breadcrumb_item(segment) -> dict`
  - Use strategy pattern for different URL types
- **Target Complexity:** ≤8
- **Priority:** 🔴 HIGH (critical path)

---

#### A4: `_normalize_items` (apps/main/context_processors.py)
- **Location:** Line 60-92
- **Complexity:** 11
- **Type:** Function (helper)
- **Purpose:** Normalize navigation items
- **Traffic:** HIGH (navigation rendering)
- **Issues:**
  - Item transformation logic complex
  - Multiple type checks and conversions
- **Refactor Strategy:**
  - Extract `_normalize_single_item(item) -> dict`
  - Extract `_validate_item_structure(item) -> bool`
- **Target Complexity:** ≤7
- **Priority:** 🟡 MEDIUM

---

#### A5: `setup_2fa` (apps/portfolio/views/auth_views.py)
- **Location:** Line 20-97
- **Complexity:** 12
- **Type:** Function (view)
- **Purpose:** Two-factor authentication setup
- **Traffic:** MEDIUM (security feature)
- **Issues:**
  - Multiple workflow branches (GET/POST)
  - QR code generation inline
  - Session management mixed with logic
- **Refactor Strategy:**
  - Extract `_generate_2fa_secret() -> str`
  - Extract `_create_qr_code(secret) -> image`
  - Extract `_verify_2fa_token(user, token) -> bool`
- **Target Complexity:** ≤8
- **Priority:** 🔴 HIGH (security critical)

---

#### A6: `validate_password_strength` (apps/portfolio/views/auth_views.py)
- **Location:** Line 344-368
- **Complexity:** 12
- **Type:** Function (view helper)
- **Purpose:** Password strength validation
- **Traffic:** MEDIUM (registration/password change)
- **Issues:**
  - Multiple validation rules inline
  - Complex conditional logic
- **Refactor Strategy:**
  - Extract individual validators: `_check_length`, `_check_complexity`, `_check_common_passwords`
  - Use validator chain pattern
- **Target Complexity:** ≤6
- **Priority:** 🟡 MEDIUM

---

### 🟡 Batch B: Middleware & Internal APIs

#### B1: `APICachingMiddleware.__call__` (apps/core/middleware/api_caching.py)
- **Location:** Line 41-97
- **Complexity:** 13
- **Type:** Method (middleware)
- **Purpose:** API response caching
- **Traffic:** HIGH (every API request)
- **Status:** ✅ Already refactored (4 improvements done)
- **Current Complexity:** 13 (needs further reduction)
- **Next Steps:**
  - Extract `_should_cache_response(request, response) -> bool`
  - Extract `_build_cache_key(request) -> str`
- **Target Complexity:** ≤10
- **Priority:** 🟡 MEDIUM (already improved)

---

#### B2: `CookieConsentMiddleware._filter_cookies` (apps/core/middleware/gdpr_compliance.py)
- **Location:** Line 158-192
- **Complexity:** 11
- **Type:** Method (middleware)
- **Purpose:** GDPR cookie filtering
- **Traffic:** HIGH (every request)
- **Issues:**
  - Complex cookie categorization logic
  - Consent checking inline
- **Refactor Strategy:**
  - Extract `_categorize_cookie(cookie_name) -> str`
  - Extract `_has_consent(request, category) -> bool`
- **Target Complexity:** ≤7
- **Priority:** 🔴 HIGH (GDPR compliance)

---

#### B3: `generate_user_data_export` (apps/portfolio/views/gdpr_views.py)
- **Location:** Line 415-502
- **Complexity:** 13
- **Type:** Function (view)
- **Purpose:** GDPR data export
- **Traffic:** LOW (occasional user requests)
- **Issues:**
  - Data collection from multiple models
  - Complex serialization logic
  - File generation inline
- **Refactor Strategy:**
  - Extract `_collect_user_data(user) -> dict`
  - Extract `_serialize_data_export(data) -> JSON`
  - Extract `_generate_export_file(data) -> File`
- **Target Complexity:** ≤8
- **Priority:** 🟡 MEDIUM (GDPR required but low traffic)

---

#### B4: `health_metrics` (apps/portfolio/views/health_api.py)
- **Location:** Line 173-252
- **Complexity:** 13
- **Type:** Function (API view)
- **Purpose:** System health metrics API
- **Traffic:** LOW (monitoring)
- **Issues:**
  - Multiple metric collection branches
  - Aggregation logic inline
- **Refactor Strategy:**
  - Extract `_collect_database_metrics() -> dict`
  - Extract `_collect_cache_metrics() -> dict`
  - Extract `_collect_system_metrics() -> dict`
- **Target Complexity:** ≤8
- **Priority:** 🟢 LOW (internal monitoring)

---

#### B5: `log_error` (apps/portfolio/views/performance_api.py)
- **Location:** Line 257-341
- **Complexity:** 13
- **Type:** Function (API view)
- **Purpose:** Error logging API
- **Traffic:** MEDIUM (error tracking)
- **Issues:**
  - Request parsing complex
  - Validation and sanitization inline
  - Multiple error handling paths
- **Refactor Strategy:**
  - Extract `_parse_error_payload(request) -> dict`
  - Extract `_validate_error_data(data) -> ValidationResult`
  - Extract `_store_error_log(data) -> None`
- **Target Complexity:** ≤9
- **Priority:** 🟡 MEDIUM

---

#### B6: `SearchAPIView._get_available_filters` (apps/portfolio/views/search_api.py)
- **Location:** Line 277-323
- **Complexity:** 12
- **Type:** Method (API view)
- **Purpose:** Dynamic filter generation for search API
- **Traffic:** MEDIUM
- **Issues:**
  - Complex filter discovery logic
  - Conditional filter building
- **Refactor Strategy:**
  - Extract `_discover_model_filters(model) -> list`
  - Extract `_build_filter_metadata(field) -> dict`
- **Target Complexity:** ≤8
- **Priority:** 🟡 MEDIUM

---

### 🟢 Batch C: Lower Priority / Management Commands

#### C1: `get_popular_tags` (apps/main/filters.py + apps/portfolio/filters.py)
- **Location:** Line 396-425 (both files)
- **Complexity:** 12
- **Type:** Function (utility)
- **Purpose:** Tag popularity calculation
- **Traffic:** MEDIUM (caching helps)
- **Issues:**
  - Annotation and aggregation logic complex
  - Duplicate code in two files ⚠️
- **Refactor Strategy:**
  - Consolidate into single implementation in `apps/core/utils/tags.py`
  - Extract `_calculate_tag_weights(tags) -> dict`
  - Extract `_sort_tags_by_popularity(tags, weights) -> list`
- **Target Complexity:** ≤8
- **Priority:** 🟡 MEDIUM (DRY violation)

---

#### C2: `_execute_code_safely` (apps/playground/views.py)
- **Location:** Line 75-174
- **Complexity:** 12
- **Type:** Function (view helper)
- **Purpose:** Sandboxed code execution
- **Traffic:** LOW (playground feature)
- **Issues:**
  - Security checks complex
  - Execution environment setup inline
  - Output capture logic embedded
- **Refactor Strategy:**
  - Extract `_validate_code_safety(code) -> ValidationResult`
  - Extract `_setup_sandbox_environment() -> dict`
  - Extract `_capture_execution_output(code) -> ExecutionResult`
- **Target Complexity:** ≤9
- **Priority:** 🔴 HIGH (security critical despite low traffic)

---

#### C3: `SocialLink.clean` (apps/main/models.py + apps/portfolio/models.py)
- **Location:** Line 141-168 (main), Line 532-559 (portfolio)
- **Complexity:** 12
- **Type:** Method (model validation)
- **Purpose:** Validate social media links
- **Traffic:** LOW (admin/create only)
- **Issues:**
  - Duplicate code in two models ⚠️
  - Multiple platform-specific validations
- **Refactor Strategy:**
  - Create `apps/core/validators/social_media.py`
  - Extract `SocialMediaValidator` class
  - Use in both models via composition
- **Target Complexity:** ≤7
- **Priority:** 🟡 MEDIUM (DRY violation)

---

#### C4: `_matches_target` (apps/main/templatetags/navigation_tags.py)
- **Location:** Line 11-33
- **Complexity:** 13
- **Type:** Function (template tag helper)
- **Purpose:** URL pattern matching for active navigation
- **Traffic:** HIGH (navigation rendering)
- **Issues:**
  - Complex regex and pattern matching
  - Multiple match strategies
- **Refactor Strategy:**
  - Extract `_exact_match(path, target) -> bool`
  - Extract `_prefix_match(path, target) -> bool`
  - Extract `_pattern_match(path, target) -> bool`
  - Use strategy pattern
- **Target Complexity:** ≤7
- **Priority:** 🟡 MEDIUM

---

#### C5: `SearchAnalyticsView._get_analytics_data` (apps/portfolio/views/search_api.py)
- **Location:** Line 431-490
- **Complexity:** 12
- **Type:** Method (API view)
- **Purpose:** Search analytics aggregation
- **Traffic:** LOW (admin analytics)
- **Issues:**
  - Multiple aggregation queries
  - Time range filtering complex
- **Refactor Strategy:**
  - Extract `_get_search_volume_data(date_range) -> dict`
  - Extract `_get_top_queries(date_range, limit) -> list`
  - Extract `_calculate_analytics_metrics(data) -> dict`
- **Target Complexity:** ≤8
- **Priority:** 🟢 LOW

---

## 2. ADDITIONAL C-COMPLEXITY FUNCTIONS (Non View/Middleware)

These are C-complexity but not directly view/middleware. Listed for context:

### Search & Formatting
- `SearchEngine._search_model` (apps/main/search_original_backup.py) - C (13)
- `AbstractFormatter._normalize_tags` (apps/main/search/formatters/) - C (13)
- `MetadataFormatter.format_metadata` (apps/main/search/formatters/) - C (12)
- `PostgreSQLSearchEngine._search_blog_posts` (apps/portfolio/fulltext_search.py) - C (12)

### File Validation
- `SecureFileValidator.__call__` (apps/portfolio/file_validators.py) - C (13)
- `FileTypeValidator.__call__` (apps/portfolio/file_validators.py) - C (11)

### Management Commands (18 functions)
- `Command.display_summary` (monitor_performance.py) - C (18)
- `Command.handle` (analyze_queries.py) - C (18)
- `Command.handle` (analyze_performance.py) - D (27) ⚠️
- ... (many more management command handlers)

**Decision:** Focus on view/middleware first (Phase 16 scope), management commands in later phase.

---

## 3. REFACTORING PATTERNS TO APPLY

### Pattern 1: Request Handler Decomposition
**Use for:** Views with mixed concerns (A1, A2, A5, B5)

```python
# Before (complexity 12)
def my_view(request):
    # Parse request - 3 branches
    # Validate data - 4 branches
    # Query database - 2 branches
    # Format response - 3 branches
    # = 12 complexity

# After (complexity 4 + helpers ≤3 each)
def my_view(request):
    data = _parse_request(request)        # Helper: 3
    if not _validate_data(data):          # Helper: 3
        return error_response()
    results = _query_database(data)       # Helper: 2
    return _format_response(results)      # Helper: 3
```

### Pattern 2: Strategy Pattern for Conditionals
**Use for:** Functions with multiple type/category branches (A3, C4)

```python
# Before (complexity 13)
def process_item(item, type):
    if type == 'A':
        # 4 conditions
    elif type == 'B':
        # 5 conditions
    elif type == 'C':
        # 4 conditions

# After (complexity 2 + strategies ≤4 each)
strategies = {
    'A': ProcessorA(),
    'B': ProcessorB(),
    'C': ProcessorC(),
}
def process_item(item, type):
    processor = strategies.get(type, DefaultProcessor())
    return processor.process(item)
```

### Pattern 3: Validator Chain
**Use for:** Functions with sequential validation steps (A6, C2)

```python
# Before (complexity 12)
def validate(value):
    if not check1(value): return False
    if not check2(value): return False
    if not check3(value): return False
    # ... 9 more checks

# After (complexity 2 + validators ≤2 each)
validators = [Validator1(), Validator2(), ..., Validator12()]
def validate(value):
    return all(v.validate(value) for v in validators)
```

### Pattern 4: Data Collector Pattern
**Use for:** Functions gathering data from multiple sources (B3, B4)

```python
# Before (complexity 13)
def collect_data(user):
    data = {}
    # Collect from source 1 - 3 branches
    # Collect from source 2 - 4 branches
    # Collect from source 3 - 3 branches
    # Aggregate - 3 branches

# After (complexity 2 + collectors ≤3 each)
collectors = [UserCollector(), ProfileCollector(), ActivityCollector()]
def collect_data(user):
    return {name: c.collect(user) for name, c in collectors}
```

---

## 4. COMMON HELPER FUNCTIONS TO EXTRACT

Create `apps/core/utils/refactor_helpers.py`:

```python
# Request parsing
def parse_request_filters(request, allowed_fields: list) -> dict
def parse_pagination_params(request, max_per_page: int = 100) -> tuple
def parse_search_query(request) -> str

# Query building
def build_filter_query(filters: dict, model: Model) -> Q
def apply_ordering(queryset, order_by: str, allowed_fields: list) -> queryset
def apply_pagination(queryset, page: int, per_page: int) -> paginated

# Response formatting
def format_api_response(data: Any, status: int = 200) -> JsonResponse
def format_error_response(message: str, code: str, status: int = 400) -> JsonResponse
def format_paginated_response(page_obj, serializer) -> dict

# Validation
def validate_required_fields(data: dict, required: list) -> ValidationResult
def sanitize_input(data: dict, field_types: dict) -> dict
```

---

## 5. IMPLEMENTATION PLAN

### Week 1: High Priority Views (Batch A)
- **Day 1-2:** A1 (search_view), A2 (projects_view)
- **Day 3:** A3 (breadcrumbs), A4 (_normalize_items)
- **Day 4:** A5 (setup_2fa)
- **Day 5:** A6 (validate_password_strength), review & testing

**Deliverables:**
- 6 functions refactored
- Helper utilities created
- Unit tests written
- Performance benchmarks recorded

### Week 2: Middleware & Internal APIs (Batch B)
- **Day 1:** B1 (APICachingMiddleware continued), B2 (CookieConsentMiddleware)
- **Day 2:** B3 (generate_user_data_export)
- **Day 3:** B4 (health_metrics), B5 (log_error)
- **Day 4:** B6 (SearchAPIView)
- **Day 5:** Integration testing, documentation

**Deliverables:**
- 6 functions refactored
- Middleware patterns documented
- CI checks updated

### Week 3: Lower Priority & Cleanup (Batch C)
- **Day 1:** C1 (get_popular_tags consolidation)
- **Day 2:** C2 (_execute_code_safely)
- **Day 3:** C3 (SocialLink.clean consolidation)
- **Day 4:** C4 (_matches_target), C5 (SearchAnalyticsView)
- **Day 5:** Final testing, documentation, roadmap update

**Deliverables:**
- 5 functions refactored
- DRY violations eliminated (C1, C3)
- Complete documentation
- Phase 16 completion report

---

## 6. TESTING STRATEGY

### Per-Function Testing
1. **Unit tests:** Each helper function tested independently
2. **Integration tests:** Full view flow tested end-to-end
3. **Regression tests:** Existing tests must pass
4. **Performance tests:** Response time ≤ baseline + 5%

### Coverage Targets
- **New helper functions:** 100% coverage
- **Refactored views:** ≥95% coverage
- **Overall views module:** ≥90% coverage

### Test Commands
```bash
# Run view tests
pytest tests/views/ -v --cov=apps.portfolio.views --cov=apps.main.views

# Performance regression check
pytest tests/performance/ --benchmark-only

# Complexity verification
radon cc apps/portfolio/views apps/main/views apps/core/middleware -s -n C
```

---

## 7. SUCCESS CRITERIA

- ✅ All 17 functions reduced to complexity ≤10 (stretch: ≤7)
- ✅ Zero functional regressions (all existing tests pass)
- ✅ Performance within 5% of baseline
- ✅ Test coverage ≥90% for refactored modules
- ✅ Flake8 0 violations
- ✅ Mypy type coverage ≥90%
- ✅ DRY violations eliminated (C1, C3)
- ✅ Helper utilities documented and reusable

---

## 8. COMPLEXITY TARGETS SUMMARY

| Function | Current | Target | Priority |
|----------|---------|--------|----------|
| search_view | 11 | ≤7 | 🔴 HIGH |
| projects_view | 11 | ≤7 | 🔴 HIGH |
| breadcrumbs | 12 | ≤8 | 🔴 HIGH |
| setup_2fa | 12 | ≤8 | 🔴 HIGH |
| _execute_code_safely | 12 | ≤9 | 🔴 HIGH (security) |
| validate_password_strength | 12 | ≤6 | 🟡 MEDIUM |
| _normalize_items | 11 | ≤7 | 🟡 MEDIUM |
| APICachingMiddleware | 13 | ≤10 | 🟡 MEDIUM |
| CookieConsentMiddleware | 11 | ≤7 | 🔴 HIGH (GDPR) |
| generate_user_data_export | 13 | ≤8 | 🟡 MEDIUM |
| health_metrics | 13 | ≤8 | 🟢 LOW |
| log_error | 13 | ≤9 | 🟡 MEDIUM |
| SearchAPIView filters | 12 | ≤8 | 🟡 MEDIUM |
| get_popular_tags | 12 | ≤8 | 🟡 MEDIUM |
| SocialLink.clean | 12 | ≤7 | 🟡 MEDIUM |
| _matches_target | 13 | ≤7 | 🟡 MEDIUM |
| SearchAnalyticsView | 12 | ≤8 | 🟢 LOW |

**Average Current:** 12.1
**Average Target:** 7.7
**Improvement:** ~36% complexity reduction

---

## NEXT ACTIONS

1. ✅ Inventory complete (this document)
2. 🔄 **IN PROGRESS:** Risk & impact analysis (todo #16)
3. ⏳ Pattern selection for each batch (todo #17)
4. ⏳ Create helper utilities module (todo #18)
5. ⏳ Begin Batch A refactoring (todo #19)

---

**Document Status:** Draft v1.0
**Last Updated:** November 5, 2025
**Next Review:** After helper utilities creation
