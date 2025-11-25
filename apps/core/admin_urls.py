"""
Modern Admin Panel URLs
"""

from django.urls import path
from django.contrib.auth import views as auth_views

from .admin_views import (
    modern_admin_dashboard,
    modern_admin_login,
    blog_management,
    cybersecurity_management,
    tools_management,
)

app_name = 'modern_admin'

urlpatterns = [
    # Login
    path('login/', modern_admin_login, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/panel/login/'), name='logout'),

    # Dashboard (Ana Sayfa)
    path('', modern_admin_dashboard, name='dashboard'),

    # İçerik Yönetimi
    path('blog/', blog_management, name='blog'),
    path('cybersecurity/', cybersecurity_management, name='cybersecurity'),
    path('tools/', tools_management, name='tools'),
]
