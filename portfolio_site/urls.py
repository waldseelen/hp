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
from django.shortcuts import redirect
from apps.main.views import home, logout_view
from apps.core.health import health_check_view, readiness_check_view, liveness_check_view

# Import API views from apps.main.views
from apps.main.views import (
    collect_performance_metric, performance_dashboard_data, health_check,
    subscribe_push_notifications, send_push_notification, log_error
)

urlpatterns = [
    # Health check endpoints (must be first for Docker/K8s)
    path('health/', health_check_view, name='health_check'),
    path('health/readiness/', readiness_check_view, name='readiness_check'),
    path('health/liveness/', liveness_check_view, name='liveness_check'),

    # API endpoints for performance monitoring and notifications
    path('api/performance/', collect_performance_metric, name='api_performance'),
    path('api/performance/dashboard/', performance_dashboard_data, name='api_performance_dashboard'),
    path('api/health/', health_check, name='api_health_check'),
    path('api/notifications/subscribe/', subscribe_push_notifications, name='api_notifications_subscribe'),
    path('api/notifications/send/', send_push_notification, name='api_notifications_send'),
    path('api/errors/log/', log_error, name='api_error_log'),

    # Admin and main application
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('logout/', logout_view, name='logout'),
    path('', include('apps.main.urls')),
    path('blog/', include('apps.blog.urls')),
    path('tools/', include('apps.tools.urls')),
    path('projects/', lambda request: redirect('tools:tool_list'), name='projects_redirect'),
    path('contact/', include('apps.contact.urls')),
    path('chat/', include('apps.chat.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
