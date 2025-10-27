# WYSIWYG Editor Evaluation for Admin Panel

**Evaluation Date:** December 2024
**Status:** Recommendation Phase
**For:** Django Admin Panel Content Management

---

## Executive Summary

This document evaluates three leading WYSIWYG (What You See Is What You Get) editors for integration with our Django admin panel: **TinyMCE**, **CKEditor**, and **Tiptap**. The evaluation considers Django integration complexity, security features, licensing, and feature completeness.

**Recommendation:** **TinyMCE** with **django-tinymce** package for immediate needs, with **Tiptap** as future consideration for custom UI.

---

## Evaluation Criteria

| Criterion | Weight | Description |
|-----------|--------|-------------|
| **Django Integration** | 30% | Availability and quality of Django packages |
| **Security** | 25% | Built-in sanitization, XSS prevention |
| **Features** | 20% | Rich editing capabilities, plugins |
| **Licensing** | 15% | Open-source vs commercial, pricing |
| **Customization** | 10% | UI theming, custom plugins |

---

## Option 1: TinyMCE

### Overview
- **Developer:** Tiny Technologies
- **Type:** Classic WYSIWYG editor
- **Website:** https://www.tiny.cloud/
- **License:** LGPL-2.1 (Community), Commercial (Cloud)

### Django Integration

**Package:** `django-tinymce`
```bash
pip install django-tinymce
```

**Setup Complexity:** ⭐⭐⭐⭐⭐ (Excellent)

**Configuration Example:**
```python
# settings.py
INSTALLED_APPS = [
    # ...
    'tinymce',
]

TINYMCE_DEFAULT_CONFIG = {
    'height': 360,
    'width': 'auto',
    'plugins': 'advlist autolink lists link image charmap preview anchor '
               'searchreplace visualblocks code fullscreen insertdatetime '
               'media table paste code help wordcount',
    'toolbar': 'undo redo | formatselect | bold italic backcolor | '
               'alignleft aligncenter alignright alignjustify | '
               'bullist numlist outdent indent | removeformat | help',
    'menubar': True,
    'statusbar': True,
    'cleanup_on_startup': True,
    'custom_undo_redo_levels': 10,
    'entity_encoding': 'raw',  # Prevents XSS
}

# Model usage
from tinymce.models import HTMLField

class BlogPost(models.Model):
    content = HTMLField()
```

### Features

✅ **Strengths:**
- Mature, battle-tested (20+ years)
- Extensive plugin ecosystem (300+ plugins)
- Excellent documentation
- Active community support
- Image upload handling
- Spell checking built-in
- Tables, lists, and formatting
- Code syntax highlighting
- Accessibility features (ARIA support)

❌ **Weaknesses:**
- Classic UI feels dated compared to modern editors
- Cloud version requires subscription for premium features
- Self-hosted version can be heavy (250KB+ minified)

### Security Features

- **HTML Sanitization:** Built-in via `valid_elements` and `extended_valid_elements`
- **XSS Prevention:** Entity encoding, content filtering
- **CSP Compatibility:** Configurable to work with Content Security Policy

**Security Config Example:**
```python
TINYMCE_DEFAULT_CONFIG = {
    # ... other config
    'valid_elements': '*[*]',  # Or restrict to specific tags
    'invalid_elements': 'script,iframe,object,embed',
    'entity_encoding': 'raw',
    'verify_html': True,
}
```

### Licensing

- **Community (Self-hosted):** LGPL-2.1 - Free for all uses
- **Cloud:** $4.8/month (Essential) to Custom pricing (Enterprise)
- **Self-hosted Premium Plugins:** One-time fees vary

**Verdict:** ✅ Community edition sufficient for our needs

### Pros & Cons

| Pros | Cons |
|------|------|
| ✅ Best Django integration | ❌ UI feels dated |
| ✅ Comprehensive features | ❌ Large bundle size |
| ✅ Free self-hosted option | ❌ Premium features costly |
| ✅ Mature and stable | ❌ Configuration complexity |

**Overall Score:** 8.5/10

---

## Option 2: CKEditor

### Overview
- **Developer:** CKSource
- **Type:** Classic/Inline WYSIWYG editor
- **Website:** https://ckeditor.com/
- **License:** GPL-2.0+ (Classic), Commercial (CKEditor 5)

### Django Integration

**Package:** `django-ckeditor`
```bash
pip install django-ckeditor django-ckeditor-5
```

**Setup Complexity:** ⭐⭐⭐⭐ (Good)

**Configuration Example:**
```python
# settings.py
INSTALLED_APPS = [
    # ...
    'ckeditor',
    'ckeditor_uploader',  # For image uploads
]

CKEDITOR_UPLOAD_PATH = "uploads/"
CKEDITOR_IMAGE_BACKEND = "pillow"

CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': 'Full',
        'height': 300,
        'width': '100%',
        'removePlugins': 'exportpdf',
        'extraAllowedContent': 'div(*);p(*);span(*)',
    },
}

# Model usage
from ckeditor.fields import RichTextField

class BlogPost(models.Model):
    content = RichTextField()
```

### Features

✅ **Strengths:**
- Modern UI (especially CKEditor 5)
- Collaborative editing support (Premium)
- Real-time collaboration
- Markdown support
- Responsive images
- Emoji support
- Track changes (Premium)

❌ **Weaknesses:**
- CKEditor 5 Django integration less mature
- Premium features expensive
- Migration from CKEditor 4 to 5 complex

### Security Features

- **HTML Sanitization:** ACF (Advanced Content Filter)
- **XSS Prevention:** Content filtering, allowlist approach
- **CSP Support:** Compatible with strict CSP

**Security Config Example:**
```python
CKEDITOR_CONFIGS = {
    'default': {
        'removePlugins': 'flash,iframe',
        'allowedContent': True,  # Or define specific rules
        'disallowedContent': 'script; iframe',
    },
}
```

### Licensing

- **CKEditor 4 Classic:** GPL-2.0+ - Free
- **CKEditor 5:** GPL-2.0+ (Open Source) or Commercial
- **Premium Features:** $690/year per website (Basic) to Custom (Enterprise)

**Verdict:** ✅ Open-source version sufficient, but CKEditor 5 integration needs work

### Pros & Cons

| Pros | Cons |
|------|------|
| ✅ Modern UI (v5) | ❌ CKEditor 5 Django integration immature |
| ✅ Collaborative editing | ❌ Premium features expensive |
| ✅ Good documentation | ❌ Complex configuration |
| ✅ Active development | ❌ Migration path unclear |

**Overall Score:** 7.5/10

---

## Option 3: Tiptap

### Overview
- **Developer:** Tiptap GmbH
- **Type:** Headless editor framework
- **Website:** https://tiptap.dev/
- **License:** MIT (Core), Commercial (Extensions)

### Django Integration

**Package:** No official Django package (requires custom integration)

**Setup Complexity:** ⭐⭐ (Challenging)

**Implementation Approach:**
1. Use Tiptap as frontend JavaScript editor
2. Store output as JSON or HTML in Django `TextField`
3. Create custom Django widget for admin integration

**Example Implementation:**
```python
# widgets.py
from django import forms
from django.utils.safestring import mark_safe

class TiptapWidget(forms.Textarea):
    def render(self, name, value, attrs=None, renderer=None):
        html = super().render(name, value, attrs, renderer)
        return mark_safe(f'''
            <div id="tiptap-editor-{name}"></div>
            <script>
                // Initialize Tiptap editor
                // ... (requires custom JavaScript)
            </script>
            {html}
        ''')

# models.py
class BlogPost(models.Model):
    content = models.TextField()  # Stores JSON or HTML

    class Meta:
        # In admin.py, use custom widget
        pass
```

### Features

✅ **Strengths:**
- Extremely modern, React-like architecture
- Full customization (headless design)
- ProseMirror-based (powerful schema)
- Collaborative editing built-in
- Framework-agnostic
- Excellent TypeScript support
- Lightweight core

❌ **Weaknesses:**
- No official Django integration
- Requires significant custom development
- Steeper learning curve
- Premium extensions needed for full features

### Security Features

- **HTML Sanitization:** Custom schema-based filtering
- **XSS Prevention:** ProseMirror's schema prevents malicious content
- **Content Validation:** Strict schema enforcement

**Security Note:** Requires custom sanitization layer in Django backend

### Licensing

- **Core:** MIT - Free
- **Pro Extensions:** €249/year (Starter) to €2,499/year (Business)
- **Cloud:** Starting at €39/month

**Verdict:** ⚠️ Requires commercial license for best features

### Pros & Cons

| Pros | Cons |
|------|------|
| ✅ Most modern architecture | ❌ No Django integration |
| ✅ Highly customizable | ❌ Requires custom development |
| ✅ Collaborative editing | ❌ Premium extensions needed |
| ✅ Lightweight | ❌ Steeper learning curve |

**Overall Score:** 7.0/10 (would be 9/10 with official Django support)

---

## Feature Comparison Matrix

| Feature | TinyMCE | CKEditor | Tiptap |
|---------|---------|----------|--------|
| **Django Integration** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |
| **Setup Time** | 30 min | 1 hour | 4-8 hours |
| **Bundle Size (min)** | 250KB | 180KB | 45KB (core) |
| **Image Upload** | ✅ Built-in | ✅ Built-in | ⚠️ Custom |
| **Tables** | ✅ | ✅ | ✅ (Pro) |
| **Code Blocks** | ✅ | ✅ | ✅ |
| **Markdown** | ❌ | ✅ (v5) | ✅ |
| **Collaborative Editing** | ❌ | ✅ (Premium) | ✅ (Built-in) |
| **Spell Check** | ✅ | ✅ | ⚠️ Browser |
| **Accessibility (WCAG)** | ✅ Excellent | ✅ Good | ⭐ Customizable |
| **Mobile Support** | ✅ Good | ✅ Excellent | ✅ Excellent |
| **Customization** | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

---

## Recommendation

### Primary Recommendation: TinyMCE

**Why TinyMCE:**
1. ✅ **Best Django Integration:** `django-tinymce` is mature, well-documented, and actively maintained
2. ✅ **Complete Features:** Everything needed out-of-the-box without premium plugins
3. ✅ **Security:** Robust sanitization and XSS prevention built-in
4. ✅ **Free:** LGPL license allows commercial use without fees
5. ✅ **Quick Setup:** Can be production-ready in under 1 hour

**Implementation Plan:**
```bash
# 1. Install
pip install django-tinymce

# 2. Configure settings.py (see config above)

# 3. Update models
from tinymce.models import HTMLField
content = HTMLField()

# 4. Run migrations
python manage.py makemigrations
python manage.py migrate

# 5. Collect static files
python manage.py collectstatic
```

### Alternative Consideration: Tiptap (Future)

**When to Consider Tiptap:**
- If we build a custom admin UI (React/Vue frontend)
- If collaborative editing becomes critical
- If we need maximum customization
- If we can invest 1-2 weeks in custom integration

---

## Security Implementation

Regardless of editor choice, implement this sanitization layer:

### 1. Install Bleach
```bash
pip install bleach
```

### 2. Create Sanitization Utility
```python
# apps/blog/utils/sanitizer.py
import bleach
from bleach.css_sanitizer import CSSSanitizer

ALLOWED_TAGS = [
    'p', 'br', 'strong', 'em', 'u', 's', 'a', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'blockquote', 'code', 'pre', 'ul', 'ol', 'li', 'hr', 'div', 'span',
    'table', 'thead', 'tbody', 'tr', 'th', 'td', 'img'
]

ALLOWED_ATTRIBUTES = {
    '*': ['class', 'id'],
    'a': ['href', 'title', 'target', 'rel'],
    'img': ['src', 'alt', 'title', 'width', 'height'],
    'span': ['style'],
    'div': ['style'],
}

ALLOWED_STYLES = ['color', 'background-color', 'font-weight', 'text-align']

css_sanitizer = CSSSanitizer(allowed_css_properties=ALLOWED_STYLES)

def sanitize_html(content):
    """Sanitize HTML content to prevent XSS attacks"""
    return bleach.clean(
        content,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        css_sanitizer=css_sanitizer,
        strip=True
    )
```

### 3. Apply in Model Save
```python
from apps.blog.utils.sanitizer import sanitize_html

class BlogPost(models.Model):
    content = HTMLField()

    def save(self, *args, **kwargs):
        # Sanitize before saving
        self.content = sanitize_html(self.content)
        super().save(*args, **kwargs)
```

---

## Implementation Timeline

| Phase | Task | Duration |
|-------|------|----------|
| **Phase 1** | Install django-tinymce | 15 min |
| **Phase 2** | Configure settings | 30 min |
| **Phase 3** | Update blog/content models | 30 min |
| **Phase 4** | Create sanitization layer | 1 hour |
| **Phase 5** | Testing and validation | 2 hours |
| **Phase 6** | Documentation | 1 hour |

**Total Estimated Time:** 5-6 hours

---

## Next Steps

1. ✅ **Decision:** Approve TinyMCE as primary editor
2. ⏳ **Implementation:** Follow implementation plan
3. ⏳ **Security:** Implement sanitization layer
4. ⏳ **Testing:** Test with sample content
5. ⏳ **Documentation:** Update developer docs

---

**Document Status:** Ready for Decision
**Prepared by:** Development Team
**Review Date:** December 2024
