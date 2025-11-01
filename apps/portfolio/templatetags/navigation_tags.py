from django import template
from django.urls import resolve

register = template.Library()


@register.simple_tag(takes_context=True)
def nav_active(context, url_name, css_class="active"):  # noqa: C901
    """
    Template tag to determine if the current page matches the given URL name.
    Returns the CSS class if there's a match, empty string otherwise.

    Usage: {% nav_active 'home' %} or {% nav_active 'home' 'custom-active-class' %}
    """
    request = context["request"]
    try:
        current_url_name = resolve(request.path_info).url_name
        # Also check if the URL namespace matches for app-specific URLs
        resolve(request.path_info).namespace

        # Handle different URL patterns
        if current_url_name == url_name:
            return css_class

        # Check if we're on a sub-page of the same section
        if url_name == "home" and request.path == "/":
            return css_class
        elif url_name == "blog" and "blog" in request.path:
            return css_class
        elif url_name == "tools" and (
            "tools" in request.path or "projects" in request.path
        ):
            return css_class
        elif url_name == "contact" and "contact" in request.path:
            return css_class
        elif url_name == "chat" and "chat" in request.path:
            return css_class
        elif url_name == "personal" and "personal" in request.path:
            return css_class
        elif url_name == "music" and "music" in request.path:
            return css_class

    except Exception:
        # If there's any error resolving the URL, return empty string
        pass

    return ""


@register.simple_tag(takes_context=True)
def is_current_page(context, url_name):
    """
    Simple boolean check if the current page matches the URL name.
    Returns True/False.

    Usage: {% is_current_page 'home' %}
    """
    request = context["request"]
    try:
        current_url_name = resolve(request.path_info).url_name
        return current_url_name == url_name
    except Exception:
        return False


@register.inclusion_tag("partials/breadcrumb.html", takes_context=True)
def render_breadcrumb(context):
    """
    Renders breadcrumb navigation using the breadcrumbs from context processor.

    Usage: {% render_breadcrumb %}
    """
    # Get breadcrumbs from context processor
    breadcrumbs = context.get("breadcrumbs", [{"title": "Ana Sayfa", "url": "/"}])
    return {"breadcrumbs": breadcrumbs}


@register.simple_tag(takes_context=True)
def get_breadcrumbs(context):
    """
    Returns breadcrumbs list for use in templates.

    Usage: {% get_breadcrumbs as breadcrumbs %}
    """
    return context.get("breadcrumbs", [{"title": "Ana Sayfa", "url": "/"}])


@register.simple_tag(takes_context=True)
def is_active_nav(context, url_name):
    """
    Checks if a navigation item should be marked as active.
    Returns True if the current page matches the URL name.

    Usage: {% is_active_nav 'home' %}
    """
    request = context["request"]
    try:
        resolved_match = resolve(request.path)
        current_url_name = resolved_match.url_name
        namespace = resolved_match.namespace

        # Handle different URL patterns
        if current_url_name == url_name:
            return True

        # Check namespace matches
        full_url_name = f"{namespace}:{url_name}" if namespace else url_name
        if (
            full_url_name == f"{namespace}:{current_url_name}"
            if namespace
            else current_url_name
        ):
            return True

        # Check section matches
        if namespace and url_name in namespace:
            return True

        return False

    except Exception:
        return False


@register.inclusion_tag("navigation/breadcrumb.html", takes_context=True)
def breadcrumb(context):
    """
    Generates breadcrumb navigation based on current URL.

    Usage: {% breadcrumb %}
    """
    request = context["request"]
    path_parts = [part for part in request.path.split("/") if part]

    breadcrumbs = [{"name": "Ana Sayfa", "url": "/"}]

    # Map URL parts to readable names
    url_mapping = {
        "blog": "Blog",
        "tools": "Projeler",
        "contact": "İletişim",
        "chat": "Sohbet",
        "personal": "Hakkımda",
        "music": "Müzik",
        "admin": "Admin",
        "ai": "AI Araçları",
        "cybersecurity": "Siber Güvenlik",
        "useful": "Useful",
    }

    current_path = ""
    for part in path_parts:
        current_path += f"/{part}"
        if part in url_mapping:
            breadcrumbs.append({"name": url_mapping[part], "url": current_path})
        elif part.isdigit():
            # Handle detail pages with IDs
            breadcrumbs.append({"name": f"#{part}", "url": current_path})

    return {"breadcrumbs": breadcrumbs}
