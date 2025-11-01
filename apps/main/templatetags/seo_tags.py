"""
Template tags for SEO optimization
"""

from django import template

from apps.main.seo import SEOOptimizer

register = template.Library()


@register.simple_tag
def auto_meta_description(content, max_length=155):
    """Generate optimized meta description from content"""
    return SEOOptimizer.generate_meta_description(content, max_length)


@register.simple_tag
def auto_alt_text(filename, context=""):
    """Generate alt text for images"""
    return SEOOptimizer.generate_alt_text(filename, context)


@register.simple_tag
def optimize_title(title, site_name="Portfolio", max_length=60):
    """Optimize page title for SEO"""
    return SEOOptimizer.optimize_title(title, site_name, max_length)


@register.simple_tag
def extract_keywords(content, max_keywords=10):
    """Extract keywords from content"""
    keywords = SEOOptimizer.extract_keywords(content, max_keywords)
    return ", ".join(keywords)


@register.filter
def auto_slug(value, max_length=50):
    """Generate SEO-friendly slug"""
    return SEOOptimizer.generate_slug(str(value), max_length)
