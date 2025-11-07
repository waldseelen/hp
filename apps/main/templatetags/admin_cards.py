import json
from pathlib import Path

from django import template
from django.apps import apps
from django.conf import settings

register = template.Library()


@register.simple_tag
def unread_contact_count():
    try:
        Contact = apps.get_model("contact", "ContactMessage")
        return Contact.objects.filter(is_read=False).count()
    except Exception:
        return 0


@register.simple_tag
def last_blog_posts(limit=5):
    try:
        Post = apps.get_model("blog", "Post")
        return Post.objects.all().order_by("-created_at")[: int(limit)]
    except Exception:
        return []


@register.simple_tag
def top_viewed_posts(limit=5):
    try:
        Post = apps.get_model("blog", "Post")
        return Post.objects.all().order_by("-view_count")[: int(limit)]
    except Exception:
        return []


@register.simple_tag
def performance_summary():
    """Try to read latest entry from reports/performance_metrics.json and return a small dict."""
    try:
        base = Path(settings.BASE_DIR) if hasattr(settings, "BASE_DIR") else Path(".")
        metrics_file = base / "reports" / "performance_metrics.json"
        if not metrics_file.exists():
            return {}
        data = json.loads(metrics_file.read_text(encoding="utf-8"))
        if not data:
            return {}
        latest = data[-1]
        # pick a few keys to display
        return {
            "p50_ms": latest.get("response_time", {}).get("p50_ms", 0),
            "p95_ms": latest.get("response_time", {}).get("p95_ms", 0),
            "db_query_count": latest.get("database", {}).get("query_count", 0),
            "cache_status": {
                k: v.get("status") for k, v in latest.get("cache", {}).items()
            },
            "cpu_percent": latest.get("system", {}).get("cpu_percent"),
            "memory_percent": latest.get("system", {}).get("memory_percent"),
        }
    except Exception:
        return {}
