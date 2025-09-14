from django.urls import path, include
from . import views

app_name = 'main'

urlpatterns = [
    # Main pages
    path('personal/', views.personal_view, name='personal'),
    path('music/', views.music_view, name='music'),
    path('ai/', views.ai_tools_view, name='ai'),
    path('cybersecurity/', views.cybersecurity_view, name='cybersecurity'),
    path('useful/', views.useful_view, name='useful'),
    
    # Project pages
    path('projects/', views.projects_view, name='projects'),
    path('projects/<slug:slug>/', views.project_detail_view, name='project_detail'),
    
    # Search functionality
    # path('search/', views.search_view, name='search'),  # Temporarily disabled - missing view
    path('search/tags/', views.tag_search_view, name='tag_search'),
    path('search/tag/<str:tag_name>/', views.tag_results_view, name='tag_results'),
    
    # Short URL service
    path('s/<str:short_code>/', views.short_url_redirect, name='short_url_redirect'),
    
    # Internationalization URLs
    path('set-language/', views.set_language, name='set_language'),
    path('language-status/', views.language_status, name='language_status'),
    
    # ==========================================================================
    # API ENDPOINTS
    # ==========================================================================
    
    # Performance monitoring API
    path('api/performance/', views.collect_performance_metric, name='api_performance_collect'),
    path('api/performance/summary/', views.performance_summary, name='api_performance_summary'),
    path('api/performance/dashboard/', views.performance_dashboard_data, name='api_performance_dashboard'),
    
    # Web Push notifications API
    path('api/webpush/subscribe/', views.subscribe_push_notifications, name='api_webpush_subscribe'),
    path('api/webpush/unsubscribe/', views.webpush_unsubscribe, name='api_webpush_unsubscribe'),
    path('api/webpush/send/', views.send_push_notification, name='api_webpush_send'),
    path('api/webpush/test/', views.test_push_notification, name='api_webpush_test'),
    path('api/webpush/vapid-public-key/', views.get_vapid_public_key, name='api_webpush_vapid_key'),
    path('api/webpush/log/', views.webpush_log, name='api_webpush_log'),
    
    # Error logging API
    path('api/errors/', views.log_error, name='api_error_log'),
    path('api/errors/summary/', views.error_summary, name='api_error_summary'),
    
    # Content API (for reading public content)
    path('api/personal-info/', views.PersonalInfoListAPIView.as_view(), name='api_personal_info'),
    path('api/social-links/', views.SocialLinkListAPIView.as_view(), name='api_social_links'),
    path('api/ai-tools/', views.AIToolListAPIView.as_view(), name='api_ai_tools'),
    path('api/cybersecurity/', views.CybersecurityResourceListAPIView.as_view(), name='api_cybersecurity'),
    path('api/useful-resources/', views.UsefulResourceListAPIView.as_view(), name='api_useful_resources'),
    
    # Health and monitoring
    # path('api/health/', views.health_check, name='api_health'),  # Temporarily disabled - missing view
    
    # Monitoring dashboard (HTML view)
    path('dashboard/', views.monitoring_dashboard, name='monitoring_dashboard'),
    path('dashboard/performance/', views.performance_analytics_view, name='performance_analytics'),
    path('dashboard/errors/', views.error_logs_view, name='error_logs'),
    path('dashboard/notifications/', views.notification_logs_view, name='notification_logs'),
]