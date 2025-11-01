from django.urls import path

from . import views

app_name = "main"

urlpatterns = [
    path("personal/", views.personal_view, name="personal"),
    path("music/", views.music_view, name="music"),
    path("ai/", views.ai_tools_view, name="ai"),
    path("cybersecurity/", views.cybersecurity_view, name="cybersecurity"),
    path("useful/", views.useful_view, name="useful"),
]
