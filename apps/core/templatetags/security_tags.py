"""
Security Template Tags
======================

Template tags for security features:
- CSP nonce injection
- SRI integrity attributes
- Security-aware static file loading

Usage:
    {% load security_tags %}
    {% csp_nonce as nonce %}
    <script nonce="{{ nonce }}">...</script>

    {% sri_script 'js/app.js' %}
    {% sri_style 'css/style.css' %}
"""

from django import template
from django.conf import settings
from django.templatetags.static import static
from django.utils.safestring import mark_safe

from apps.core.middleware.security_headers import (
    SubresourceIntegrityHelper,
    get_csp_nonce,
)

register = template.Library()

# Initialize SRI helper
_sri_helper = SubresourceIntegrityHelper()


@register.simple_tag(takes_context=True)
def csp_nonce(context):
    """
    Get CSP nonce from request context.

    Usage:
        {% csp_nonce as nonce %}
        <script nonce="{{ nonce }}">...</script>
    """
    request = context.get("request")
    if request:
        return get_csp_nonce(request) or ""
    return ""


@register.simple_tag
def sri_script(path, **attrs):
    """
    Generate script tag with SRI integrity attribute.

    Usage:
        {% sri_script 'js/app.js' %}
        {% sri_script 'js/app.js' async='async' %}

    Args:
        path: Path to JavaScript file (relative to STATIC_URL)
        **attrs: Additional HTML attributes

    Returns:
        HTML script tag with integrity attribute
    """
    try:
        # Get static URL
        url = static(path)

        # Generate integrity hash
        integrity = _sri_helper.generate_hash(path)

        # Build attributes
        attr_str = " ".join([f'{k}="{v}"' for k, v in attrs.items()])
        if attr_str:
            attr_str = " " + attr_str

        # Build script tag
        script_tag = (
            f'<script src="{url}" '
            f'integrity="{integrity}" '
            f'crossorigin="anonymous"{attr_str}></script>'
        )

        return mark_safe(
            script_tag
        )  # nosec B703, B308 - Intentional HTML generation for template tag

    except Exception:
        # Fallback to regular script tag in development
        if settings.DEBUG:
            url = static(path)
            attr_str = " ".join([f'{k}="{v}"' for k, v in attrs.items()])
            if attr_str:
                attr_str = " " + attr_str
            return mark_safe(
                f'<script src="{url}"{attr_str}></script>'
            )  # nosec B703, B308 - Intentional HTML generation for template tag
        raise


@register.simple_tag
def sri_style(path, **attrs):
    """
    Generate link tag with SRI integrity attribute for CSS.

    Usage:
        {% sri_style 'css/style.css' %}
        {% sri_style 'css/style.css' media='print' %}

    Args:
        path: Path to CSS file (relative to STATIC_URL)
        **attrs: Additional HTML attributes

    Returns:
        HTML link tag with integrity attribute
    """
    try:
        # Get static URL
        url = static(path)

        # Generate integrity hash
        integrity = _sri_helper.generate_hash(path)

        # Build attributes
        attr_str = " ".join([f'{k}="{v}"' for k, v in attrs.items()])
        if attr_str:
            attr_str = " " + attr_str

        # Build link tag
        link_tag = (
            f'<link rel="stylesheet" href="{url}" '
            f'integrity="{integrity}" '
            f'crossorigin="anonymous"{attr_str}>'
        )

        return mark_safe(
            link_tag
        )  # nosec B703, B308 - Intentional HTML generation for template tag

    except Exception:
        # Fallback to regular link tag in development
        if settings.DEBUG:
            url = static(path)
            attr_str = " ".join([f'{k}="{v}"' for k, v in attrs.items()])
            if attr_str:
                attr_str = " " + attr_str
            return mark_safe(
                f'<link rel="stylesheet" href="{url}"{attr_str}>'
            )  # nosec B703, B308 - Intentional HTML generation for template tag
        raise


@register.simple_tag
def sri_integrity(path):
    """
    Get SRI integrity attribute value for a file.

    Usage:
        <script src="{% static 'js/app.js' %}"
                integrity="{% sri_integrity 'js/app.js' %}"
                crossorigin="anonymous"></script>

    Args:
        path: Path to file (relative to STATIC_URL)

    Returns:
        Integrity attribute value (e.g., 'sha384-...')
    """
    try:
        return _sri_helper.generate_hash(path)
    except Exception:
        # Return empty string in development
        if settings.DEBUG:
            return ""
        raise


@register.simple_tag(takes_context=True)
def secure_script(context, content):
    """
    Generate inline script tag with CSP nonce.

    Usage:
        {% secure_script %}
            console.log('Hello, world!');
        {% endsecure_script %}

    Args:
        context: Template context
        content: JavaScript content

    Returns:
        HTML script tag with nonce
    """
    request = context.get("request")
    nonce = get_csp_nonce(request) if request else ""

    if nonce:
        return mark_safe(
            f'<script nonce="{nonce}">{content}</script>'
        )  # nosec B703, B308 - Intentional HTML generation for template tag
    else:
        # Fallback without nonce (not recommended in production)
        return mark_safe(
            f"<script>{content}</script>"
        )  # nosec B703, B308 - Intentional HTML generation for template tag


@register.simple_tag(takes_context=True)
def secure_style(context, content):
    """
    Generate inline style tag with CSP nonce.

    Usage:
        {% secure_style %}
            body { background: #fff; }
        {% endsecure_style %}

    Args:
        context: Template context
        content: CSS content

    Returns:
        HTML style tag with nonce
    """
    request = context.get("request")
    nonce = get_csp_nonce(request) if request else ""

    if nonce:
        return mark_safe(
            f'<style nonce="{nonce}">{content}</style>'
        )  # nosec B703, B308 - Intentional HTML generation for template tag
    else:
        # Fallback without nonce (not recommended in production)
        return mark_safe(
            f"<style>{content}</style>"
        )  # nosec B703, B308 - Intentional HTML generation for template tag
