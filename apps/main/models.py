from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator, validate_email
from django.db import models
from django.utils import timezone

from apps.core.utils.model_helpers import (
    auto_set_published_at,
    calculate_reading_time,
    generate_unique_slug,
)


class Admin(AbstractUser):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100, help_text="Display name for the portfolio")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    # FIX GROUPS AND PERMISSIONS CLASH
    groups = models.ManyToManyField(
        "auth.Group",
        verbose_name="groups",
        blank=True,
        help_text="The groups this user belongs to.",
        related_name="admin_users",
        related_query_name="admin_user",
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        verbose_name="user permissions",
        blank=True,
        help_text="Specific permissions for this user.",
        related_name="admin_users",
        related_query_name="admin_user",
    )

    # Use username as primary, not email
    REQUIRED_FIELDS = ["email", "name"]

    class Meta:
        verbose_name = "Admin User"
        verbose_name_plural = "Admin Users"

    def __str__(self):
        return self.name


class PersonalInfo(models.Model):
    TYPE_CHOICES = [
        ("text", "Text"),
        ("json", "JSON"),
        ("markdown", "Markdown"),
        ("html", "HTML"),
    ]

    key = models.CharField(
        max_length=100, unique=True, help_text="Unique identifier for this information"
    )
    value = models.TextField(help_text="The content/value of this information")
    type = models.CharField(
        max_length=10,
        choices=TYPE_CHOICES,
        default="text",
        help_text="How this content should be rendered",
    )
    order = models.IntegerField(
        default=0, help_text="Display order (lower numbers appear first)"
    )
    is_visible = models.BooleanField(
        default=True, help_text="Whether this information is visible on the site"
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "key"]
        verbose_name = "Personal Information"
        verbose_name_plural = "Personal Information"

    def clean(self):
        if self.type == "json":
            import json

            try:
                json.loads(self.value)
            except json.JSONDecodeError:
                raise ValidationError({"value": "Invalid JSON format"})

    def __str__(self):
        return f"{self.key} ({self.get_type_display()})"


class SocialLink(models.Model):
    PLATFORM_CHOICES = [
        ("github", "GitHub"),
        ("linkedin", "LinkedIn"),
        ("twitter", "Twitter"),
        ("instagram", "Instagram"),
        ("facebook", "Facebook"),
        ("youtube", "YouTube"),
        ("tiktok", "TikTok"),
        ("discord", "Discord"),
        ("telegram", "Telegram"),
        ("whatsapp", "WhatsApp"),
        ("email", "Email"),
        ("website", "Website"),
        ("other", "Other"),
    ]

    platform = models.CharField(
        max_length=50, choices=PLATFORM_CHOICES, help_text="Social media platform"
    )
    url = models.CharField(
        max_length=255, help_text="URL to your profile or email address"
    )
    description = models.TextField(
        blank=True, null=True, help_text="Optional description of this social link"
    )
    stats = models.JSONField(
        blank=True, null=True, help_text="JSON data for follower counts, etc."
    )
    is_primary = models.BooleanField(
        default=False, help_text="Mark as primary/main social link"
    )
    is_visible = models.BooleanField(
        default=True, help_text="Whether this link is visible on the site"
    )
    order = models.IntegerField(
        default=0, help_text="Display order (lower numbers appear first)"
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "platform"]
        verbose_name = "Social Link"
        verbose_name_plural = "Social Links"
        unique_together = ["platform", "url"]

    def clean(self):
        # Handle email platform separately
        if self.platform == "email":
            try:
                email_address = self.url.replace("mailto:", "")
                validate_email(email_address)
                if not self.url.lower().startswith("mailto:"):
                    self.url = f"mailto:{self.url}"
            except ValidationError:
                raise ValidationError({"url": "Please enter a valid email address"})
        else:
            # Validate URL format for non-email platforms
            try:
                URLValidator(schemes=["http", "https"])(self.url)
            except ValidationError:
                raise ValidationError({"url": "Please enter a valid URL"})

            # Platform-specific URL validation
            url_lower = self.url.lower()
            if self.platform == "github" and "github.com" not in url_lower:
                raise ValidationError({"url": "GitHub URL must contain github.com"})
            elif self.platform == "linkedin" and "linkedin.com" not in url_lower:
                raise ValidationError({"url": "LinkedIn URL must contain linkedin.com"})
            elif self.platform == "twitter" and not any(
                x in url_lower for x in ["twitter.com", "x.com"]
            ):
                raise ValidationError(
                    {"url": "Twitter URL must contain twitter.com or x.com"}
                )

    def save(self, *args, **kwargs):
        # Ensure only one primary link
        if self.is_primary:
            SocialLink.objects.filter(is_primary=True).exclude(pk=self.pk).update(
                is_primary=False
            )
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_platform_display()}{' (Primary)' if self.is_primary else ''}"


class AITool(models.Model):
    CATEGORY_CHOICES = [
        ("general", "Genel Platformlar & Sohbet"),
        ("visual", "Görsel & Tasarım"),
        ("video", "Video & Animasyon"),
        ("audio", "Ses, Müzik & Podcast"),
        ("text", "Yazı & İçerik Üretimi"),
        ("code", "Kodlama & Geliştirme"),
        ("research", "Araştırma & Akademik"),
        ("productivity", "Verimlilik & Yardımcı Araçlar"),
        ("other", "Diğer"),
    ]

    name = models.CharField(max_length=100, help_text="AI aracının adı")
    description = models.TextField(help_text="AI aracının kısa açıklaması")
    url = models.URLField(help_text="AI aracının web sitesi URL'si")
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default="general",
        help_text="AI aracının kategorisi",
    )
    icon_url = models.URLField(
        blank=True, null=True, help_text="AI aracının ikonu URL'si (opsiyonel)"
    )
    image = models.ImageField(
        upload_to="ai_tools/", blank=True, null=True, help_text="AI aracının görseli"
    )
    is_featured = models.BooleanField(
        default=False, help_text="Öne çıkan araç olarak işaretle"
    )
    is_free = models.BooleanField(default=True, help_text="Ücretsiz mi?")
    rating = models.FloatField(default=0.0, help_text="Kişisel değerlendirme (0-5)")
    tags = models.CharField(
        max_length=200,
        blank=True,
        help_text="Virgülle ayrılmış etiketler (AI, GPT, vs.)",
    )
    order = models.IntegerField(
        default=0, help_text="Sıralama (küçük sayılar önce görünür)"
    )
    is_visible = models.BooleanField(
        default=True, help_text="Site üzerinde görünür mü?"
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["category", "order", "name"]
        verbose_name = "AI Tool"
        verbose_name_plural = "AI Tools"

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"


class CybersecurityResource(models.Model):
    TYPE_CHOICES = [
        ("tool", "Güvenlik Aracı"),
        ("threat", "Tehdit Türü"),
        ("standard", "Standart/Framework"),
        ("practice", "En İyi Uygulama"),
        ("news", "Güncel Haber/Tehdit"),
        ("tutorial", "Eğitim/Rehber"),
        ("certification", "Sertifikasyon"),
        ("other", "Diğer"),
    ]

    DIFFICULTY_CHOICES = [
        ("beginner", "Başlangıç"),
        ("intermediate", "Orta"),
        ("advanced", "İleri"),
        ("expert", "Uzman"),
    ]

    title = models.CharField(max_length=150, help_text="Kaynak başlığı")
    description = models.TextField(help_text="Kaynağın detaylı açıklaması")
    content = models.TextField(blank=True, help_text="Ana içerik (Markdown destekli)")
    type = models.CharField(
        max_length=20, choices=TYPE_CHOICES, default="tool", help_text="Kaynak türü"
    )
    difficulty = models.CharField(
        max_length=20,
        choices=DIFFICULTY_CHOICES,
        default="beginner",
        help_text="Zorluk seviyesi",
    )
    url = models.URLField(blank=True, null=True, help_text="İlgili web sitesi URL'si")
    image = models.ImageField(
        upload_to="cybersecurity/", blank=True, null=True, help_text="Kaynak görseli"
    )
    tags = models.CharField(
        max_length=200,
        blank=True,
        help_text="Virgülle ayrılmış etiketler (malware, firewall, vs.)",
    )
    is_featured = models.BooleanField(
        default=False, help_text="Öne çıkan kaynak olarak işaretle"
    )
    is_urgent = models.BooleanField(default=False, help_text="Acil/güncel tehdit mi?")
    severity_level = models.IntegerField(
        default=1,
        choices=[(1, "Düşük"), (2, "Orta"), (3, "Yüksek"), (4, "Kritik")],
        help_text="Önem/ciddiyet seviyesi",
    )
    order = models.IntegerField(default=0, help_text="Sıralama")
    is_visible = models.BooleanField(
        default=True, help_text="Site üzerinde görünür mü?"
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_urgent", "-severity_level", "type", "order", "title"]
        verbose_name = "Cybersecurity Resource"
        verbose_name_plural = "Cybersecurity Resources"

    def __str__(self):
        return f"{self.title} ({self.get_type_display()})"


class BlogCategory(models.Model):
    CATEGORY_CHOICES = [
        ("philosophy", "Felsefe"),
        ("history", "Tarih"),
        ("sociology", "Sosyoloji"),
        ("technology", "Teknoloji"),
        ("personal", "Kişisel"),
        ("other", "Diğer"),
    ]

    name = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        unique=True,
        help_text="Blog kategorisi",
    )
    display_name = models.CharField(
        max_length=100, help_text="Görüntülenecek kategori adı"
    )
    description = models.TextField(blank=True, help_text="Kategori açıklaması")
    color = models.CharField(
        max_length=7, default="#3B82F6", help_text="Kategori rengi (hex kod)"
    )
    icon = models.CharField(
        max_length=50, blank=True, help_text="Kategori ikonu (CSS class veya emoji)"
    )
    order = models.IntegerField(default=0, help_text="Sıralama")
    is_visible = models.BooleanField(
        default=True, help_text="Site üzerinde görünür mü?"
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "display_name"]
        verbose_name = "Blog Category"
        verbose_name_plural = "Blog Categories"

    def __str__(self):
        return self.display_name


class BlogPost(models.Model):
    STATUS_CHOICES = [
        ("draft", "Taslak"),
        ("published", "Yayınlandı"),
        ("archived", "Arşivlendi"),
    ]

    title = models.CharField(max_length=200, help_text="Blog yazısının başlığı")
    slug = models.SlugField(
        max_length=200,
        unique=True,
        help_text="URL için benzersiz slug (otomatik oluşturulur)",
    )
    category = models.ForeignKey(
        BlogCategory,
        on_delete=models.CASCADE,
        related_name="posts",
        help_text="Blog yazısının kategorisi",
    )
    excerpt = models.TextField(max_length=300, help_text="Kısa özet (300 karakter)")
    content = models.TextField(help_text="Ana içerik (Markdown destekli)")
    featured_image = models.ImageField(
        upload_to="blog_posts/", blank=True, null=True, help_text="Öne çıkan görsel"
    )
    tags = models.CharField(
        max_length=200, blank=True, help_text="Virgülle ayrılmış etiketler"
    )
    author = models.ForeignKey(
        Admin,
        on_delete=models.CASCADE,
        related_name="blog_posts",
        help_text="Yazı sahibi",
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="draft", help_text="Yazı durumu"
    )
    is_featured = models.BooleanField(
        default=False, help_text="Öne çıkan yazı olarak işaretle"
    )
    reading_time = models.IntegerField(
        default=0, help_text="Tahmini okuma süresi (dakika)"
    )
    view_count = models.IntegerField(default=0, help_text="Görüntülenme sayısı")
    meta_description = models.CharField(
        max_length=160, blank=True, help_text="SEO meta açıklama"
    )
    published_at = models.DateTimeField(
        blank=True, null=True, help_text="Yayınlanma tarihi"
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-published_at", "-created_at"]
        verbose_name = "Blog Post"
        verbose_name_plural = "Blog Posts"

    def save(self, *args, **kwargs):
        # Auto-generate unique slug from title
        if not self.slug:
            self.slug = generate_unique_slug(self)

        # Otomatik okuma süresi hesaplama (ortalama 200 kelime/dakika)
        if self.content:
            self.reading_time = calculate_reading_time(self.content)

        # Yayınlanma tarihi otomatik set etme
        auto_set_published_at(self)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"


class MusicPlaylist(models.Model):
    PLATFORM_CHOICES = [
        ("spotify", "Spotify"),
        ("youtube", "YouTube Music"),
        ("apple", "Apple Music"),
        ("soundcloud", "SoundCloud"),
        ("other", "Diğer"),
    ]

    name = models.CharField(max_length=100, help_text="Playlist adı")
    description = models.TextField(blank=True, help_text="Playlist açıklaması")
    platform = models.CharField(
        max_length=20,
        choices=PLATFORM_CHOICES,
        default="spotify",
        help_text="Müzik platformu",
    )
    url = models.URLField(help_text="Playlist URL'si")
    embed_url = models.URLField(
        blank=True, help_text="Embed için URL (otomatik oluşturulur)"
    )
    cover_image = models.URLField(blank=True, help_text="Playlist kapak görseli URL'si")
    track_count = models.IntegerField(default=0, help_text="Şarkı sayısı")
    is_featured = models.BooleanField(
        default=False, help_text="Öne çıkan playlist olarak işaretle"
    )
    order = models.IntegerField(default=0, help_text="Sıralama")
    is_visible = models.BooleanField(
        default=True, help_text="Site üzerinde görünür mü?"
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "name"]
        verbose_name = "Music Playlist"
        verbose_name_plural = "Music Playlists"

    def save(self, *args, **kwargs):
        # Spotify embed URL otomatik oluşturma
        if self.platform == "spotify" and self.url and not self.embed_url:
            if "playlist/" in self.url:
                playlist_id = self.url.split("playlist/")[-1].split("?")[0]
                self.embed_url = f"https://open.spotify.com/embed/playlist/{playlist_id}?utm_source=generator"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.get_platform_display()})"


class SpotifyCurrentTrack(models.Model):
    track_name = models.CharField(max_length=200, help_text="Şarkı adı")
    artist_name = models.CharField(max_length=200, help_text="Sanatçı adı")
    album_name = models.CharField(max_length=200, blank=True, help_text="Albüm adı")
    track_url = models.URLField(blank=True, help_text="Spotify şarkı URL'si")
    image_url = models.URLField(blank=True, help_text="Albüm kapağı URL'si")
    is_playing = models.BooleanField(default=False, help_text="Şu an çalıyor mu?")
    progress_ms = models.IntegerField(
        default=0, help_text="Çalma ilerlemesi (milisaniye)"
    )
    duration_ms = models.IntegerField(default=0, help_text="Şarkı süresi (milisaniye)")
    last_updated = models.DateTimeField(auto_now=True, help_text="Son güncelleme")

    class Meta:
        verbose_name = "Spotify Current Track"
        verbose_name_plural = "Spotify Current Track"
        get_latest_by = "last_updated"

    def __str__(self):
        return f"{self.track_name} - {self.artist_name}"


class UsefulResource(models.Model):
    TYPE_CHOICES = [
        ("website", "Website"),
        ("app", "Uygulama"),
        ("tool", "Araç"),
        ("extension", "Tarayıcı Eklentisi"),
        ("other", "Diğer"),
    ]

    CATEGORY_CHOICES = [
        ("development", "Geliştirme"),
        ("design", "Tasarım"),
        ("productivity", "Verimlilik"),
        ("ai", "Yapay Zeka"),
        ("learning", "Öğrenme"),
        ("entertainment", "Eğlence"),
        ("utility", "Yardımcı Programlar"),
        ("other", "Diğer"),
    ]

    name = models.CharField(max_length=100, help_text="Kaynak adı")
    description = models.TextField(help_text="Kaynak açıklaması")
    url = models.URLField(help_text="Kaynak URL'si")
    type = models.CharField(
        max_length=20, choices=TYPE_CHOICES, default="website", help_text="Kaynak türü"
    )
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default="utility",
        help_text="Kaynak kategorisi",
    )
    icon_url = models.URLField(blank=True, null=True, help_text="Kaynak ikonu URL'si")
    image = models.ImageField(
        upload_to="useful_resources/", blank=True, null=True, help_text="Kaynak görseli"
    )
    is_free = models.BooleanField(default=True, help_text="Ücretsiz mi?")
    is_featured = models.BooleanField(
        default=False, help_text="Öne çıkan kaynak olarak işaretle"
    )
    rating = models.FloatField(default=0.0, help_text="Kişisel değerlendirme (0-5)")
    tags = models.CharField(
        max_length=200, blank=True, help_text="Virgülle ayrılmış etiketler"
    )
    order = models.IntegerField(default=0, help_text="Sıralama")
    is_visible = models.BooleanField(
        default=True, help_text="Site üzerinde görünür mü?"
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["category", "order", "name"]
        verbose_name = "Useful Resource"
        verbose_name_plural = "Useful Resources"

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"
