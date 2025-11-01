from django import template
from django.apps import apps

register = template.Library()


@register.simple_tag
def model_count(app_label, model_name):
    """Return object count for app_label.ModelName.

    Usage: {% model_count 'blog' 'Post' %}
    """
    try:
        model = apps.get_model(app_label, model_name)
        return model.objects.all().count()
    except Exception:
        return 0
