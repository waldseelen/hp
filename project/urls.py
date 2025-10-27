"""
URL configuration for portfolio_site project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.shortcuts import redirect
from django.views.generic import TemplateView
from django.views.static import serve
from django.http import FileResponse
import os
from apps.main.views import home, logout_view
from apps.core.health import health_check_view, readiness_check_view, liveness_check_view

# Import API views from apps.main.views
# from apps.main.views import (
#     collect_performance_metric, performance_dashboard_data, health_check,
#     subscribe_push_notifications, send_push_notification, log_error
# )
# from apps.main.views.logging_dashboard import (
#     logging_dashboard_view, log_data_api, log_alerts_api,
#     acknowledge_alert_api, log_export_view
# )
# from apps.main.views.search_api import (
#     SearchAutocompleteView, SearchAPIView, SearchFiltersView,
#     SearchAnalyticsView, popular_searches_api
# )

# Language-independent URLs (API, admin, health checks)
urlpatterns = [
    # Health check endpoints (must be first for Docker/K8s)
    path('health/', health_check_view, name='health_check'),
    path('health/readiness/', readiness_check_view, name='readiness_check'),
    path('health/liveness/', liveness_check_view, name='liveness_check'),

    # PWA and JSON endpoints
    path('manifest.json', TemplateView.as_view(template_name='manifest.json', content_type='application/manifest+json'), name='manifest'),
    path('analytics.json', TemplateView.as_view(template_name='analytics.json', content_type='application/json'), name='analytics'),

    # API endpoints for performance monitoring and notifications (commented out temporarily)
    # path('api/performance/', collect_performance_metric, name='api_performance'),
    # path('api/performance/dashboard/', performance_dashboard_data, name='api_performance_dashboard'),
    # path('api/health/', health_check, name='api_health_check'),
    # path('api/notifications/subscribe/', subscribe_push_notifications, name='api_notifications_subscribe'),
    # path('api/notifications/send/', send_push_notification, name='api_notifications_send'),
    # path('api/errors/log/', log_error, name='api_error_log'),

    # Search API endpoints (commented out temporarily)
    # path('api/search/autocomplete/', SearchAutocompleteView.as_view(), name='api_search_autocomplete'),
    # path('api/search/', SearchAPIView.as_view(), name='api_search'),
    # path('api/search/filters/', SearchFiltersView.as_view(), name='api_search_filters'),
    # path('api/search/analytics/', SearchAnalyticsView.as_view(), name='api_search_analytics'),
    # path('api/search/popular/', popular_searches_api, name='api_popular_searches'),

    # Log monitoring API endpoints (commented out temporarily)
    # path('api/logs/data/', log_data_api, name='api_log_data'),
    # path('api/logs/alerts/', log_alerts_api, name='api_log_alerts'),
    # path('api/logs/acknowledge/', acknowledge_alert_api, name='api_acknowledge_alert'),
    # path('api/logs/export/', log_export_view, name='api_log_export'),

    # Admin (language-independent)
    path('admin/', admin.site.urls),

    # TinyMCE Rich Text Editor
    path('tinymce/', include('tinymce.urls')),

    # Language selection URLs
    path('i18n/', include('django.conf.urls.i18n')),

    # SEO Files (robots.txt, sitemap.xml)
    path('robots.txt', lambda request: FileResponse(open(os.path.join(settings.BASE_DIR, 'static', 'robots.txt'), 'rb'), content_type='text/plain')),

    # Service Worker (must be served from root for proper scope)
    path('sw.js', lambda request: FileResponse(open(os.path.join(settings.BASE_DIR.parent, 'sw.js'), 'rb'), content_type='application/javascript')),
]

# Language-dependent URLs
urlpatterns += i18n_patterns(
    # Main application URLs
    path('', home, name='home'),
    path('logout/', logout_view, name='logout'),
    path('', include('apps.main.urls')),
    path('blog/', include('apps.blog.urls')),
    path('playground/', include('apps.playground.urls')),
    path('tools/', include('apps.tools.urls')),
    path('projects/', lambda request: redirect('tools:tool_list'), name='projects_redirect'),
    path('contact/', include('apps.contact.urls')),
    path('chat/', include('apps.chat.urls')),

    # Log monitoring dashboard (commented out temporarily)
    # path('logs/', logging_dashboard_view, name='logging_dashboard'),

    # GDPR Compliance URLs (commented out temporarily)
    # path('gdpr/', include(('apps.main.urls_gdpr', 'gdpr'))),

    prefix_default_language=False,
)

# Custom error handlers
handler404 = 'project.views.custom_404'
handler500 = 'project.views.custom_500'
# handler403 = 'apps.main.error_handlers.custom_403_handler'
# handler400 = 'apps.main.error_handlers.custom_400_handler'

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

