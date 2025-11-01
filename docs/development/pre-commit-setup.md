# Pre-Commit Hooks Setup Guide

**Last Updated:** 2025-11-01
**For:** Django Portfolio Project
**Pre-commit Version:** 4.3.0+

---

## Overview

This project uses pre-commit hooks to automatically check code quality before commits. All hooks run automatically when you `git commit`.

## Quick Setup

```powershell
# 1. Install pre-commit (if not already installed)
pip install pre-commit

# 2. Install git hooks
pre-commit install

# 3. (Optional) Run on all files
pre-commit run --all-files
```

---

## Installed Hooks

### 🎨 Code Formatting

**Black** - Python code formatter
- Auto-formats Python code to PEP 8 style
- Line length: 88 characters
- Excludes: `migrations/`

**isort** - Import sorter
- Organizes imports alphabetically
- Groups: stdlib → third-party → local
- Excludes: `migrations/`

### 🔍 Linting & Type Checking

**Flake8** - Python linter
- Checks PEP 8 style violations
- Additional plugins:
  - `flake8-docstrings` - Docstring checks
  - `flake8-bugbear` - Bug detection
  - `flake8-comprehensions` - List/dict comprehension checks
- Excludes: `migrations/`

**Mypy** - Static type checker
- Verifies Python type hints
- Uses `django-stubs` for Django support
- Config: `mypy.ini`
- Excludes: `migrations/`

**Pydocstyle** - Docstring style checker
- Enforces PEP 257 docstring conventions
- Excludes: `migrations/`

### 🔒 Security

**Bandit** - Security vulnerability scanner
- Detects common security issues
- Level: Medium and High severity
- Excludes: `tests/`

### ✅ General Checks

**Pre-commit hooks:**
- `trailing-whitespace` - Removes trailing whitespace
- `end-of-file-fixer` - Ensures newline at EOF
- `check-yaml` - Validates YAML syntax
- `check-toml` - Validates TOML syntax
- `check-added-large-files` - Prevents large file commits
- `check-merge-conflict` - Detects merge conflict markers
- `debug-statements` - Finds debug print/pdb statements
- `check-ast` - Verifies Python AST validity

### 🌐 Frontend Checks (if applicable)

**stylelint** - CSS linter
- Auto-fixes CSS/SCSS issues
- Runs on: `*.css`, `*.scss`

**ESLint** - JavaScript linter
- Auto-fixes JS issues
- Runs on: `*.js`

### 🐍 Django-Specific

**django-check** - Django system check
- Runs: `python manage.py check`
- Validates Django configuration

**django-check-migrations** - Migration check
- Runs: `python manage.py makemigrations --check --dry-run`
- Detects missing migrations
- Triggers on: `models.py` changes

---

## Usage

### Automatic (Recommended)

Pre-commit runs automatically on `git commit`:

```powershell
git add .
git commit -m "Your commit message"
# Hooks run automatically here
```

### Manual Run

```powershell
# Run on staged files only
pre-commit run

# Run on all files
pre-commit run --all-files

# Run specific hook
pre-commit run black
pre-commit run flake8
pre-commit run mypy

# Run with verbose output
pre-commit run --all-files --verbose
```

### Skip Hooks (Emergency Only)

```powershell
# Skip all hooks (NOT RECOMMENDED)
git commit -m "Emergency fix" --no-verify

# Skip specific hook
SKIP=flake8 git commit -m "Your message"

# Skip multiple hooks
SKIP=flake8,mypy git commit -m "Your message"
```

⚠️ **Warning:** Only skip hooks if absolutely necessary. Always fix issues properly.

---

## Troubleshooting

### Problem: Hook fails with "command not found"

**Solution:**
```powershell
# Reinstall dependencies
pip install pre-commit black isort flake8 mypy bandit pydocstyle
pre-commit install --install-hooks
```

### Problem: Mypy fails with import errors

**Solution:**
```powershell
# Install type stubs
pip install django-stubs types-requests

# Or update mypy config
# Edit mypy.ini: Set ignore_missing_imports = True
```

### Problem: Pre-commit is too slow

**Solutions:**
1. **Run only on changed files** (default behavior)
2. **Skip slow hooks during development:**
   ```powershell
   SKIP=mypy,bandit git commit -m "WIP"
   ```
3. **Use parallel execution** (already configured)
4. **Run expensive checks in CI only** (Phase 18.3)

### Problem: Hooks fail on Windows

**Solution:**
```powershell
# Use PowerShell (not CMD)
# Ensure Python scripts are in PATH
$env:PATH += ";C:\Python314\Scripts"

# Reinstall pre-commit
pip uninstall pre-commit
pip install pre-commit
pre-commit install
```

### Problem: Django checks fail

**Solution:**
```powershell
# Ensure Django settings are accessible
$env:DJANGO_SETTINGS_MODULE = "project.settings"

# Run Django check manually
python manage.py check
```

### Problem: "ValueError: bad marshal data" or cache errors

**Solution:**
```powershell
# Clean pre-commit cache
pre-commit clean
pre-commit uninstall
pre-commit install
```

---

## Configuration Files

### `.pre-commit-config.yaml`
Main configuration file for all hooks. Located in project root.

**Key Sections:**
- `repos`: List of hook repositories
- `hooks`: Individual hook configurations
- `exclude`: Files/folders to skip
- `additional_dependencies`: Extra packages for hooks

**Updating Hook Versions:**
```powershell
# Auto-update to latest versions
pre-commit autoupdate

# Then commit the changes
git add .pre-commit-config.yaml
git commit -m "chore: update pre-commit hooks"
```

### `mypy.ini`
Mypy type checking configuration.

**Key Settings:**
- `python_version = 3.11`
- `plugins = mypy_django_plugin.main`
- `ignore_missing_imports = True`

### `.flake8` or `setup.cfg`
Flake8 configuration (if exists).

---

## Best Practices

### ✅ DO

1. **Run hooks before pushing:**
   ```powershell
   pre-commit run --all-files
   git push
   ```

2. **Fix issues immediately:**
   - Black/isort auto-fix → Just re-commit
   - Flake8/mypy errors → Fix code, then commit

3. **Update hooks regularly:**
   ```powershell
   pre-commit autoupdate
   ```

4. **Use project's make.ps1 script:**
   ```powershell
   .\make.ps1 check-quick  # Format + lint
   .\make.ps1 check-all    # Full quality check
   ```

### ❌ DON'T

1. **Don't skip hooks habitually**
   - Breaks code quality standards
   - Causes CI failures

2. **Don't commit with `--no-verify` unless emergency**
   - Use for hotfixes only
   - Always create follow-up ticket to fix properly

3. **Don't ignore hook failures**
   - If hook fails, there's a reason
   - Fix the underlying issue

---

## Integration with CI/CD

Pre-commit hooks are the **first line of defense**. CI/CD (Phase 18.3) provides the **second line**:

| Check | Pre-commit | CI/CD |
|-------|------------|-------|
| Black | ✅ Auto-fix | ✅ Verify |
| Isort | ✅ Auto-fix | ✅ Verify |
| Flake8 | ✅ Check | ✅ Check + Report |
| Mypy | ✅ Check | ✅ Check + Report |
| Bandit | ✅ Check | ✅ Check + Report |
| Tests | ❌ | ✅ Full suite |
| Coverage | ❌ | ✅ ≥85% required |

**Philosophy:** Catch issues locally before they reach CI.

---

## Performance Optimization

### Current Configuration

Pre-commit is already optimized for performance:

1. **Parallel Execution:** Multiple hooks run concurrently
2. **Caching:** Results cached between runs
3. **Selective Running:** Only runs on changed files
4. **Fast Hooks First:** Quick checks (trailing-whitespace) run before slow ones (mypy)

### Execution Time Benchmarks

| Hook | Approximate Time | Notes |
|------|------------------|-------|
| trailing-whitespace | <1s | Very fast |
| black | 2-5s | Fast |
| isort | 2-4s | Fast |
| flake8 | 5-10s | Medium |
| mypy | 10-30s | Slow (first run) |
| bandit | 5-15s | Medium |
| Django checks | 3-8s | Medium |

**Total (all hooks):** ~30-60 seconds on full codebase
**Total (changed files only):** ~5-15 seconds

### Speed Up Development

For rapid development cycles:

```powershell
# Option 1: Use make.ps1 for quick checks
.\make.ps1 format  # Just formatting (fast)
.\make.ps1 lint    # Format + lint (medium)

# Option 2: Skip slow hooks temporarily
SKIP=mypy,bandit git commit -m "WIP: feature X"

# Option 3: Run expensive checks less frequently
# - Run mypy/bandit manually before pushing
# - Let CI catch remaining issues
```

---

## Adding New Hooks

To add a new hook:

1. **Edit `.pre-commit-config.yaml`:**
   ```yaml
   - repo: https://github.com/example/hook-repo
     rev: v1.0.0
     hooks:
       - id: hook-name
         exclude: migrations/
   ```

2. **Install the hook:**
   ```powershell
   pre-commit install --install-hooks
   ```

3. **Test it:**
   ```powershell
   pre-commit run hook-name --all-files
   ```

4. **Document it:** Update this guide

---

## For New Developers

### First-Time Setup

```powershell
# 1. Clone repository
git clone https://github.com/waldseelen/hp.git
cd hp

# 2. Create virtual environment
python -m venv .venv-1
.venv-1\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install pre-commit hooks
pip install pre-commit
pre-commit install

# 5. Run initial check (optional but recommended)
pre-commit run --all-files
```

### Daily Workflow

```powershell
# 1. Make changes
# 2. Stage files
git add .

# 3. Commit (hooks run automatically)
git commit -m "feat: add new feature"

# 4. If hooks fail:
#    - Review output
#    - Fix issues
#    - Stage changes
#    - Commit again
```

---

## Support

**Issues with pre-commit?**
- Check this guide's Troubleshooting section
- Run: `pre-commit run --verbose` for detailed output
- Ask team for help
- See official docs: https://pre-commit.com

**Issues with specific hooks?**
- Black: https://black.readthedocs.io
- Flake8: https://flake8.pycqa.org
- Mypy: https://mypy.readthedocs.io
- Bandit: https://bandit.readthedocs.io

---

## Changelog

### 2025-11-01 - Phase 18.2
- ✅ Pre-commit installed and configured
- ✅ All hooks tested and working
- ✅ Documentation created
- ✅ Integration with make.ps1 script
- ✅ Mypy and Bandit hooks already configured
- ✅ Django-specific hooks operational

---

**Next Steps:** Phase 18.3 - CI/CD Pipeline Setup
