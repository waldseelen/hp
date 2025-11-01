"""
Template tags for Schema.org structured data
"""

from django import template
from django.utils.safestring import mark_safe

from apps.main.schema import StructuredData, render_structured_data

register = template.Library()


@register.simple_tag(takes_context=True)
def website_schema(context):
    """Render website schema markup"""
    request = context.get("request")
    if not request:
        return ""
    schema = StructuredData.website_schema(request)
    return mark_safe(render_structured_data(schema))


@register.simple_tag
def person_schema(request):
    """Render person schema markup"""
    schema = StructuredData.person_schema(request)
    return mark_safe(render_structured_data(schema))


@register.simple_tag
def blog_post_schema(request, post):
    """Render blog post schema markup"""
    schema = StructuredData.blog_post_schema(request, post)
    return mark_safe(render_structured_data(schema))


@register.simple_tag
def project_schema(request, project):
    """Render project schema markup"""
    schema = StructuredData.project_schema(request, project)
    return mark_safe(render_structured_data(schema))


@register.simple_tag
def breadcrumb_schema(request, items):
    """Render breadcrumb schema markup"""
    schema = StructuredData.breadcrumb_schema(request, items)
    return mark_safe(render_structured_data(schema))


@register.simple_tag
def organization_schema(request):
    """Render organization schema markup"""
    schema = StructuredData.organization_schema(request)
    return mark_safe(render_structured_data(schema))


@register.simple_tag
def faq_schema(faqs):
    """Render FAQ schema markup"""
    schema = StructuredData.faq_schema(faqs)
    return mark_safe(render_structured_data(schema))
