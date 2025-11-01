from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html

from .admin_utils import SanitizedContentAdminMixin
from .models import (
    Admin,
    AITool,
    BlogCategory,
    BlogPost,
    CybersecurityResource,
    MusicPlaylist,
    PersonalInfo,
    SocialLink,
    SpotifyCurrentTrack,
    UsefulResource,
)


@admin.register(Admin)
class AdminUserAdmin(UserAdmin):
    list_display = ("email", "name", "is_staff", "is_active", "created_at")
    list_filter = ("is_staff", "is_active", "created_at")
    search_fields = ("email", "name")
    ordering = ("-created_at",)


@admin.register(PersonalInfo)
class PersonalInfoAdmin(admin.ModelAdmin):
    list_display = ("key", "type", "is_visible", "order", "updated_at")
    list_filter = ("type", "is_visible")
    search_fields = ("key", "value")
    list_editable = ("is_visible", "order")
    ordering = ("order", "key")


@admin.register(SocialLink)
class SocialLinkAdmin(admin.ModelAdmin):
    list_display = ("platform", "url", "is_primary", "is_visible", "order")
    list_filter = ("platform", "is_primary", "is_visible")
    search_fields = ("platform", "url", "description")
    list_editable = ("is_primary", "is_visible", "order")
    ordering = ("order", "platform")


@admin.register(AITool)
class AIToolAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "is_featured",
        "is_free",
        "rating_display",
        "is_visible",
        "order",
    )
    list_filter = ("category", "is_featured", "is_free", "is_visible")
    search_fields = ("name", "description", "tags")
    list_editable = ("is_featured", "is_visible", "order")
    ordering = ("category", "order", "name")
    actions = ["reindex_selected_items"]

    fieldsets = (
        ("Temel Bilgiler", {"fields": ("name", "description", "url", "category")}),
        (
            "Görsel",
            {
                "fields": ("icon_url", "image", "image_preview"),
                "classes": ("collapse",),
            },
        ),
        ("Değerlendirme & Etiketler", {"fields": ("rating", "is_free", "tags")}),
        ("Görünürlük & Sıralama", {"fields": ("is_featured", "is_visible", "order")}),
        (
            "Tarihler",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    readonly_fields = ("created_at", "updated_at", "image_preview")

    def rating_display(self, obj):
        if obj.rating:
            stars = "⭐" * int(obj.rating)
            return format_html('<span title="{}/5">{}</span>', obj.rating, stars)
        return "-"

    rating_display.short_description = "Rating"

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 200px;" />',
                obj.image.url,
            )
        return "No image"

    image_preview.short_description = "Image Preview"


@admin.register(CybersecurityResource)
class CybersecurityResourceAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "type",
        "difficulty",
        "severity_display",
        "is_urgent",
        "is_featured",
        "is_visible",
    )
    list_filter = (
        "type",
        "difficulty",
        "severity_level",
        "is_urgent",
        "is_featured",
        "is_visible",
    )
    search_fields = ("title", "description", "content", "tags")
    list_editable = ("is_urgent", "is_featured", "is_visible")
    ordering = ("-is_urgent", "-severity_level", "type", "order", "title")

    fieldsets = (
        (
            "Temel Bilgiler",
            {"fields": ("title", "description", "type", "difficulty", "url")},
        ),
        (
            "İçerik",
            {
                "fields": ("content",),
                "classes": ("collapse",),
            },
        ),
        (
            "Görsel",
            {
                "fields": ("image", "image_preview"),
                "classes": ("collapse",),
            },
        ),
        ("Önem & Etiketler", {"fields": ("severity_level", "is_urgent", "tags")}),
        ("Görünürlük & Sıralama", {"fields": ("is_featured", "is_visible", "order")}),
        (
            "Tarihler",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    readonly_fields = ("created_at", "updated_at", "image_preview")

    def severity_display(self, obj):
        colors = {1: "#28a745", 2: "#ffc107", 3: "#fd7e14", 4: "#dc3545"}
        labels = {1: "Düşük", 2: "Orta", 3: "Yüksek", 4: "Kritik"}
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.severity_level, "#6c757d"),
            labels.get(obj.severity_level, "Bilinmiyor"),
        )

    severity_display.short_description = "Severity"

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 200px;" />',
                obj.image.url,
            )
        return "No image"

    image_preview.short_description = "Image Preview"


@admin.register(BlogCategory)
class BlogCategoryAdmin(admin.ModelAdmin):
    list_display = (
        "display_name",
        "name",
        "color_preview",
        "icon",
        "order",
        "is_visible",
    )
    list_filter = ("is_visible",)
    search_fields = ("display_name", "name", "description")
    list_editable = ("order", "is_visible")
    ordering = ("order", "display_name")

    fieldsets = (
        ("Temel Bilgiler", {"fields": ("name", "display_name", "description")}),
        ("Görünüm", {"fields": ("color", "color_preview", "icon")}),
        ("Sıralama & Görünürlük", {"fields": ("order", "is_visible")}),
        (
            "Tarihler",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    readonly_fields = ("created_at", "updated_at", "color_preview")

    def color_preview(self, obj):
        if obj.color:
            return format_html(
                '<div style="width: 30px; height: 20px; background-color: {}; border: 1px solid #ccc; display: inline-block;"></div> {}',
                obj.color,
                obj.color,
            )
        return "-"

    color_preview.short_description = "Color"


@admin.register(BlogPost)
class BlogPostAdmin(SanitizedContentAdminMixin):
    list_display = (
        "title",
        "category",
        "status",
        "author",
        "is_featured",
        "reading_time",
        "view_count",
        "published_at",
    )
    list_filter = ("status", "category", "is_featured", "author", "published_at")
    search_fields = ("title", "excerpt", "content", "tags")
    list_editable = ("status", "is_featured")
    ordering = ("-published_at", "-created_at")
    actions = ["reindex_selected_posts"]

    # Fields to sanitize on save
    sanitized_fields = ("content", "excerpt")
    sanitization_type = "html"

    fieldsets = (
        (
            "Temel Bilgiler",
            {"fields": ("title", "slug", "category", "author", "status")},
        ),
        (
            "İçerik",
            {"fields": ("excerpt", "content", "featured_image", "blog_image_preview")},
        ),
        (
            "SEO & Meta",
            {
                "fields": ("meta_description", "tags"),
                "classes": ("collapse",),
            },
        ),
        (
            "İstatistik & Ayarlar",
            {"fields": ("is_featured", "reading_time", "view_count")},
        ),
        (
            "Tarihler",
            {
                "fields": ("published_at", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    readonly_fields = (
        "created_at",
        "updated_at",
        "reading_time",
        "view_count",
        "blog_image_preview",
    )
    prepopulated_fields = {"slug": ("title",)}

    def blog_image_preview(self, obj):
        if obj.featured_image:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 200px;" />',
                obj.featured_image.url,
            )
        return "No image"

    blog_image_preview.short_description = "Featured Image Preview"

    @admin.action(description="Reindex selected posts in search engine")
    def reindex_selected_posts(self, request, queryset):
        """Reindex selected blog posts to search engine"""
        try:
            from apps.main.search_index import search_index_manager

            results = search_index_manager.bulk_index(list(queryset))

            self.message_user(
                request,
                format_html(
                    "✓ Reindexed {} posts. Indexed: {}, Skipped: {}, Failed: {}",
                    queryset.count(),
                    results["indexed"],
                    results["skipped"],
                    results["failed"],
                ),
                level="SUCCESS" if results["failed"] == 0 else "WARNING",
            )
        except Exception as e:
            self.message_user(request, f"✗ Reindex failed: {e}", level="ERROR")


@admin.register(MusicPlaylist)
class MusicPlaylistAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "platform",
        "track_count",
        "is_featured",
        "order",
        "is_visible",
    )
    list_filter = ("platform", "is_featured", "is_visible")
    search_fields = ("name", "description")
    list_editable = ("is_featured", "order", "is_visible")
    ordering = ("order", "name")

    fieldsets = (
        ("Temel Bilgiler", {"fields": ("name", "description", "platform")}),
        ("URL & Embed", {"fields": ("url", "embed_url", "embed_preview")}),
        ("Görsel & İstatistik", {"fields": ("cover_image", "track_count")}),
        ("Sıralama & Görünürlük", {"fields": ("is_featured", "order", "is_visible")}),
        (
            "Tarihler",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    readonly_fields = ("created_at", "updated_at", "embed_preview")

    def embed_preview(self, obj):
        if obj.embed_url and obj.platform == "spotify":
            return format_html(
                '<iframe src="{}" width="300" height="152" frameborder="0" allowtransparency="true" allow="encrypted-media"></iframe>',
                obj.embed_url,
            )
        elif obj.embed_url:
            return format_html(
                '<a href="{}" target="_blank">Preview Embed</a>', obj.embed_url
            )
        return "No embed URL"

    embed_preview.short_description = "Embed Preview"


@admin.register(SpotifyCurrentTrack)
class SpotifyCurrentTrackAdmin(admin.ModelAdmin):
    list_display = (
        "track_name",
        "artist_name",
        "album_name",
        "is_playing",
        "last_updated",
    )
    list_filter = ("is_playing", "last_updated")
    search_fields = ("track_name", "artist_name", "album_name")
    ordering = ("-last_updated",)

    fieldsets = (
        (
            "Şarkı Bilgileri",
            {"fields": ("track_name", "artist_name", "album_name", "track_url")},
        ),
        ("Çalma Durumu", {"fields": ("is_playing", "progress_ms", "duration_ms")}),
        (
            "Görsel",
            {
                "fields": ("image_url", "spotify_image_preview"),
                "classes": ("collapse",),
            },
        ),
        (
            "Tarih",
            {
                "fields": ("last_updated",),
            },
        ),
    )

    readonly_fields = ("last_updated", "spotify_image_preview")

    def spotify_image_preview(self, obj):
        if obj.image_url:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 100px;" />',
                obj.image_url,
            )
        return "No image"

    spotify_image_preview.short_description = "Album Cover Preview"


@admin.register(UsefulResource)
class UsefulResourceAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "type",
        "is_free",
        "rating_display",
        "is_featured",
        "is_visible",
        "order",
    )
    list_filter = ("category", "type", "is_free", "is_featured", "is_visible")
    search_fields = ("name", "description", "tags")
    list_editable = ("is_featured", "is_visible", "order")
    ordering = ("category", "order", "name")

    fieldsets = (
        (
            "Temel Bilgiler",
            {"fields": ("name", "description", "url", "category", "type")},
        ),
        (
            "Görsel",
            {
                "fields": ("icon_url", "image", "useful_image_preview"),
                "classes": ("collapse",),
            },
        ),
        ("Değerlendirme & Etiketler", {"fields": ("rating", "is_free", "tags")}),
        ("Görünürlük & Sıralama", {"fields": ("is_featured", "is_visible", "order")}),
        (
            "Tarihler",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    readonly_fields = ("created_at", "updated_at", "useful_image_preview")

    def rating_display(self, obj):
        if obj.rating:
            stars = "⭐" * int(obj.rating)
            return format_html('<span title="{}/5">{}</span>', obj.rating, stars)
        return "-"

    rating_display.short_description = "Rating"

    def useful_image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 200px;" />',
                obj.image.url,
            )
        return "No image"

    useful_image_preview.short_description = "Image Preview"
