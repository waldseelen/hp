# Search Tests Quick Reference

## Running Tests

### Quick Start
```bash
# Run all search tests
.\run_search_tests.ps1

# Run only unit tests (fast, no MeiliSearch needed)
.\run_search_tests.ps1 -TestType unit

# Run only integration tests
.\run_search_tests.ps1 -TestType integration

# Run with coverage report
.\run_search_tests.ps1 -TestType coverage

# Run specific markers
.\run_search_tests.ps1 -Markers "search and api"

# Verbose output
.\run_search_tests.ps1 -Verbose
```

### Direct pytest Commands
```bash
# All search tests
pytest tests/unit/test_search_index.py tests/integration/test_search_api.py tests/integration/test_admin_reindex.py -v

# Only unit tests
pytest tests/unit/test_search_index.py -m unit -v

# Only API tests
pytest tests/integration/test_search_api.py -m api -v

# Only security tests
pytest -m security -v

# With coverage
pytest tests/unit/test_search_index.py --cov=apps.main.search_index --cov-report=html

# Parallel execution
pytest -n 4 tests/
```

## Test Files Overview

### `tests/unit/test_search_index.py` (400+ lines, 50+ tests)
**Unit tests for SearchIndexManager**

Test Classes:
- `TestSearchIndexManagerInit` - Initialization, configuration
- `TestContentSanitization` - HTML/Markdown sanitization, XSS prevention
- `TestDocumentBuilding` - Document creation, field mapping
- `TestIndexOperations` - index_document(), delete_document(), bulk_index()
- `TestTagParsing` - Tag string parsing
- `TestURLGeneration` - URL generation for results
- `TestXSSPrevention` - Security tests for XSS payloads
- `TestSearchIndexManagerSingleton` - Singleton pattern

Key Tests:
- ✓ `test_sanitize_xss_payloads` - 6 XSS payloads sanitized
- ✓ `test_build_document_blog_post` - BlogPost → search document
- ✓ `test_index_document_draft_skipped` - Drafts not indexed
- ✓ `test_bulk_index_batching` - Batch processing works
- ✓ `test_parse_tags_comma_separated` - Tag parsing

### `tests/integration/test_search_api.py` (600+ lines, 40+ tests)
**Integration tests for Search API endpoints**

Test Classes:
- `TestSearchAPIEndpoint` - /api/search/ main search
- `TestSearchSuggestEndpoint` - /api/search/suggest/ autocomplete
- `TestSearchStatsEndpoint` - /api/search/stats/ statistics
- `TestSearchRateLimiting` - Rate limiting (100 req/min)
- `TestSearchResponseFormat` - JSON response validation
- `TestSearchWithRealData` - End-to-end tests

Key Tests:
- ✓ `test_search_basic_query` - Basic search works
- ✓ `test_search_with_pagination` - Pagination (page, per_page)
- ✓ `test_search_with_category_filter` - Category filtering
- ✓ `test_search_visibility_filter` - Only visible items
- ✓ `test_suggest_performance` - Autocomplete < 500ms
- ✓ `test_rate_limit_anonymous_user` - Rate limiting enforced
- ✓ `test_stats_per_model_counts` - Stats by model type

### `tests/integration/test_admin_reindex.py` (500+ lines, 35+ tests)
**Integration tests for admin reindex functionality**

Test Classes:
- `TestAdminSaveIndexUpdate` - Admin save triggers index
- `TestAdminDeleteIndexRemoval` - Admin delete removes from index
- `TestBulkReindexAdminAction` - Bulk reindex action
- `TestManagementCommand` - reindex_search command
- `TestSignalIntegration` - Signal handlers
- `TestIndexingPerformance` - Performance benchmarks

Key Tests:
- ✓ `test_create_blog_post_in_admin_triggers_index` - Save → index
- ✓ `test_delete_blog_post_removes_from_index` - Delete → remove
- ✓ `test_bulk_reindex_blog_posts` - Bulk action works
- ✓ `test_reindex_all_command` - Management command works
- ✓ `test_signal_handles_index_errors` - Errors don't break save
- ✓ `test_bulk_index_performance` - 100 posts < 5 seconds
- ✓ `test_admin_save_latency` - Save + index < 1 second

## Test Markers

Use markers to filter tests:

```bash
# Search-related tests
pytest -m search

# API endpoint tests
pytest -m api

# Admin interface tests
pytest -m admin

# Performance tests
pytest -m performance

# Security tests (XSS, sanitization)
pytest -m security

# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# Combine markers
pytest -m "search and not performance"
pytest -m "api or admin"
```

## Coverage Targets

| Component | Target | Current |
|-----------|--------|---------|
| apps/main/search_index.py | 90% | TBD |
| apps/main/views/search_views.py | 85% | TBD |
| apps/main/signals.py (search) | 80% | TBD |
| apps/main/admin.py (reindex) | 75% | TBD |

View coverage:
```bash
pytest --cov=apps.main --cov-report=html
# Open: htmlcov/index.html
```

## Test Data Fixtures

Available in `tests/conftest_search.py`:

**Users:**
- `regular_user` - Normal user
- `admin_user` - Superuser
- `authenticated_client` - Logged-in client
- `admin_client` - Admin client

**Models:**
- `blog_post` - Published blog post
- `draft_blog_post` - Draft post
- `multiple_blog_posts` - 5 posts
- `ai_tool` - Single AI tool
- `multiple_ai_tools` - 3 tools
- `useful_resource` - Resource item

**Mocks:**
- `mock_meilisearch_client` - Mocked MeiliSearch
- `mock_search_index_manager` - Mocked manager
- `mock_search_results` - Sample results
- `xss_payloads` - XSS test cases

**Content:**
- `safe_html_content` - Safe HTML
- `markdown_content` - Markdown
- `xss_payloads` - XSS attempts

## Prerequisites

### Required Packages
```bash
pip install pytest pytest-django pytest-xdist pytest-cov pytest-mock
```

Or via requirements:
```bash
pip install -r requirements.txt
```

### MeiliSearch Setup
Integration tests require MeiliSearch:

```bash
# Start MeiliSearch
docker-compose up -d meilisearch

# Check status
curl http://localhost:7700/health

# View logs
docker-compose logs -f meilisearch
```

**Note:** Unit tests don't require MeiliSearch (fully mocked).

## Troubleshooting

### Tests fail with "Connection refused"
→ MeiliSearch not running. Start with: `docker-compose up -d meilisearch`

### Import errors (pytest, rest_framework)
→ Install test dependencies: `pip install pytest pytest-django djangorestframework`

### Tests hang or timeout
→ Check if MeiliSearch is indexing. View stats: `curl http://localhost:7700/stats`

### Coverage too low
→ Run with verbose: `pytest --cov=apps.main --cov-report=term-missing -v`

### Database locked errors
→ Use `--reuse-db` flag: `pytest --reuse-db`

## CI/CD Integration

Add to GitHub Actions:

```yaml
- name: Start MeiliSearch
  run: docker-compose up -d meilisearch

- name: Wait for MeiliSearch
  run: |
    timeout 30 bash -c 'until curl -f http://localhost:7700/health; do sleep 1; done'

- name: Run Search Tests
  run: |
    pytest tests/unit/test_search_index.py \
           tests/integration/test_search_api.py \
           tests/integration/test_admin_reindex.py \
           --cov=apps.main \
           --cov-report=xml \
           --junitxml=test-results.xml

- name: Upload Coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
```

## Performance Benchmarks

Expected test execution times:

| Test Suite | Duration | Tests |
|------------|----------|-------|
| Unit (test_search_index.py) | ~5-10s | 50+ |
| Integration (test_search_api.py) | ~15-30s | 40+ |
| Integration (test_admin_reindex.py) | ~10-20s | 35+ |
| **Total** | **~30-60s** | **125+** |

Parallel execution (4 workers):
```bash
pytest -n 4  # ~15-30s total
```

## Next Steps

After tests pass:

1. ✓ Review coverage report: `htmlcov/index.html`
2. ✓ Add CI/CD integration (GitHub Actions)
3. ✓ Set up pre-commit hooks for tests
4. ✓ Configure test database fixtures
5. ✓ Add performance regression tests
6. ✓ Integrate with Sentry for error tracking
7. ✓ Create test data factories (factory_boy)
8. ✓ Add E2E tests with Playwright (optional)

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-django](https://pytest-django.readthedocs.io/)
- [MeiliSearch API Docs](https://www.meilisearch.com/docs/)
- [Django Testing](https://docs.djangoproject.com/en/stable/topics/testing/)
