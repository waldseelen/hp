from django.contrib import admin
from django.utils.html import format_html

from .models import Tool


@admin.register(Tool)
class ToolAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "category",
        "rating_display",
        "pricing",
        "is_favorite",
        "is_visible",
        "created_at",
    )
    list_filter = ("category", "is_favorite", "is_visible", "rating", "created_at")
    search_fields = ("title", "description", "category", "tags")
    list_editable = ("is_favorite", "is_visible")
    ordering = ("category", "title")

    fieldsets = (
        ("Ana Bilgiler", {"fields": ("title", "description", "url", "category")}),
        (
            "Görseller",
            {
                "fields": ("icon_url", "image", "image_preview"),
                "classes": ("collapse",),
            },
        ),
        ("Değerlendirme & Etiketler", {"fields": ("rating", "pricing", "tags")}),
        ("Favoriler & Görünürlük", {"fields": ("is_favorite", "is_visible")}),
        (
            "Güncelleme Bilgisi",
            {
                "fields": ("last_updated",),
                "classes": ("collapse",),
            },
        ),
        (
            "Tarihler",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    readonly_fields = ("created_at", "updated_at", "image_preview")

    def rating_display(self, obj):
        if obj.rating:
            stars = "⭐" * obj.rating + "☆" * (5 - obj.rating)
            return format_html('<span title="{}/5">{}</span>', obj.rating, stars)
        return "-"

    rating_display.short_description = "Rating"

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 200px;" />',
                obj.image.url,
            )
        elif obj.icon_url:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 100px;" />',
                obj.icon_url,
            )
        return "No image"

    image_preview.short_description = "Image Preview"
