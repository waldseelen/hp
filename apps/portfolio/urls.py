from django.urls import path
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
    path('search/', views.search_view, name='search'),
    path('search/tags/', views.tag_search_view, name='tag_search'),
    path('search/tag/<str:tag_name>/', views.tag_results_view, name='tag_results'),

    # Performance monitoring dashboard
    path('dashboard/', views.performance_dashboard_view, name='performance_dashboard'),

    # Design System UI Kit
    path('ui-kit/', views.ui_kit_view, name='ui_kit'),

    # PWA Offline page
    path('offline/', views.offline_view, name='offline'),
    
    # Short URL service
    path('s/<str:short_code>/', views.short_url_redirect, name='short_url_redirect'),
    
    # Internationalization URLs
    path('set-language/', views.set_language, name='set_language'),
    path('language-status/', views.language_status, name='language_status'),
    
    # Health and monitoring (moved to main urls.py)
    
    # Authentication
    path('logout/', views.logout_view, name='logout'),
    
    # PWA and JSON endpoints (using template views for simplicity)
    # path('manifest.json', views.manifest_json, name='manifest_json'),
    # path('analytics.json', views.analytics_json, name='analytics_json'),

    # Security endpoints
    path('api/security/csp-report/', views.csp_violation_report, name='csp_violation_report'),
    path('api/security/network-error-report/', views.network_error_report, name='network_error_report'),
]