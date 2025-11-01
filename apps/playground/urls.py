from django.urls import path

from . import views

app_name = "playground"

urlpatterns = [
    # Main pages
    path("", views.index, name="index"),
    path("editor/", views.editor, name="editor"),
    path("editor/<int:language_id>/", views.editor, name="editor_language"),
    path("gallery/", views.gallery, name="gallery"),
    # API endpoints
    path("api/execute/", views.execute_code, name="execute_code"),
    path("api/save/", views.save_snippet, name="save_snippet"),
    path("api/template/<int:template_id>/", views.get_template, name="get_template"),
    # Snippet sharing
    path("snippet/<uuid:pk>/", views.snippet_detail, name="snippet_detail"),
    path("share/<uuid:pk>/", views.snippet_detail, name="share_snippet"),
]
