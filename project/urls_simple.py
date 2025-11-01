from django.contrib import admin
from django.http import HttpResponse
from django.urls import path


def home(request):
    return HttpResponse(
        """
    <h1>Portfolio Site Çalışıyor!</h1>
    <p>Django başarıyla başlatıldı.</p>
    <p><a href="/admin/">Admin Panel</a></p>
    """
    )


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", home, name="home"),
]
