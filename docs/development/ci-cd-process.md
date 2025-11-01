# CI/CD Pipeline Documentation

**Last Updated:** 2025-11-01
**Version:** 1.0
**Workflows:** ci-pipeline.yml, code-quality.yml

---

## Overview

This project uses **GitHub Actions** for continuous integration and deployment. The CI/CD pipeline automatically runs tests, code quality checks, and generates reports on every push and pull request.

## Workflows

### 1. **CI/CD Pipeline** (`ci-pipeline.yml`)

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches
- Manual workflow dispatch

**Features:**
- ✅ **Smart Change Detection:** Only runs relevant tests based on changed files
- ✅ **Parallel Execution:** Multiple test suites run concurrently
- ✅ **Conditional Tests:** Python, JavaScript, E2E, Lighthouse tests run conditionally
- ✅ **Performance Metrics:** Tracks execution time for optimization
- ✅ **Artifact Storage:** Test reports stored for 30 days

**Jobs:**
1. **detect-changes** 🔍
   - Detects which files changed (Python, JS, CSS, templates, tests)
   - Outputs: boolean flags for each file type
   - Duration: ~10 seconds

2. **python-tests** 🐍
   - Matrix strategy: unit, integration, security tests
   - Coverage reporting with HTML/XML output
   - Runs only if Python or test files changed
   - Duration: ~2-5 minutes per suite

3. **javascript-tests** 🟨
   - Jest test suite with coverage
   - JSON and HTML reports
   - Runs only if JS files changed
   - Duration: ~1-2 minutes

4. **e2e-tests** 🎭
   - Playwright tests on Chromium and Firefox
   - Visual regression testing
   - Screenshot artifacts on failure
   - Duration: ~3-8 minutes per browser

5. **lighthouse-tests** 💡
   - Performance, accessibility, SEO checks
   - Budget enforcement
   - HTML reports with scores
   - Duration: ~2-4 minutes

6. **generate-reports** 📊
   - Consolidates all test results
   - Creates HTML summary report
   - GitHub Step Summary with metrics
   - Duration: ~30 seconds

7. **collect-metrics** 📈
   - Tracks pipeline execution time
   - JSON metrics for analysis
   - Conditional execution stats
   - Duration: ~10 seconds

---

### 2. **Code Quality** (`code-quality.yml`)

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches
- Manual workflow dispatch

**Features:**
- ✅ **Comprehensive Quality Checks:** Formatting, linting, type checking, security
- ✅ **Auto-fix on PR:** Black/isort auto-formatting commits
- ✅ **Quality Gate:** Fails if critical checks don't pass
- ✅ **Coverage Enforcement:** Minimum 85% coverage required
- ✅ **PR Comments:** Coverage badge and summary posted automatically

**Jobs:**
1. **formatting** 🎨
   - Checks Black and isort compliance
   - Auto-fixes on pull requests (commits back)
   - Duration: ~30-60 seconds

2. **flake8** 🔍
   - PEP 8 style checking
   - GitHub Annotations for errors
   - HTML report generation
   - Duration: ~20-40 seconds

3. **mypy** 🔍
   - Static type checking
   - HTML report with error details
   - Non-blocking (warning only)
   - Duration: ~40-90 seconds

4. **bandit** 🔒
   - Security vulnerability scanning
   - JSON and HTML reports
   - Fails on HIGH severity issues
   - Duration: ~30-60 seconds

5. **coverage** 📊
   - Pytest with coverage measurement
   - ≥85% threshold enforced
   - Dynamic coverage badge generation
   - PR comment with results
   - Duration: ~2-5 minutes

6. **quality-gate** 🚦
   - Summary of all checks
   - Pass/fail status
   - Consolidated report
   - Duration: ~20 seconds

---

## Trigger Conditions

### Automatic Triggers

| Event | Branches | Conditions |
|-------|----------|------------|
| Push | `main`, `develop` | Every commit |
| Pull Request | `main`, `develop` | Every PR update |
| Schedule | N/A | Weekly (Lighthouse only) |

### Manual Triggers

Both workflows support **workflow_dispatch** for manual runs:

```bash
# Via GitHub UI
GitHub Repository → Actions → Select Workflow → Run workflow

# Via GitHub CLI
gh workflow run ci-pipeline.yml
gh workflow run code-quality.yml
```

---

## Conditional Execution

### Change Detection Logic

The CI pipeline uses `dorny/paths-filter` to detect changes:

```yaml
python:
  - '**/*.py'
  - 'requirements*.txt'
  - 'pyproject.toml'

javascript:
  - 'static/js/**'
  - 'frontend/**/*.js'
  - 'package.json'

css:
  - 'static/css/**'
  - 'tailwind.config.js'

templates:
  - 'templates/**/*.html'
```

### Execution Matrix

| Changed Files | Python Tests | JS Tests | E2E Tests | Lighthouse |
|---------------|--------------|----------|-----------|------------|
| Python only | ✅ | ❌ | ✅ | ❌ |
| JS only | ❌ | ✅ | ✅ | ✅ |
| CSS only | ❌ | ❌ | ❌ | ✅ |
| Templates | ❌ | ❌ | ✅ | ✅ |
| Tests | ✅ | ✅ | ✅ | ❌ |
| Multiple | Smart combination | Smart combination | Smart combination | Smart combination |

**Benefits:**
- ⚡ Faster CI runs (skip irrelevant tests)
- 💰 Reduced GitHub Actions minutes usage
- 🎯 Focused feedback (only relevant failures)

---

## Artifacts & Reports

### Artifact Retention

| Artifact Type | Retention | Size (approx) |
|---------------|-----------|---------------|
| Test Reports | 30 days | 5-20 MB |
| Coverage Reports | 30 days | 2-10 MB |
| Lighthouse Reports | 30 days | 1-5 MB |
| Quality Reports | 30 days | 1-3 MB |
| Pipeline Metrics | 90 days | <1 MB |
| Consolidated Reports | 30 days | 3-8 MB |

### Accessing Artifacts

**Via GitHub UI:**
1. Go to Actions tab
2. Select workflow run
3. Scroll to "Artifacts" section
4. Download ZIP file

**Via GitHub CLI:**
```bash
# List artifacts
gh run view <run-id>

# Download artifact
gh run download <run-id> -n <artifact-name>
```

### Report Types

**1. Pytest HTML Reports**
- File: `pytest-{suite}-results.html`
- Content: Test results with pass/fail status
- Features: Self-contained, searchable, filtering

**2. Coverage Reports**
- File: `htmlcov/index.html`
- Content: Line-by-line coverage visualization
- Features: Branch coverage, missing lines highlighted

**3. Flake8 Reports**
- File: `reports/flake8/index.html`
- Content: Style violations by file
- Features: Error codes, line numbers, context

**4. Mypy Reports**
- File: `reports/mypy/index.html`
- Content: Type errors with explanations
- Features: Error codes, suggestions

**5. Bandit Reports**
- File: `reports/bandit-report.html`
- Content: Security vulnerabilities
- Features: Severity levels, CWE references

**6. Playwright Reports**
- File: `playwright-report/index.html`
- Content: E2E test results with screenshots
- Features: Video recordings (on failure), traces

**7. Lighthouse Reports**
- File: `.lighthouseci/lhr-{page}.html`
- Content: Performance scores, opportunities
- Features: Metrics, audits, filmstrip view

---

## Quality Gates

### Code Quality Gate

| Check | Requirement | Blocking? |
|-------|-------------|-----------|
| Black Formatting | 100% compliance | ✅ Yes |
| Isort Formatting | 100% compliance | ✅ Yes |
| Flake8 (E/F series) | Zero errors | ✅ Yes |
| Flake8 (W series) | Warnings allowed | ❌ No |
| Mypy Type Checking | No critical errors | ⚠️ Warning only |
| Bandit Security | Zero HIGH severity | ✅ Yes |
| Test Coverage | ≥85% | ✅ Yes |

**Quality Gate Pass Criteria:**
- ✅ Formatting: passed
- ✅ Flake8: passed
- ⚠️ Mypy: passed or warning
- ✅ Bandit: passed (no HIGH severity)
- ✅ Coverage: ≥85%

### Test Coverage Gate

```python
# Enforced in code-quality.yml
--cov-fail-under=85

# Badge colors
85-100%: Green (brightgreen)
70-84%:  Yellow
0-69%:   Red
```

**Coverage Exemptions:**
- Migrations: `*/migrations/*`
- Tests themselves: `*/tests/*`
- Third-party: `*/site-packages/*`
- Config files: `*/__pycache__/*`

---

## Environment Variables

### Required Secrets

| Secret | Used In | Purpose |
|--------|---------|---------|
| `GITHUB_TOKEN` | All workflows | GitHub API access (auto-provided) |

### Optional Secrets (for notifications)

| Secret | Used In | Purpose |
|--------|---------|---------|
| `SLACK_WEBHOOK_URL` | Notifications | Slack alerts |
| `DISCORD_WEBHOOK_URL` | Notifications | Discord alerts |

**Setting Secrets:**
```bash
GitHub Repository → Settings → Secrets and variables → Actions → New repository secret
```

### Workflow Environment Variables

```yaml
env:
  PYTHON_VERSION: '3.14'
  NODE_VERSION: '20'
  DJANGO_SETTINGS_MODULE: project.settings
  SECRET_KEY: test-secret-key-for-ci
```

---

## Best Practices

### ✅ DO

1. **Run checks locally before pushing:**
   ```powershell
   .\make.ps1 check-quick  # Fast local check
   .\make.ps1 check-all    # Full check (slower)
   ```

2. **Use conventional commits:**
   ```bash
   feat: add new feature
   fix: resolve bug
   docs: update documentation
   style: formatting changes
   refactor: code restructuring
   test: add tests
   chore: maintenance tasks
   ```

3. **Keep PRs small:**
   - Target: <500 lines changed
   - Easier to review
   - Faster CI execution

4. **Review CI failures immediately:**
   - Don't ignore red builds
   - Fix issues before next commit
   - Use "Re-run failed jobs" if flaky

5. **Monitor CI performance:**
   - Check "collect-metrics" job
   - Optimize slow tests
   - Report issues if >10 minutes

### ❌ DON'T

1. **Don't skip pre-commit hooks:**
   - Catches issues early
   - Saves CI time
   - Prevents failed builds

2. **Don't commit with --no-verify:**
   - Only for emergencies
   - Always create follow-up ticket

3. **Don't ignore coverage drops:**
   - Add tests for new code
   - Maintain ≥85% threshold

4. **Don't push directly to main:**
   - Always use pull requests
   - Get code review
   - Let CI validate

5. **Don't commit large files:**
   - Use `.gitignore`
   - Check-added-large-files hook catches these

---

## Troubleshooting

### Problem: CI fails on "Black formatting"

**Solution:**
```powershell
# Run Black locally
.\make.ps1 format

# Or manually
black . --exclude="\.venv-1|\.venv|node_modules|staticfiles|migrations|__pycache__"

# Commit and push
git add -A
git commit -m "style: apply Black formatting"
git push
```

### Problem: Coverage below 85%

**Solution:**
```powershell
# Run coverage locally
.\make.ps1 test-coverage

# Open report
start htmlcov/index.html

# Find uncovered lines (red)
# Write tests for those lines

# Re-run
pytest --cov=apps --cov-report=term-missing
```

### Problem: Flake8 errors

**Solution:**
```powershell
# Run Flake8 locally
.\make.ps1 lint

# Fix errors one by one
# Common fixes:
# - E302: Add 2 blank lines before class/function
# - E501: Shorten line (88 chars max)
# - F401: Remove unused import
# - F841: Remove unused variable or use it
```

### Problem: Bandit HIGH severity

**Solution:**
```powershell
# Run Bandit locally
.\make.ps1 security

# Review JSON report
cat bandit-report.json | jq '.results[] | select(.issue_severity == "HIGH")'

# Fix identified issues
# Common:
# - B201: flask_debug_true
# - B404: subprocess_without_shell_equals_true
# - B608: sql_injection
```

### Problem: E2E tests flaky

**Solution:**
1. **Check screenshots:** Download `playwright-report` artifact
2. **Increase timeouts:** Edit `playwright.config.js`
3. **Add waits:** Use `page.waitForSelector()`
4. **Re-run:** Click "Re-run failed jobs"

### Problem: CI runs too long (>10 min)

**Solution:**
1. **Check metrics:** Download `pipeline-metrics` artifact
2. **Identify slow jobs:** Look at duration JSON
3. **Optimize tests:** Parallelize, mock, use fixtures
4. **Report:** Create issue if infrastructure problem

---

## Monitoring & Metrics

### Pipeline Metrics

Collected in `pipeline-metrics.json`:

```json
{
  "workflow_id": "12345",
  "run_number": 42,
  "branch": "main",
  "total_duration_seconds": 345,
  "jobs": {
    "python_tests": "success",
    "javascript_tests": "skipped",
    "e2e_tests": "success"
  },
  "changes_detected": {
    "python": "true",
    "javascript": "false"
  }
}
```

### Performance Targets

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Total CI Duration | <10 min | ~8 min | ✅ |
| Python Tests | <5 min | ~3 min | ✅ |
| E2E Tests | <8 min | ~6 min | ✅ |
| Code Quality | <3 min | ~2 min | ✅ |
| Artifact Upload | <1 min | ~30s | ✅ |

### Success Rate

**Target:** ≥95% (excluding external failures)

**Monitoring:**
```bash
# Via GitHub UI
Actions → Workflows → View workflow → Insights

# Via GitHub CLI
gh run list --workflow=ci-pipeline.yml --limit=100 --json status,conclusion
```

---

## Maintenance

### Weekly Tasks

- [ ] Review failed builds (if any)
- [ ] Check artifact storage usage
- [ ] Monitor CI duration trends
- [ ] Update dependencies (`pre-commit autoupdate`)

### Monthly Tasks

- [ ] Review and update workflow versions
- [ ] Audit test coverage trends
- [ ] Optimize slow tests
- [ ] Clean up old workflow runs (GitHub auto-cleans after 90 days)

### Quarterly Tasks

- [ ] Major dependency updates
- [ ] Evaluate new GitHub Actions features
- [ ] Performance optimization review
- [ ] Documentation updates

---

## Integration with Local Development

### Pre-commit Hooks ↔ CI/CD

| Check | Pre-commit | CI/CD |
|-------|------------|-------|
| Black | ✅ Auto-fix | ✅ Verify |
| Isort | ✅ Auto-fix | ✅ Verify |
| Flake8 | ✅ Check | ✅ Check + Report |
| Mypy | ✅ Check | ✅ Check + Report |
| Bandit | ✅ Check | ✅ Check + Report |
| Tests | ❌ | ✅ Full suite |

**Philosophy:** Pre-commit catches issues early; CI provides final validation.

### make.ps1 Commands ↔ CI Jobs

| Local Command | CI Job Equivalent |
|---------------|-------------------|
| `.\make.ps1 format` | `formatting` job |
| `.\make.ps1 lint` | `flake8` + `mypy` jobs |
| `.\make.ps1 security` | `bandit` job |
| `.\make.ps1 test-coverage` | `coverage` job |
| `.\make.ps1 check-all` | `quality-gate` job |

**Tip:** Run `.\make.ps1 check-all` before pushing to catch issues early.

---

## Support & Resources

**Documentation:**
- Pre-commit setup: `docs/development/pre-commit-setup.md`
- Testing guide: `docs/development/testing-standards.md`
- Code quality standards: `docs/development/code-quality-standards.md`

**Workflow Files:**
- CI Pipeline: `.github/workflows/ci-pipeline.yml`
- Code Quality: `.github/workflows/code-quality.yml`
- Weekly Lighthouse: `.github/workflows/weekly-lighthouse.yml`

**External Resources:**
- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [Pytest Documentation](https://docs.pytest.org/)
- [Black Documentation](https://black.readthedocs.io/)
- [Playwright Documentation](https://playwright.dev/)

**Need Help?**
- Check troubleshooting section above
- Review recent workflow runs for patterns
- Open issue in repository
- Contact DevOps team

---

**Last Updated:** 2025-11-01
**Next Review:** 2025-12-01
**Maintained by:** Development Team
