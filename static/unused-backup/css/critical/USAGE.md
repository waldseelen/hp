<!-- Critical CSS Usage in Django Templates -->

<!-- Base template (templates/base.html) -->
<style>
  {% include "static/css/critical/base.css" %}
</style>

<!-- Home page (templates/main/home.html) -->
{% block critical_css %}
<style>
  {% include "static/css/critical/home.css" %}
</style>
{% endblock %}

<!-- Blog page (templates/blog/list.html) -->
{% block critical_css %}
<style>
  {% include "static/css/critical/blog.css" %}
</style>
{% endblock %}

<!-- Contact page (templates/contact/form.html) -->
{% block critical_css %}
<style>
  {% include "static/css/critical/contact.css" %}
</style>
{% endblock %}

<!-- Load non-critical CSS asynchronously -->
<link rel="preload" href="{% static 'css/output.css' %}" as="style" onload="this.onload=null;this.rel='stylesheet'">
<noscript><link rel="stylesheet" href="{% static 'css/output.css' %}"></noscript>