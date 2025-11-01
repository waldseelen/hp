from django.urls import path

from . import views

app_name = "main"

urlpatterns = [
    path("personal/", views.personal_view, name="personal"),
]
