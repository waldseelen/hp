"""
Custom template tags for advanced caching functionality.
"""

import hashlib

from django import template
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

from apps.main.cache_utils import cache_manager

register = template.Library()


@register.simple_tag(takes_context=True)
def cache_fragment(context, fragment_name, timeout=600, vary_on=None):
    """
    Cache a template fragment with optional variation.
    Usage: {% cache_fragment "fragment_name" 300 "user_id,page_num" %}
    """
    # Build cache key
    key_parts = [fragment_name]

    if vary_on:
        for var_name in vary_on.split(","):
            var_name = var_name.strip()
            if var_name in context:
                key_parts.append(f"{var_name}_{context[var_name]}")

    # Create hash for long keys
    cache_key = "_".join(key_parts)
    if len(cache_key) > 200:
        cache_key = f"fragment_{hashlib.md5(cache_key.encode(), usedforsecurity=False).hexdigest()}"
    else:
        cache_key = f"fragment_{cache_key}"

    # Try to get from cache
    cached_content = cache_manager.get(cache_key)
    if cached_content is not None:
        return mark_safe(cached_content)

    # Not in cache, will be populated by {% endcache_fragment %}
    context["_cache_fragment_key"] = cache_key
    context["_cache_fragment_timeout"] = timeout
    return ""


@register.simple_tag(takes_context=True)
def endcache_fragment(context):
    """End cache fragment block."""
    return ""


@register.inclusion_tag("components/cached_component.html", takes_context=True)
def cached_component(context, component_name, template_name, timeout=600, **kwargs):
    """
    Render and cache a component template.
    Usage: {% cached_component "header" "components/header.html" 300 user=user %}
    """
    # Build cache key from component name and context variables
    context_hash = hashlib.md5(
        str(sorted(kwargs.items())).encode(), usedforsecurity=False
    ).hexdigest()[:8]

    cache_key = f"component_{component_name}_{context_hash}"

    # Try cache first
    cached_html = cache_manager.get(cache_key)
    if cached_html is not None:
        return {"cached_html": mark_safe(cached_html)}

    # Render component
    component_context = context.flatten()
    component_context.update(kwargs)

    try:
        rendered_html = render_to_string(
            template_name, component_context, request=context.get("request")
        )
        cache_manager.set(cache_key, rendered_html, timeout)
        return {"cached_html": mark_safe(rendered_html)}
    except Exception as e:
        return {"cached_html": f"<!-- Component render error: {e} -->"}


@register.simple_tag(takes_context=True)
def cache_query(context, query_name, timeout=300):
    """
    Cache database query results.
    Usage: {% cache_query "recent_posts" 600 as cached_posts %}
    """
    cache_key = f"query_{query_name}"

    # Check for user-specific caching
    request = context.get("request")
    if request and hasattr(request, "user") and request.user.is_authenticated:
        cache_key += f"_user_{request.user.pk}"

    return cache_key


@register.filter
def cache_value(value, key_timeout):
    """
    Cache a template variable value.
    Usage: {{ expensive_calculation|cache_value:"calc_result,300" }}
    """
    if "," in key_timeout:
        cache_key, timeout = key_timeout.split(",", 1)
        timeout = int(timeout)
    else:
        cache_key = key_timeout
        timeout = 300

    cache_key = f"filter_{cache_key}"

    # Try cache
    cached_value = cache_manager.get(cache_key)
    if cached_value is not None:
        return cached_value

    # Cache the value
    cache_manager.set(cache_key, value, timeout)
    return value


@register.simple_tag
def invalidate_cache(pattern):
    """
    Invalidate cache entries matching pattern.
    Usage: {% invalidate_cache "blog_*" %}
    """
    count = cache_manager.delete_pattern(pattern)
    return f"Invalidated {count} cache entries"


@register.simple_tag
def cache_stats():
    """
    Get cache statistics.
    Usage: {% cache_stats as stats %}
    """
    return cache_manager.get_stats()


@register.inclusion_tag("components/cache_debug.html", takes_context=True)
def cache_debug_info(context):
    """
    Display cache debug information (only in DEBUG mode).
    Usage: {% cache_debug_info %}
    """
    from django.conf import settings

    if not settings.DEBUG:
        return {"debug": False}

    stats = cache_manager.get_stats()

    return {
        "debug": True,
        "stats": stats,
        "cache_backend": settings.CACHES["default"]["BACKEND"],
    }


class CacheFragmentNode(template.Node):
    """Node for cache fragment template tag."""

    def __init__(self, nodelist, fragment_name, timeout, vary_on):
        self.nodelist = nodelist
        self.fragment_name = template.Variable(fragment_name)
        self.timeout = template.Variable(timeout) if timeout else None
        self.vary_on = [template.Variable(var) for var in vary_on] if vary_on else []

    def render(self, context):
        # Get values
        fragment_name = self.fragment_name.resolve(context)
        timeout = self.timeout.resolve(context) if self.timeout else 600

        # Build cache key
        key_parts = [fragment_name]

        for var in self.vary_on:
            try:
                value = var.resolve(context)
                key_parts.append(str(value))
            except template.VariableDoesNotExist:
                key_parts.append("none")

        cache_key = f"template_fragment_{'_'.join(key_parts)}"

        # Try cache
        cached_content = cache_manager.get(cache_key)
        if cached_content is not None:
            return cached_content

        # Render and cache
        content = self.nodelist.render(context)
        cache_manager.set(cache_key, content, timeout)

        return content


@register.tag
def cache_block(parser, token):
    """
    Cache a block of template content.
    Usage:
    {% cache_block "block_name" 300 user.id request.path %}
        <!-- content to cache -->
    {% endcache_block %}
    """
    tokens = token.split_contents()

    if len(tokens) < 3:
        raise template.TemplateSyntaxError(
            f"'{tokens[0]}' tag requires at least fragment name and timeout"
        )

    fragment_name = tokens[1]
    timeout = tokens[2] if len(tokens) > 2 else None
    vary_on = tokens[3:] if len(tokens) > 3 else []

    nodelist = parser.parse(("endcache_block",))
    parser.delete_first_token()

    return CacheFragmentNode(nodelist, fragment_name, timeout, vary_on)


# Smart caching tags based on model changes
@register.simple_tag
def smart_cache_key(model_name, action="list", **filters):
    """
    Generate smart cache keys that include model version for auto-invalidation.
    Usage: {% smart_cache_key "Post" "list" status="published" as cache_key %}
    """
    # Include model's last modified time in cache key
    try:
        from django.apps import apps
        from django.utils import timezone

        model_class = apps.get_model(model_name)

        # Get latest update time for the model
        try:
            latest_update = model_class.objects.latest("updated_at").updated_at
            version = latest_update.timestamp()
        except (AttributeError, model_class.DoesNotExist):
            # Fallback to current time
            version = timezone.now().timestamp()

        # Build cache key
        filter_hash = hashlib.md5(
            str(sorted(filters.items())).encode(), usedforsecurity=False
        ).hexdigest()[:8]

        cache_key = f"smart_{model_name.lower()}_{action}_{version:.0f}_{filter_hash}"
        return cache_key

    except Exception:
        # Fallback to simple cache key
        filter_hash = hashlib.md5(
            str(sorted(filters.items())).encode(), usedforsecurity=False
        ).hexdigest()[:8]
        return f"fallback_{model_name.lower()}_{action}_{filter_hash}"


# Context processor for cache stats in templates
def cache_context_processor(request):
    """Add cache information to template context."""
    from django.conf import settings

    context = {
        "cache_enabled": "redis" in settings.CACHES["default"]["BACKEND"].lower(),
        "cache_debug": settings.DEBUG,
    }

    if settings.DEBUG:
        context["cache_stats"] = cache_manager.get_stats()

    return context
