# Type Checking Guidelines

**Created:** 2025-11-01
**Status:** Phase 17 - Baseline Established
**Related:** mypy.ini, Phase 19 Type Safety Improvements

---

## Overview

This document provides guidelines for adding and maintaining type hints in the Django project. Type hints improve code quality, IDE support, and catch bugs at development time.

---

## Current Status (Phase 17)

**Mypy Configuration:** ✅ Enabled with Django plugin
**Strict Mode:** ❌ Not yet enabled (planned for Phase 19)
**Core Modules Type Hints:** ⚠️ Partial coverage
**CI/CD Integration:** ❌ Planned for Phase 18

### Configuration

Location: `mypy.ini`

```ini
[mypy]
python_version = 3.11
plugins = mypy_django_plugin.main
warn_return_any = True
warn_unused_configs = True
check_untyped_defs = True
show_error_codes = True
```

---

## Type Hint Standards

### 1. Function Signatures

**Always add type hints to:**
- Function parameters
- Return types
- Public API methods
- View functions

```python
from typing import Optional, Dict, List, Any
from django.http import HttpRequest, HttpResponse

# ✅ GOOD
def get_user_data(user_id: int) -> Optional[Dict[str, Any]]:
    """Fetch user data by ID."""
    try:
        user = User.objects.get(id=user_id)
        return {"id": user.id, "name": user.username}
    except User.DoesNotExist:
        return None

# ✅ GOOD - View function
def profile_view(request: HttpRequest, user_id: int) -> HttpResponse:
    """Display user profile."""
    context = get_user_data(user_id)
    return render(request, "profile.html", context)

# ❌ BAD - Missing type hints
def get_user_data(user_id):
    user = User.objects.get(id=user_id)
    return {"id": user.id, "name": user.username}
```

### 2. Django-Specific Types

```python
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.db.models import QuerySet
from typing import Optional

# Models
from apps.portfolio.models import BlogPost

def get_published_posts() -> QuerySet[BlogPost]:
    """Get all published blog posts."""
    return BlogPost.objects.filter(status="published")

def post_detail(request: HttpRequest, post_id: int) -> HttpResponse:
    """Display blog post detail."""
    post: Optional[BlogPost] = BlogPost.objects.filter(id=post_id).first()
    if not post:
        return HttpResponse("Not found", status=404)
    return render(request, "post.html", {"post": post})
```

### 3. Optional vs Union

```python
from typing import Optional, Union

# ✅ Use Optional for values that can be None
def find_user(username: str) -> Optional[User]:
    try:
        return User.objects.get(username=username)
    except User.DoesNotExist:
        return None

# ✅ Use Union for multiple possible types
def format_value(value: Union[int, float, str]) -> str:
    return str(value)
```

### 4. Generic Types

```python
from typing import List, Dict, Tuple, Set

# ✅ Specify container types
def get_tag_list() -> List[str]:
    return ["python", "django", "web"]

def get_user_scores() -> Dict[str, int]:
    return {"alice": 95, "bob": 87}

def get_coordinates() -> Tuple[float, float]:
    return (40.7128, -74.0060)

# ✅ Nested generics
def get_user_tags() -> Dict[str, List[str]]:
    return {
        "user1": ["python", "django"],
        "user2": ["javascript", "react"]
    }
```

### 5. Type Aliases

```python
from typing import Dict, List, TypeAlias

# Create aliases for complex types
UserData: TypeAlias = Dict[str, Any]
TagList: TypeAlias = List[str]
UserTags: TypeAlias = Dict[str, List[str]]

def process_user(data: UserData) -> TagList:
    return data.get("tags", [])
```

---

## Common Patterns

### Pattern 1: Django QuerySet

```python
from django.db.models import QuerySet
from apps.portfolio.models import BlogPost

def get_recent_posts(limit: int = 10) -> QuerySet[BlogPost]:
    """Get recent blog posts."""
    return BlogPost.objects.order_by("-created_at")[:limit]
```

### Pattern 2: Request/Response

```python
from django.http import HttpRequest, JsonResponse
from typing import Dict, Any

def api_endpoint(request: HttpRequest) -> JsonResponse:
    """API endpoint with JSON response."""
    data: Dict[str, Any] = {
        "success": True,
        "message": "Data retrieved"
    }
    return JsonResponse(data)
```

### Pattern 3: Model Methods

```python
from django.db import models
from typing import Optional
from datetime import datetime

class BlogPost(models.Model):
    title = models.CharField(max_length=200)
    published_at = models.DateTimeField(null=True, blank=True)

    def is_published(self) -> bool:
        """Check if post is published."""
        return self.published_at is not None

    def get_publish_date(self) -> Optional[datetime]:
        """Get publish date if available."""
        return self.published_at
```

### Pattern 4: Decorators

```python
from typing import Callable, Any
from functools import wraps

def require_auth(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator requiring authentication."""
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # Authentication logic
        return func(*args, **kwargs)
    return wrapper
```

---

## Django-Specific Considerations

### 1. Model Fields with Choices

```python
from django.db import models
from typing import Literal

class BlogPost(models.Model):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("published", "Published"),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)

    # Type hint for status
    status: Literal["draft", "published"]
```

### 2. Foreign Keys

```python
from django.db import models
from typing import Optional

class Comment(models.Model):
    post = models.ForeignKey("BlogPost", on_delete=models.CASCADE)

    # Access with type hint
    post: BlogPost  # Django-stubs provides this
```

### 3. Manager Methods

```python
from django.db import models
from django.db.models import QuerySet

class BlogPostManager(models.Manager["BlogPost"]):
    def published(self) -> QuerySet["BlogPost"]:
        return self.filter(status="published")

class BlogPost(models.Model):
    objects = BlogPostManager()
```

---

## When to Skip Type Hints

### Acceptable Cases for `# type: ignore`

```python
# Django's get_*_display() methods (auto-generated)
status_display = post.get_status_display()  # type: ignore[attr-defined]

# Complex Django internals
from django.contrib.auth import get_user_model
User = get_user_model()  # type: ignore[misc]

# Third-party libraries without stubs
import some_external_lib  # type: ignore[import]
```

---

## Running Mypy

### Basic Check
```bash
python -m mypy apps/main apps/portfolio
```

### Check Specific File
```bash
python -m mypy apps/main/models.py
```

### Check with Error Codes
```bash
python -m mypy apps/ --show-error-codes
```

### Strict Mode (Phase 19)
```bash
python -m mypy apps/ --strict
```

---

## Common Mypy Errors

### Error: Need type annotation

```python
# ❌ BAD
items = []

# ✅ GOOD
items: List[str] = []
```

### Error: Missing return type

```python
# ❌ BAD
def get_data():
    return {"key": "value"}

# ✅ GOOD
def get_data() -> Dict[str, str]:
    return {"key": "value"}
```

### Error: Incompatible types

```python
# ❌ BAD
def process(value: int) -> str:
    return value  # Error: Expected str, got int

# ✅ GOOD
def process(value: int) -> str:
    return str(value)
```

---

## IDE Integration

### VS Code

1. Install Python extension
2. Enable type checking in settings:
   ```json
   {
     "python.linting.mypyEnabled": true,
     "python.linting.mypyArgs": [
       "--config-file=mypy.ini"
     ]
   }
   ```

### PyCharm

1. Settings → Tools → Python Integrated Tools
2. Select "Mypy" as type checker
3. Configure path to mypy.ini

---

## Phase 19 Roadmap

**Planned Improvements:**

1. **Strict Mode Gradual Rollout**
   - Enable `disallow_untyped_defs` per module
   - Start with utilities, then models, then views

2. **Django-Stubs Enhancement**
   - Update django-stubs to latest version
   - Resolve Django-specific type issues

3. **Type Hint Coverage**
   - Target: 80%+ coverage in core modules
   - Focus on public APIs first

4. **CI/CD Integration** (Phase 18)
   - Add mypy to GitHub Actions
   - Fail build on type errors

---

## Resources

- [Mypy Documentation](https://mypy.readthedocs.io/)
- [Python Type Hints PEP 484](https://peps.python.org/pep-0484/)
- [Django-Stubs](https://github.com/typeddjango/django-stubs)
- [Type Checking Best Practices](https://typing.readthedocs.io/)

---

**Last Updated:** 2025-11-01
**Next Review:** Phase 19 kickoff
