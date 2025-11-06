from django.contrib import admin
from django.utils.html import format_html

from .models import Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "author",
        "status",
        "status_display",
        "view_count",
        "reading_time",
        "published_at",
        "created_at",
    )
    list_filter = ("status", "author", "created_at", "published_at")
    search_fields = ("title", "excerpt", "content", "meta_description")
    list_editable = ("status",)
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    prepopulated_fields = {"slug": ("title",)}

    fieldsets = (
        ("Ana Bilgiler", {"fields": ("title", "slug", "excerpt", "author")}),
        (
            "İçerik",
            {
                "fields": ("content",),
                "classes": ("wide",),
            },
        ),
        (
            "Görseller",
            {
                "fields": ("featured_image_url", "featured_image", "image_preview"),
                "classes": ("collapse",),
            },
        ),
        ("Yayınlama", {"fields": ("status", "published_at", "tags")}),
        (
            "SEO",
            {
                "fields": ("meta_description",),
                "classes": ("collapse",),
            },
        ),
        (
            "İstatistikler",
            {
                "fields": ("view_count", "reading_time_display"),
                "classes": ("collapse",),
            },
        ),
        (
            "Tarihler",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    readonly_fields = (
        "created_at",
        "updated_at",
        "view_count",
        "reading_time_display",
        "image_preview",
    )
    actions = [
        "make_published",
        "make_draft",
        "make_unlisted",
    ]

    def status_display(self, obj):
        colors = {
            "draft": "#6c757d",
            "published": "#28a745",
            "unlisted": "#fd7e14",
            "scheduled": "#007bff",
        }
        icons = {"draft": "📝", "published": "✅", "unlisted": "🔒", "scheduled": "⏰"}
        return format_html(
            '<span style="color: {};">{} {}</span>',
            colors.get(obj.status, "#6c757d"),
            icons.get(obj.status, ""),
            obj.get_status_display(),
        )

    status_display.short_description = "Status"

    def reading_time(self, obj):
        time = obj.get_reading_time()
        return f"{time} min" if time > 0 else "-"

    reading_time.short_description = "Reading Time"

    def reading_time_display(self, obj):
        return self.reading_time(obj)

    reading_time_display.short_description = "Reading Time"

    def image_preview(self, obj):
        if obj.featured_image:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 200px;" />',
                obj.featured_image.url,
            )
        elif obj.featured_image_url:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 200px;" />',
                obj.featured_image_url,
            )
        return "No image"

    image_preview.short_description = "Image Preview"

    def save_model(self, request, obj, form, change):
        if not change:
            obj.author = request.user
        super().save_model(request, obj, form, change)

    # Bulk actions for changing post status
    def make_published(self, request, queryset):
        updated = queryset.update(status="published")
        self.message_user(request, f"{updated} post(s) marked as published.")

    make_published.short_description = "Mark selected posts as published"

    def make_draft(self, request, queryset):
        updated = queryset.update(status="draft")
        self.message_user(request, f"{updated} post(s) marked as draft.")

    make_draft.short_description = "Mark selected posts as draft"

    def make_unlisted(self, request, queryset):
        updated = queryset.update(status="unlisted")
        self.message_user(request, f"{updated} post(s) marked as unlisted.")

    make_unlisted.short_description = "Mark selected posts as unlisted"

    class Media:
        css = {"all": ("admin/css/forms.css",)}
        js = ("admin/js/jquery.init.js",)
