# Code Quality Standards

## Overview

This document defines the code quality standards and enforcement policies for the portfolio project. These standards ensure maintainable, secure, and performant code across the entire codebase.

## 🎯 Quality Metrics

### Cyclomatic Complexity

**Definition:** Measures the number of linearly independent paths through a program's source code.

**Standards:**
- **Maximum:** 10 (strictly enforced in CI/CD)
- **Recommended:** ≤5 for most functions
- **Warning Level:** 8-10

**Rationale:**
- Functions with complexity >10 are difficult to test and maintain
- High complexity increases bug probability
- Reduced complexity improves code readability

**Tools:**
- `flake8` with McCabe plugin (C901)
- Automated checking in CI/CD pipeline
- Pre-commit hook enforcement

**Example:**
```python
# BAD: Complexity = 12
def process_data(data, filters):
    result = []
    for item in data:
        if filters.get('type') == 'A':
            if item.value > 100:
                if item.status == 'active':
                    result.append(item)
        elif filters.get('type') == 'B':
            if item.value < 50:
                if item.status == 'pending':
                    result.append(item)
        elif filters.get('type') == 'C':
            if item.value == 75:
                result.append(item)
    return result

# GOOD: Complexity = 3 (extracted helpers)
def process_data(data, filters):
    filter_func = get_filter_function(filters)
    return [item for item in data if filter_func(item)]

def get_filter_function(filters):
    filter_type = filters.get('type')
    if filter_type == 'A':
        return lambda item: item.value > 100 and item.status == 'active'
    elif filter_type == 'B':
        return lambda item: item.value < 50 and item.status == 'pending'
    elif filter_type == 'C':
        return lambda item: item.value == 75
    return lambda item: False
```

---

### Cognitive Complexity

**Definition:** Measures how difficult code is to understand (considers nesting, breaks in linear flow).

**Standards:**
- **Maximum:** 15
- **Recommended:** ≤10 for most functions
- **Warning Level:** 12-15

**Rationale:**
- Cognitive complexity better reflects actual code readability
- Accounts for nested structures that increase mental load
- Helps identify code that needs refactoring

**Tools:**
- `radon` for cognitive complexity analysis
- CI/CD monitoring and reporting
- Pre-commit hook validation

**Cognitive Complexity Factors:**
- Each nesting level: +1
- Each break in linear flow: +1 (if/else, loops, try/except)
- Recursion: +1 per recursive call

---

### Test Coverage

**Standards:**
- **Minimum:** 85% overall coverage
- **Critical modules:** ≥90% coverage
- **New code:** ≥90% coverage required
- **Security modules:** 100% coverage recommended

**Enforcement:**
- CI/CD pipeline fails if coverage <85%
- Coverage reports generated for each PR
- Coverage badges in README

**Coverage Categories:**
- **Line Coverage:** Percentage of code lines executed
- **Branch Coverage:** Percentage of decision branches tested
- **Function Coverage:** Percentage of functions called

**Tools:**
- `pytest-cov` for coverage measurement
- HTML reports for detailed analysis
- XML reports for CI/CD integration

---

## 📋 Code Style Standards

### Python (PEP 8 + Black)

**Formatting:**
- **Line Length:** 88 characters (Black default)
- **Indentation:** 4 spaces
- **String Quotes:** Double quotes preferred
- **Trailing Commas:** Required in multi-line structures

**Tools:**
- `black` - code formatter (enforced in CI/CD)
- `isort` - import sorting
- `flake8` - linting

**Configuration:**
```python
# pyproject.toml
[tool.black]
line-length = 88
target-version = ['py311']
exclude = '''
/(
    \.venv
  | migrations
  | __pycache__
)/
'''

[tool.isort]
profile = "black"
skip = [".venv", "migrations", "__pycache__"]
```

### Naming Conventions

**Python:**
- **Functions/Variables:** `snake_case`
- **Classes:** `PascalCase`
- **Constants:** `UPPER_SNAKE_CASE`
- **Private:** `_leading_underscore`
- **Protected:** `__double_leading_underscore`

**Django:**
- **Models:** Singular `PascalCase` (e.g., `User`, `BlogPost`)
- **Views:** Descriptive names (e.g., `UserListView`, `create_blog_post`)
- **URLs:** `kebab-case` (e.g., `/blog-posts/`, `/user-profile/`)
- **Templates:** `snake_case.html` (e.g., `blog_post_detail.html`)

---

## 🔒 Security Standards

### OWASP Top 10 Compliance

All code must address OWASP Top 10 vulnerabilities:

1. **A01: Broken Access Control**
   - Enforce authorization checks in all views
   - Use Django's permission system
   - No direct object references without validation

2. **A02: Cryptographic Failures**
   - Use HTTPS in production
   - Strong password hashing (Argon2/PBKDF2)
   - No hardcoded secrets

3. **A03: Injection**
   - Use parameterized queries (Django ORM)
   - Validate/sanitize all user input
   - Escape HTML output

4. **A04: Insecure Design**
   - Security by design principles
   - Threat modeling for new features
   - Defense in depth

5. **A05: Security Misconfiguration**
   - Secure default settings
   - Remove debug mode in production
   - Keep dependencies updated

6. **A06: Vulnerable Components**
   - Regular dependency updates
   - Security scanning (Safety, Bandit)
   - Remove unused dependencies

7. **A07: Identification/Authentication Failures**
   - Strong password policy (≥12 chars)
   - Rate limiting on auth endpoints
   - Session security (HttpOnly, Secure, SameSite)

8. **A08: Software/Data Integrity Failures**
   - Code signing
   - Integrity checks for dependencies
   - Secure CI/CD pipeline

9. **A09: Security Logging/Monitoring**
   - Log all security events
   - Monitor for anomalies
   - Alerting on suspicious activity

10. **A10: Server-Side Request Forgery (SSRF)**
    - Validate URLs
    - Whitelist allowed domains
    - No user-controlled URLs

### Security Scanning

**Tools:**
- `bandit` - Python security scanner
- `safety` - dependency vulnerability checker
- `semgrep` - semantic code analysis
- OWASP ZAP - penetration testing

**Enforcement:**
- No high-severity issues allowed in production
- Medium-severity issues must be documented and tracked
- Security scans in CI/CD pipeline

---

## 📊 Performance Standards

### Response Time

**Targets:**
- **Homepage:** <1 second (p95)
- **API endpoints:** <500ms (p95)
- **Search queries:** <200ms (p95)
- **Database queries:** <50ms (p95)

### Database

**Standards:**
- **N+1 queries:** Not allowed (use `select_related`, `prefetch_related`)
- **Query count:** Max 20 queries per request
- **Index coverage:** All foreign keys and frequently queried fields
- **Migration size:** <100 operations per migration

**Tools:**
- Django Debug Toolbar (development)
- `django-query-inspector` (CI/CD)
- Database query logging

### Caching

**Requirements:**
- Cache frequently accessed data
- Use Redis for session storage
- Implement cache invalidation strategy
- Monitor cache hit rates (target: >80%)

---

## 🧪 Testing Standards

### Test Categories

1. **Unit Tests**
   - Test individual functions/methods
   - Mock external dependencies
   - Fast execution (<1ms per test)
   - Coverage: ≥90% for business logic

2. **Integration Tests**
   - Test component interactions
   - Use test database
   - Moderate execution time (<100ms per test)
   - Coverage: All critical workflows

3. **End-to-End Tests**
   - Test full user workflows
   - Use Playwright/Selenium
   - Slower execution (<5s per test)
   - Coverage: Critical user journeys

4. **Security Tests**
   - Test authentication/authorization
   - Test input validation
   - Test CSRF/XSS protection
   - Coverage: 100% for security features

### Test Quality

**Requirements:**
- **Descriptive names:** `test_user_cannot_delete_other_users_posts`
- **Arrange-Act-Assert pattern:** Clear test structure
- **No test interdependencies:** Tests must run in any order
- **Fast execution:** Total test suite <5 minutes
- **Reliable:** No flaky tests allowed

**Example:**
```python
def test_user_cannot_delete_other_users_posts():
    # Arrange
    user1 = User.objects.create(username='user1')
    user2 = User.objects.create(username='user2')
    post = BlogPost.objects.create(author=user1, title='Test')

    # Act
    client = Client()
    client.force_login(user2)
    response = client.post(f'/blog/posts/{post.id}/delete/')

    # Assert
    assert response.status_code == 403
    assert BlogPost.objects.filter(id=post.id).exists()
```

---

## 📝 Documentation Standards

### Code Documentation

**Requirements:**
- **Module docstrings:** Purpose, usage, examples
- **Function docstrings:** Args, returns, raises, examples
- **Class docstrings:** Purpose, attributes, methods
- **Complex logic:** Inline comments explaining "why"

**Format:** Google Style Docstrings

**Example:**
```python
def calculate_discount(price: float, discount_percent: float) -> float:
    """Calculate discounted price.

    Args:
        price: Original price in USD
        discount_percent: Discount percentage (0-100)

    Returns:
        Discounted price in USD

    Raises:
        ValueError: If discount_percent is not in range 0-100

    Examples:
        >>> calculate_discount(100, 10)
        90.0
        >>> calculate_discount(50, 20)
        40.0
    """
    if not 0 <= discount_percent <= 100:
        raise ValueError("Discount must be between 0 and 100")

    return price * (1 - discount_percent / 100)
```

### API Documentation

**Requirements:**
- OpenAPI/Swagger documentation
- Request/response examples
- Authentication requirements
- Error codes and messages

---

## 🔄 CI/CD Enforcement

### Quality Gates

**All checks must pass before merge:**

1. ✅ **Code Formatting**
   - Black formatting check
   - isort import sorting
   - Auto-fix on PR

2. ✅ **Linting**
   - Flake8 linting (E, F, W codes)
   - No undefined names
   - No unused imports

3. ✅ **Complexity**
   - Cyclomatic complexity ≤10
   - Cognitive complexity ≤15
   - Radon analysis

4. ✅ **Type Checking**
   - Mypy type checking (warning only)
   - Type hints for public APIs

5. ✅ **Security**
   - Bandit security scan
   - No high-severity issues
   - Safety dependency check

6. ✅ **Testing**
   - All tests pass
   - Coverage ≥85%
   - No flaky tests

7. ✅ **Performance**
   - No N+1 queries
   - Response time targets met
   - No memory leaks

### Progressive Enforcement

**Phase 1 (Completed):**
- ✅ Max complexity: 25 → 18 → 12 → 10
- ✅ Coverage: 80% → 85%

**Phase 2 (Current):**
- ✅ Security: All OWASP Top 10 addressed
- ✅ CI/CD: Automated security scanning

**Phase 3 (Next):**
- Performance: Response time monitoring
- Caching: Redis integration

---

## 🛠️ Development Tools

### Required Tools

**Python:**
- `black` - Code formatter
- `isort` - Import sorter
- `flake8` - Linter
- `mypy` - Type checker
- `pytest` - Test runner
- `radon` - Complexity analyzer

**Security:**
- `bandit` - Security scanner
- `safety` - Dependency checker
- `semgrep` - Semantic analyzer

**Git:**
- `pre-commit` - Git hooks
- Commit message linter

### IDE Configuration

**VS Code Settings:**
```json
{
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.linting.mypyEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
```

---

## 📈 Monitoring & Reporting

### Metrics Dashboard

**Track:**
- Average cyclomatic complexity (target: <5)
- Test coverage trend (target: ≥85%)
- Security vulnerabilities (target: 0 high)
- Code duplication (target: <5%)
- Technical debt ratio (target: <5%)

### Quality Reports

**Generated:**
- Daily: Complexity report
- Weekly: Full quality scan
- Per PR: Coverage and security report
- Monthly: Technical debt assessment

---

## ✅ Checklist: New Code

Before submitting code, verify:

- [ ] All tests pass locally
- [ ] Coverage ≥85% (≥90% for new code)
- [ ] No complexity violations (C≤10)
- [ ] No security issues (Bandit clean)
- [ ] Code formatted (Black + isort)
- [ ] Type hints added for public APIs
- [ ] Docstrings for all public functions
- [ ] No N+1 database queries
- [ ] Pre-commit hooks pass
- [ ] CI/CD pipeline passes

---

## 📚 References

- [PEP 8 – Style Guide for Python Code](https://peps.python.org/pep-0008/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Django Security Best Practices](https://docs.djangoproject.com/en/stable/topics/security/)
- [Cyclomatic Complexity](https://en.wikipedia.org/wiki/Cyclomatic_complexity)
- [Cognitive Complexity](https://www.sonarsource.com/docs/CognitiveComplexity.pdf)

---

**Document Version:** 1.0
**Last Updated:** November 2, 2025
**Maintainer:** Development Team
