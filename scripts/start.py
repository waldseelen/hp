import os
import sys

from django.conf import settings
from django.core.wsgi import get_wsgi_application
from django.http import HttpResponse
from django.urls import path

# Minimal Django setup
settings.configure(
    DEBUG=True,
    SECRET_KEY="dev-key-123",
    ROOT_URLCONF=__name__,
    ALLOWED_HOSTS=["*"],
)


def home(request):
    return HttpResponse(
        "<h1>🎉 Site Çalışıyor!</h1><p>Port: 8000</p><p>Django Portfolio Site</p>"
    )


urlpatterns = [
    path("", home),
]

if __name__ == "__main__":
    from django.core.management import execute_from_command_line

    execute_from_command_line(["manage.py", "runserver", "8000"])
