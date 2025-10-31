# Search Models Index - Comprehensive Indexing Plan

**Created:** 2025-10-31
**Purpose:** Define all models and fields for MeiliSearch full-text indexing
**Status:** Complete Model Inventory

---

## Overview

This document specifies which Django models will be indexed for site-wide search and which fields from each model will be searchable. All content is sanitized before indexing to prevent XSS attacks.

**Indexing Strategy:**
- Real-time indexing via Django signals (post_save/post_delete)
- Sanitized content (HTML/Markdown → plain text)
- Metadata enrichment (tags, categories, visibility flags)
- Public URL generation for search results

---

## Indexed Models

### 1. BlogPost (`apps.main.models.BlogPost`)

**Primary Fields:**
| Field | Type | Indexed | Searchable Weight | Notes |
|-------|------|---------|-------------------|-------|
| `id` | Integer | ✅ | - | Primary key |
| `title` | CharField(200) | ✅ | HIGH (10) | Main search field |
| `slug` | SlugField(200) | ✅ | LOW (2) | URL identifier |
| `excerpt` | TextField(300) | ✅ | MEDIUM (7) | Summary text |
| `content` | TextField | ✅ | MEDIUM (5) | Full content (sanitized) |
| `tags` | CharField(200) | ✅ | HIGH (8) | Comma-separated tags |
| `meta_description` | CharField(160) | ✅ | LOW (3) | SEO description |

**Metadata Fields:**
| Field | Type | Indexed | Purpose |
|-------|------|---------|---------|
| `status` | CharField | ✅ | Filter by published/draft |
| `is_featured` | Boolean | ✅ | Boost featured posts |
| `category.name` | ForeignKey | ✅ | Category facet |
| `category.display_name` | ForeignKey | ✅ | Display category |
| `author.name` | ForeignKey | ✅ | Author info |
| `published_at` | DateTime | ✅ | Sort by date |
| `updated_at` | DateTime | ✅ | Freshness boost |
| `view_count` | Integer | ✅ | Popularity boost |
| `reading_time` | Integer | ✅ | Display metadata |
| `is_visible` | Computed | ✅ | `status == 'published'` |

**Searchable URL:**
- URL Pattern: `/blog/{slug}/`
- Reverse: `blog:detail` with `slug`

**Sanitization:**
- `content`: HTML → plain text via `ContentSanitizer.sanitize_html(strip_tags=True)`
- `excerpt`: HTML → plain text
- `title`, `meta_description`: Keep as-is (no HTML allowed)

---

### 2. AITool (`apps.main.models.AITool`)

**Primary Fields:**
| Field | Type | Indexed | Searchable Weight | Notes |
|-------|------|---------|-------------------|-------|
| `id` | Integer | ✅ | - | Primary key |
| `name` | CharField(100) | ✅ | HIGH (10) | Tool name |
| `description` | TextField | ✅ | HIGH (8) | Full description |
| `url` | URLField | ✅ | LOW (1) | External URL |
| `tags` | CharField(200) | ✅ | HIGH (7) | Comma-separated |

**Metadata Fields:**
| Field | Type | Indexed | Purpose |
|-------|------|---------|---------|
| `category` | CharField | ✅ | Category facet (general, visual, code, etc.) |
| `is_featured` | Boolean | ✅ | Boost featured tools |
| `is_free` | Boolean | ✅ | Filter free/paid |
| `rating` | Float | ✅ | Popularity/quality score |
| `is_visible` | Boolean | ✅ | Visibility filter |
| `order` | Integer | ✅ | Manual ordering |
| `created_at` | DateTime | ✅ | Freshness |
| `updated_at` | DateTime | ✅ | Recent updates |

**Searchable URL:**
- URL Pattern: `/ai-tools/` (anchor: `#tool-{id}`)
- Reverse: `main:ai` + `#{id}`

**Sanitization:**
- `description`: Plain text (no HTML expected)
- `name`: Plain text

---

### 3. UsefulResource (`apps.main.models.UsefulResource`)

**Primary Fields:**
| Field | Type | Indexed | Searchable Weight | Notes |
|-------|------|---------|-------------------|-------|
| `id` | Integer | ✅ | - | Primary key |
| `name` | CharField(100) | ✅ | HIGH (10) | Resource name |
| `description` | TextField | ✅ | HIGH (8) | Full description |
| `url` | URLField | ✅ | LOW (1) | External URL |
| `tags` | CharField(200) | ✅ | HIGH (7) | Comma-separated |

**Metadata Fields:**
| Field | Type | Indexed | Purpose |
|-------|------|---------|---------|
| `type` | CharField | ✅ | Type facet (website, app, tool, extension) |
| `category` | CharField | ✅ | Category facet (development, design, ai, etc.) |
| `is_featured` | Boolean | ✅ | Boost featured |
| `is_free` | Boolean | ✅ | Filter free/paid |
| `rating` | Float | ✅ | Quality score |
| `is_visible` | Boolean | ✅ | Visibility filter |
| `order` | Integer | ✅ | Manual ordering |
| `created_at` | DateTime | ✅ | Freshness |
| `updated_at` | DateTime | ✅ | Recent updates |

**Searchable URL:**
- URL Pattern: `/useful/` (anchor: `#resource-{id}`)
- Reverse: `main:useful` + `#{id}`

**Sanitization:**
- `description`: Plain text
- `name`: Plain text

---

### 4. CybersecurityResource (`apps.main.models.CybersecurityResource`)

**Primary Fields:**
| Field | Type | Indexed | Searchable Weight | Notes |
|-------|------|---------|-------------------|-------|
| `id` | Integer | ✅ | - | Primary key |
| `title` | CharField(150) | ✅ | HIGH (10) | Resource title |
| `description` | TextField | ✅ | HIGH (8) | Short description |
| `content` | TextField | ✅ | MEDIUM (6) | Full content (Markdown) |
| `tags` | CharField(200) | ✅ | HIGH (7) | Comma-separated |

**Metadata Fields:**
| Field | Type | Indexed | Purpose |
|-------|------|---------|---------|
| `type` | CharField | ✅ | Type facet (tool, threat, standard, practice, etc.) |
| `difficulty` | CharField | ✅ | Difficulty filter (beginner, intermediate, advanced, expert) |
| `severity_level` | Integer | ✅ | Urgency sorting (1=Low, 4=Critical) |
| `is_urgent` | Boolean | ✅ | Urgent threats boost |
| `is_featured` | Boolean | ✅ | Featured content |
| `is_visible` | Boolean | ✅ | Visibility filter |
| `order` | Integer | ✅ | Manual ordering |
| `url` | URLField | ✅ | External resource |
| `created_at` | DateTime | ✅ | Freshness |
| `updated_at` | DateTime | ✅ | Recent updates |

**Searchable URL:**
- URL Pattern: `/cybersecurity/` (anchor: `#resource-{id}`)
- Reverse: `main:cybersecurity` + `#{id}`

**Sanitization:**
- `content`: Markdown → plain text via `ContentSanitizer.sanitize_markdown()` then strip HTML
- `description`: Plain text
- `title`: Plain text

---

### 5. Tool (`apps.tools.models.Tool`)

**Primary Fields:**
| Field | Type | Indexed | Searchable Weight | Notes |
|-------|------|---------|-------------------|-------|
| `id` | Integer | ✅ | - | Primary key |
| `title` | CharField(200) | ✅ | HIGH (10) | Tool title |
| `description` | TextField | ✅ | HIGH (8) | Tool description |
| `tags` | CharField/JSONField | ✅ | HIGH (7) | Tool tags |

**Metadata Fields:**
| Field | Type | Indexed | Purpose |
|-------|------|---------|---------|
| `is_visible` | Boolean | ✅ | Visibility filter |
| `created_at` | DateTime | ✅ | Freshness |
| `updated_at` | DateTime | ✅ | Recent updates |

**Searchable URL:**
- URL Pattern: `/tools/` or `/tools/{slug}/`
- Reverse: `tools:tool_list` (needs verification)

**Sanitization:**
- `description`: Plain text
- `title`: Plain text

**Note:** Tool model structure needs verification - may have additional fields like `slug`, `category`, `is_featured`

---

### 6. PersonalInfo (`apps.main.models.PersonalInfo`)

**Primary Fields:**
| Field | Type | Indexed | Searchable Weight | Notes |
|-------|------|---------|-------------------|-------|
| `id` | Integer | ✅ | - | Primary key |
| `key` | CharField(100) | ✅ | HIGH (9) | Info identifier (e.g., "bio", "skills") |
| `value` | TextField | ✅ | MEDIUM (6) | Content value |

**Metadata Fields:**
| Field | Type | Indexed | Purpose |
|-------|------|---------|---------|
| `type` | CharField | ✅ | Content type (text, json, markdown, html) |
| `is_visible` | Boolean | ✅ | Visibility filter |
| `order` | Integer | ✅ | Display order |
| `created_at` | DateTime | ✅ | Freshness |
| `updated_at` | DateTime | ✅ | Recent updates |

**Searchable URL:**
- URL Pattern: `/personal/` (anchor: `#info-{key}`)
- Reverse: `main:personal` + `#{key}`

**Sanitization:**
- `value`: Type-specific sanitization:
  - `html`: `ContentSanitizer.sanitize_html(strip_tags=True)`
  - `markdown`: `ContentSanitizer.sanitize_markdown()` then strip HTML
  - `json`: Extract text values, concatenate
  - `text`: Keep as-is
- `key`: Plain text

**Indexing Rule:** Only index if `is_visible=True`

---

### 7. SocialLink (`apps.main.models.SocialLink`)

**Primary Fields:**
| Field | Type | Indexed | Searchable Weight | Notes |
|-------|------|---------|-------------------|-------|
| `id` | Integer | ✅ | - | Primary key |
| `platform` | CharField(50) | ✅ | HIGH (8) | Platform name (GitHub, LinkedIn, etc.) |
| `description` | TextField | ✅ | MEDIUM (5) | Link description |

**Metadata Fields:**
| Field | Type | Indexed | Purpose |
|-------|------|---------|---------|
| `url` | CharField(255) | ✅ | External link |
| `is_primary` | Boolean | ✅ | Primary link boost |
| `is_visible` | Boolean | ✅ | Visibility filter |
| `order` | Integer | ✅ | Display order |
| `created_at` | DateTime | ✅ | Freshness |
| `updated_at` | DateTime | ✅ | Recent updates |

**Searchable URL:**
- URL Pattern: External URL (direct link to social profile)
- Use `url` field directly

**Sanitization:**
- `description`: Plain text (if exists)
- `platform`: Plain text
- `url`: Validate protocol (http, https, mailto only)

**Indexing Rule:** Only index if `is_visible=True`

---

## Index Schema Design

### Primary Index: `portfolio_search`

**Searchable Attributes (in order of priority):**
1. `title` / `name` (weight: 10)
2. `excerpt` / `description` (weight: 8)
3. `tags` (weight: 7)
4. `content` / `value` (weight: 5)
5. `meta_description` (weight: 3)

**Filterable Attributes:**
- `model_type` (BlogPost, AITool, Tool, etc.)
- `category`
- `type`
- `is_visible`
- `is_featured`
- `is_free`
- `difficulty`
- `severity_level`
- `status`
- `published_at` (range filter)
- `updated_at` (range filter)

**Sortable Attributes:**
- `published_at` (descending)
- `updated_at` (descending)
- `view_count` (descending)
- `rating` (descending)
- `relevance` (default)

**Displayed Attributes:**
- `id`
- `model_type`
- `title` / `name`
- `excerpt` / `description` (truncated to 200 chars)
- `url`
- `category`
- `tags` (first 5 tags)
- `metadata` (JSON object with dates, author, etc.)

---

## Document Structure Example

```json
{
  "id": "BlogPost:42",
  "model_type": "BlogPost",
  "model_id": 42,
  "title": "Understanding Django Signals",
  "content": "Django signals allow decoupled applications to get notified when certain actions occur...",
  "excerpt": "Learn how Django signals enable event-driven architecture in your applications.",
  "tags": ["django", "python", "signals", "architecture"],
  "category": "technology",
  "category_display": "Teknoloji",
  "author": "John Doe",
  "url": "/blog/understanding-django-signals/",
  "is_visible": true,
  "is_featured": true,
  "status": "published",
  "published_at": 1698710400,
  "updated_at": 1698796800,
  "view_count": 1250,
  "reading_time": 5,
  "meta_description": "A comprehensive guide to Django signals and event-driven patterns.",
  "search_category": "Blog Posts",
  "search_icon": "📝"
}
```

---

## Sanitization Rules

### XSS Prevention
1. **HTML Content:** Strip all tags, preserve only text content
2. **Markdown Content:** Convert to HTML, then strip tags
3. **URLs:** Validate protocol whitelist (http, https, mailto, ftp)
4. **Special Characters:** Escape or remove script-like patterns
5. **JSON Content:** Extract text values only, skip nested structures

### Content Extraction
- **Maximum Content Length:** 10,000 characters per field
- **Tag Parsing:** Split by comma, trim whitespace, limit to 20 tags
- **Text Truncation:** Excerpt limited to 200 chars in results

### Sanitizer Integration
```python
from apps.main.sanitizer import ContentSanitizer

# HTML sanitization
clean_text = ContentSanitizer.sanitize_html(raw_html, strip_tags=True)

# Markdown sanitization
html_content = ContentSanitizer.sanitize_markdown(markdown_text)
clean_text = ContentSanitizer.sanitize_html(html_content, strip_tags=True)

# URL validation
valid_url = ContentSanitizer.validate_url(url, allowed_protocols=['http', 'https'])
```

---

## Indexing Triggers

### Automatic (Signal-based)
- **post_save:** Index/update document immediately after model save
- **post_delete:** Remove document from index immediately after model delete

### Manual (Admin-triggered)
- **Reindex All:** Management command `python manage.py reindex_search --all`
- **Reindex Model:** Management command `python manage.py reindex_search --model=BlogPost`
- **Admin Action:** Bulk reindex selected items from admin list view

### Scheduled (Optional)
- **Daily Sync:** Verify index consistency (cron job)
- **Weekly Full Reindex:** Complete rebuild to prevent drift

---

## Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Index Latency (post_save) | < 5 seconds | Time from model save to searchable |
| Search Response Time | < 100ms | 95th percentile query time |
| Bulk Indexing Speed | > 100 docs/sec | Initial index population |
| Index Size per Document | < 10KB | Average document size |
| Total Index Size (1000 docs) | < 10MB | Compressed index size |

---

## Security Considerations

1. **Visibility Filter:** Only index `is_visible=True` content for public search
2. **Draft Content:** BlogPost with `status='draft'` should NOT be indexed
3. **Sensitive Fields:** Never index passwords, API keys, admin emails
4. **URL Validation:** Sanitize external URLs to prevent malicious redirects
5. **Rate Limiting:** Implement search API rate limiting (100 req/min per IP)

---

## Next Steps

1. ✅ Model inventory completed
2. ⏳ Create `apps/main/search_index.py` with `SearchIndexManager`
3. ⏳ Integrate MeiliSearch client and configuration
4. ⏳ Implement signal handlers for automatic indexing
5. ⏳ Create management command for manual reindexing
6. ⏳ Build search API endpoint (`/api/search/`)
7. ⏳ Create frontend search interface
8. ⏳ Write comprehensive test suite

---

**Status:** Document Complete ✅
**Next Action:** Create MeiliSearch Docker configuration (Task 2)
