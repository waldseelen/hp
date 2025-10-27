# Django-parler Multilingual Content PoC Plan

**Plan Date:** December 2024
**Status:** Proof of Concept Phase
**Objective:** Implement multilingual content management using django-parler

---

## Executive Summary

This document outlines a Proof of Concept (PoC) plan for implementing **django-parler** to enable multilingual content management across our Django application. The PoC will focus on the Blog app as a testbed before broader deployment.

**Timeline:** 1-2 weeks
**Risk Level:** Low (non-destructive, can be rolled back)
**Success Criteria:** Blog posts editable in both Turkish and English with seamless admin integration

---

## What is Django-parler?

**django-parler** is a Django model translation library that:
- Stores translations in separate database tables
- Provides simple API for accessing translations
- Integrates seamlessly with Django admin
- Supports fallback languages
- Maintains separate URLs per language

**Documentation:** https://django-parler.readthedocs.io/

---

## Installation & Setup

### Step 1: Install Package

```bash
pip install django-parler
```

**Version:** 2.3+ recommended

### Step 2: Add to INSTALLED_APPS

```python
# settings.py
INSTALLED_APPS = [
    # ... existing apps
    'parler',
    'apps.blog',
    # ... other apps
]
```

### Step 3: Configure Languages

```python
# settings.py
from django.utils.translation import gettext_lazy as _

# Languages supported by the application
LANGUAGES = [
    ('en', _('English')),
    ('tr', _('Turkish')),
]

LANGUAGE_CODE = 'tr'  # Default language

# Parler configuration
PARLER_LANGUAGES = {
    None: (
        {'code': 'en'},
        {'code': 'tr'},
    ),
    'default': {
        'fallbacks': ['en'],          # Fallback if translation missing
        'hide_untranslated': False,   # Show content even if not translated
    }
}

# Enable i18n
USE_I18N = True
USE_L10N = True
```

---

## PoC Scope: Blog App

We'll implement django-parler for the Blog app first as a controlled test.

### Current Blog Model

```python
# apps/blog/models.py (CURRENT)
class Post(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    excerpt = models.TextField(blank=True)
    content = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    published_at = models.DateTimeField(null=True, blank=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### New Parler-Enabled Model

```python
# apps/blog/models.py (NEW)
from parler.models import TranslatableModel, TranslatedFields

class Post(TranslatableModel):
    # Non-translatable fields (same across all languages)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Translatable fields (separate per language)
    translations = TranslatedFields(
        title=models.CharField(_('Title'), max_length=200),
        slug=models.SlugField(_('Slug'), unique=True),
        excerpt=models.TextField(_('Excerpt'), blank=True),
        content=models.TextField(_('Content')),
    )

    class Meta:
        verbose_name = _('Blog Post')
        verbose_name_plural = _('Blog Posts')
        ordering = ['-published_at']

    def __str__(self):
        return self.safe_translation_getter('title', any_language=True) or f"Post #{self.pk}"

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('blog:post_detail', kwargs={'slug': self.slug})
```

**Database Impact:**
- Creates new table: `blog_post_translation`
- Original `blog_post` table keeps non-translatable fields
- Translation table has: `id`, `master_id`, `language_code`, `title`, `slug`, `excerpt`, `content`

---

## Migration Strategy

### Phase 1: Create Migrations

```bash
# 1. Create new model structure
python manage.py makemigrations blog

# 2. Apply migrations
python manage.py migrate blog
```

### Phase 2: Data Migration

Create custom migration to move existing data to translations:

```python
# apps/blog/migrations/0002_migrate_to_parler.py
from django.db import migrations

def migrate_existing_posts(apps, schema_editor):
    """Migrate existing Post data to translation tables"""
    Post = apps.get_model('blog', 'Post')
    PostTranslation = apps.get_model('blog', 'PostTranslation')

    for post in Post.objects.all():
        # Create Turkish translation (default language)
        PostTranslation.objects.create(
            master_id=post.id,
            language_code='tr',
            title=post.title,
            slug=post.slug,
            excerpt=post.excerpt or '',
            content=post.content,
        )

        # Optionally create placeholder English translation
        # Or leave empty for manual translation

class Migration(migrations.Migration):
    dependencies = [
        ('blog', '0001_add_parler_fields'),
    ]

    operations = [
        migrations.RunPython(migrate_existing_posts),
    ]
```

### Phase 3: Rollback Plan (if needed)

```python
# Create reverse migration to restore original structure
# Keep original data backup before starting PoC
```

---

## Admin Integration

### Current Admin

```python
# apps/blog/admin.py (CURRENT)
@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'status', 'published_at']
    list_filter = ['status', 'created_at']
    search_fields = ['title', 'content']
    prepopulated_fields = {'slug': ('title',)}
```

### Parler-Enabled Admin

```python
# apps/blog/admin.py (NEW)
from parler.admin import TranslatableAdmin

@admin.register(Post)
class PostAdmin(TranslatableAdmin):
    list_display = ['title', 'author', 'status', 'published_at', 'language_column']
    list_filter = ['status', 'created_at']

    # Parler-specific settings
    fieldsets = (
        (_('Content'), {
            'fields': ('title', 'slug', 'excerpt', 'content'),
        }),
        (_('Publishing'), {
            'fields': ('author', 'status', 'published_at'),
        }),
    )

    def get_prepopulated_fields(self, request, obj=None):
        return {'slug': ('title',)}
```

**Admin Features:**
- Language tabs at the top of edit form
- Switch between languages to edit translations
- Visual indicator of translated vs untranslated content
- Bulk translation actions

---

## Usage Examples

### Accessing Translations in Views

```python
# views.py
from django.utils.translation import get_language

def post_detail(request, slug):
    # Automatically uses current language
    post = Post.objects.translated(get_language()).get(slug=slug)
    # OR
    post = Post.objects.get(slug=slug)  # Uses current active language

    # Access specific language
    post.set_current_language('en')
    english_title = post.title

    post.set_current_language('tr')
    turkish_title = post.title

    # Safe access with fallback
    title = post.safe_translation_getter('title', any_language=True)

    context = {'post': post}
    return render(request, 'blog/post_detail.html', context)
```

### In Templates

```django
{# blog/post_detail.html #}
{% load i18n %}

<article>
    <h1>{{ post.title }}</h1>  {# Automatically in current language #}
    <div class="content">
        {{ post.content|safe }}
    </div>

    {# Language switcher #}
    <div class="language-switcher">
        {% get_available_languages as languages %}
        {% for lang_code, lang_name in languages %}
            <a href="{% url 'set_language' %}?next={{ request.path }}&language={{ lang_code }}">
                {{ lang_name }}
            </a>
        {% endfor %}
    </div>
</article>
```

### Querying Translations

```python
# Get all posts with English translations
posts = Post.objects.translated('en')

# Get posts with any translation
posts = Post.objects.all()

# Filter by translated fields
posts = Post.objects.translated('en').filter(title__icontains='Django')

# Prefetch translations for performance
posts = Post.objects.prefetch_related('translations')
```

---

## URL Configuration

### Language-Prefixed URLs

```python
# project/urls.py
from django.conf.urls.i18n import i18n_patterns
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),  # Language switcher
]

# Add i18n patterns for translated URLs
urlpatterns += i18n_patterns(
    path('blog/', include('apps.blog.urls')),
    # Other translated URLs
    prefix_default_language=True,  # /en/blog/ and /tr/blog/
)
```

**Result:**
- English: `/en/blog/my-post/`
- Turkish: `/tr/blog/benim-yazim/`

---

## Testing Plan

### Unit Tests

```python
# apps/blog/tests/test_parler_integration.py
from django.test import TestCase
from apps.blog.models import Post

class ParlerIntegrationTest(TestCase):
    def test_create_post_with_translations(self):
        """Test creating post with multiple translations"""
        post = Post.objects.create(
            title='English Title',
            slug='english-title',
            content='English content',
            status='published',
        )
        post.set_current_language('tr')
        post.title = 'Türkçe Başlık'
        post.slug = 'turkce-baslik'
        post.content = 'Türkçe içerik'
        post.save()

        # Verify English version
        post.set_current_language('en')
        self.assertEqual(post.title, 'English Title')

        # Verify Turkish version
        post.set_current_language('tr')
        self.assertEqual(post.title, 'Türkçe Başlık')

    def test_fallback_language(self):
        """Test fallback to English if Turkish missing"""
        post = Post.objects.create(
            title='Only English',
            slug='only-english',
            content='Content',
        )

        # Switch to Turkish, should fallback to English
        post.set_current_language('tr')
        title = post.safe_translation_getter('title', any_language=True)
        self.assertEqual(title, 'Only English')
```

### Manual Testing Checklist

- [ ] Create new post in Turkish
- [ ] Add English translation
- [ ] Verify both versions display correctly
- [ ] Test language switcher
- [ ] Test slug uniqueness per language
- [ ] Test admin language tabs
- [ ] Test search across languages
- [ ] Test ordering/filtering

---

## Performance Considerations

### Database Queries

**Problem:** N+1 queries when accessing translations

**Solution:** Use `prefetch_related`

```python
# ❌ Bad: N+1 queries
posts = Post.objects.all()
for post in posts:
    print(post.title)  # Separate query for each post

# ✅ Good: Single query with prefetch
posts = Post.objects.prefetch_related('translations')
for post in posts:
    print(post.title)
```

### Caching Strategy

```python
from django.core.cache import cache

def get_cached_post(slug, language='tr'):
    cache_key = f'post_{slug}_{language}'
    post = cache.get(cache_key)

    if post is None:
        post = Post.objects.translated(language).get(slug=slug)
        cache.set(cache_key, post, 3600)  # 1 hour

    return post
```

---

## Success Criteria

| Criterion | Target | Status |
|-----------|--------|--------|
| Blog posts editable in both languages | ✅ Yes | ⏳ Pending |
| Admin interface user-friendly | ✅ 5-star rating | ⏳ Pending |
| No data loss during migration | ✅ 100% | ⏳ Pending |
| Performance acceptable | ✅ < 100ms per query | ⏳ Pending |
| URL structure clean | ✅ /en/, /tr/ prefixes | ⏳ Pending |

---

## Timeline

| Week | Phase | Tasks |
|------|-------|-------|
| **Week 1** | Setup | Install django-parler, configure settings, create migrations |
| **Week 1** | Migration | Migrate existing data, test data integrity |
| **Week 1** | Admin | Configure TranslatableAdmin, test admin interface |
| **Week 2** | Frontend | Update views and templates for translations |
| **Week 2** | Testing | Write tests, perform manual testing |
| **Week 2** | Documentation | Document usage, create team guide |

---

## Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Data loss during migration | High | Low | Full database backup before starting |
| Performance degradation | Medium | Medium | Implement caching, optimize queries |
| Admin UI complexity | Low | Medium | Training session for content team |
| URL conflicts | Medium | Low | Careful slug validation per language |

---

## Rollback Plan

If PoC fails:

1. **Keep Original Data:** Backup database before migrations
2. **Reverse Migrations:** Run rollback migrations
3. **Restore Models:** Revert to original model definitions
4. **Clear Cache:** Flush all cached translations
5. **Verify:** Run tests to ensure original functionality

---

## Next Steps After PoC

If PoC successful:

1. ✅ **Expand to Other Models:** Apply to portfolio projects, tools, etc.
2. ✅ **Enhance Admin:** Add translation progress indicators
3. ✅ **Build Translation Workflow:** Create process for translators
4. ✅ **Implement Sitemap:** Per-language sitemaps for SEO
5. ✅ **Add Analytics:** Track language usage

---

## Resources

- **django-parler Documentation:** https://django-parler.readthedocs.io/
- **GitHub Repository:** https://github.com/django-parler/django-parler
- **Tutorial:** https://www.caktusgroup.com/blog/2014/09/15/django-parler/
- **Example Project:** https://github.com/django-parler/django-parler/tree/master/example

---

**Status:** Ready to Start PoC
**Prepared by:** Development Team
**Approval Required:** ✅ Proceed with Week 1 implementation
