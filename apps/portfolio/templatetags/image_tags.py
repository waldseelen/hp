"""
Template tags for image optimization
"""

from django import template
from django.conf import settings
from django.utils.html import format_html
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def lazy_image(
    src,
    alt="",
    css_class="",
    width="",
    height="",
    placeholder="",
    webp_src="",
    fallback="",
):
    """
    Render an optimized lazy-loading image with progressive enhancement

    Args:
        src: Image source URL
        alt: Alt text for accessibility
        css_class: Additional CSS classes
        width: Image width
        height: Image height
        placeholder: Low quality placeholder image for progressive loading
        webp_src: WebP format alternative
        fallback: Fallback image for errors

    Returns:
        HTML string for optimized image
    """
    classes = ["lazy-load"]
    if css_class:
        classes.append(css_class)

    if placeholder:
        classes.append("progressive-load")

    # Build attributes
    attrs = {
        "class": " ".join(classes),
        "alt": alt,
        "loading": "lazy",
        "data-src": src,
    }

    if width:
        attrs["width"] = width
    if height:
        attrs["height"] = height
    if placeholder:
        attrs["src"] = placeholder
        attrs["data-placeholder"] = placeholder
    else:
        attrs["src"] = (
            'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1"%3E%3C/svg%3E'
        )

    if webp_src:
        attrs["data-webp"] = webp_src
    if fallback:
        attrs["data-fallback"] = fallback

    # Create img tag
    attr_string = " ".join([f'{k}="{v}"' for k, v in attrs.items()])

    return format_html("<img {}>", mark_safe(attr_string))


@register.simple_tag
def responsive_image(
    src, alt="", css_class="", sizes="100vw", srcset="", webp_srcset="", lazy=True
):
    """
    Render a responsive image with srcset and sizes

    Args:
        src: Base image source
        alt: Alt text
        css_class: CSS classes
        sizes: Sizes attribute for responsive images
        srcset: Source set for different resolutions
        webp_srcset: WebP source set
        lazy: Enable lazy loading

    Returns:
        HTML string for responsive image
    """
    classes = []
    if lazy:
        classes.append("lazy-load")
    if css_class:
        classes.append(css_class)

    attrs = {
        "alt": alt,
        "sizes": sizes,
    }

    if classes:
        attrs["class"] = " ".join(classes)

    if lazy:
        attrs["loading"] = "lazy"
        attrs["data-src"] = src
        attrs["src"] = (
            'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1"%3E%3C/svg%3E'
        )
        if srcset:
            attrs["data-srcset"] = srcset
        if webp_srcset:
            attrs["data-webp-srcset"] = webp_srcset
    else:
        attrs["src"] = src
        if srcset:
            attrs["srcset"] = srcset

    attr_string = " ".join([f'{k}="{v}"' for k, v in attrs.items()])

    return format_html("<img {}>", mark_safe(attr_string))


@register.simple_tag
def optimized_image(
    src, alt="", width="", height="", quality=85, format="auto", lazy=True, css_class=""
):
    """
    Generate an optimized image with automatic format selection and quality compression

    Args:
        src: Image source
        alt: Alt text
        width: Target width
        height: Target height
        quality: JPEG/WebP quality (1-100)
        format: Output format ('auto', 'webp', 'jpeg', 'png')
        lazy: Enable lazy loading
        css_class: Additional CSS classes

    Returns:
        HTML for optimized image
    """
    # This would integrate with image processing service in production
    # For now, return optimized lazy image

    classes = []
    if lazy:
        classes.append("lazy-load")
    if css_class:
        classes.append(css_class)

    # In production, you'd generate different sizes and formats
    # For example: src_webp = generate_webp_version(src, quality, width, height)

    attrs = {
        "alt": alt,
        "class": " ".join(classes) if classes else "",
    }

    if width:
        attrs["width"] = width
    if height:
        attrs["height"] = height

    if lazy:
        attrs["loading"] = "lazy"
        attrs["data-src"] = src
        attrs["src"] = (
            'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1"%3E%3C/svg%3E'
        )
    else:
        attrs["src"] = src

    attr_string = " ".join([f'{k}="{v}"' for k, v in attrs.items() if v])

    return format_html("<img {}>", mark_safe(attr_string))


@register.simple_tag
def cdn_url(path):
    """
    Generate CDN URL for static assets

    Args:
        path: Asset path

    Returns:
        Full CDN URL or regular static URL
    """
    if getattr(settings, "CDN_ENABLED", False) and getattr(settings, "CDN_DOMAIN", ""):
        return f"https://{settings.CDN_DOMAIN}{path}"
    else:
        return f"{settings.STATIC_URL.rstrip('/')}{path}"


@register.filter
def webp_support(image_url):
    """
    Check if WebP version exists and return appropriate URL

    Args:
        image_url: Original image URL

    Returns:
        WebP URL if exists, otherwise original URL
    """
    if not image_url:
        return image_url

    # Check if WebP version exists
    webp_url = image_url.rsplit(".", 1)[0] + ".webp"

    # In production, you'd check if the WebP file actually exists
    # For now, return the WebP URL with fallback handling in the template

    return webp_url


@register.inclusion_tag("components/picture_element.html")
def picture_tag(
    src, alt="", css_class="", width="", height="", webp_src="", avif_src="", lazy=True
):
    """
    Render a <picture> element with multiple format support

    Args:
        src: Fallback image source
        alt: Alt text
        css_class: CSS classes
        width: Image width
        height: Image height
        webp_src: WebP source
        avif_src: AVIF source (next-gen format)
        lazy: Enable lazy loading

    Returns:
        Dictionary for picture_element.html template
    """
    return {
        "src": src,
        "alt": alt,
        "css_class": css_class,
        "width": width,
        "height": height,
        "webp_src": webp_src,
        "avif_src": avif_src,
        "lazy": lazy,
    }


@register.simple_tag
def image_preload(src, as_type="image", media="", sizes=""):
    """
    Generate preload link for critical images

    Args:
        src: Image source
        as_type: Resource type (default: 'image')
        media: Media query for responsive preloading
        sizes: Sizes for responsive preloading

    Returns:
        Preload link HTML
    """
    attrs = {
        "rel": "preload",
        "as": as_type,
        "href": src,
    }

    if media:
        attrs["media"] = media
    if sizes:
        attrs["imagesizes"] = sizes

    attr_string = " ".join([f'{k}="{v}"' for k, v in attrs.items()])

    return format_html("<link {}>", mark_safe(attr_string))


@register.simple_tag(takes_context=True)
def critical_image(context, src, alt="", css_class="", width="", height=""):
    """
    Render a critical image that should load immediately (above the fold)

    Args:
        context: Template context
        src: Image source
        alt: Alt text
        css_class: CSS classes
        width: Image width
        height: Image height

    Returns:
        HTML for critical image with preload
    """
    # Add preload to head section
    preload_html = image_preload(src)

    # Store preload in context for head section
    if "preload_images" not in context:
        context["preload_images"] = []
    context["preload_images"].append(preload_html)

    # Return regular image tag (no lazy loading for critical images)
    attrs = {
        "src": src,
        "alt": alt,
    }

    if css_class:
        attrs["class"] = css_class
    if width:
        attrs["width"] = width
    if height:
        attrs["height"] = height

    attr_string = " ".join([f'{k}="{v}"' for k, v in attrs.items()])

    return format_html("<img {}>", mark_safe(attr_string))
