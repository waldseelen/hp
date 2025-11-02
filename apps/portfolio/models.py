import base64
import io

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator, validate_email
from django.db import models
from django.utils import timezone

import pyotp
import qrcode

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

    # Two-Factor Authentication fields
    totp_secret = models.CharField(
        max_length=32, blank=True, help_text="TOTP secret key"
    )
    is_2fa_enabled = models.BooleanField(
        default=False, help_text="Whether 2FA is enabled"
    )
    backup_codes = models.JSONField(
        default=list, blank=True, help_text="Backup recovery codes"
    )

    # Security tracking
    failed_login_attempts = models.IntegerField(default=0)
    last_failed_login = models.DateTimeField(null=True, blank=True)
    account_locked_until = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "name"]

    groups = models.ManyToManyField(
        "auth.Group",
        verbose_name="groups",
        blank=True,
        help_text="The groups this user belongs to.",
        related_name="admin_set",
        related_query_name="admin",
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        verbose_name="user permissions",
        blank=True,
        help_text="Specific permissions for this user.",
        related_name="admin_set",
        related_query_name="admin",
    )

    class Meta:
        verbose_name = "Admin User"
        verbose_name_plural = "Admin Users"
        app_label = "portfolio"

    def __str__(self):
        return self.name

    def generate_totp_secret(self):
        """Generate a new TOTP secret"""
        if not self.totp_secret:
            self.totp_secret = pyotp.random_base32()
            self.save(update_fields=["totp_secret"])
        return self.totp_secret

    def get_totp_uri(self, issuer_name="Portfolio Site"):
        """Get TOTP URI for QR code generation"""
        if not self.totp_secret:
            self.generate_totp_secret()

        totp = pyotp.TOTP(self.totp_secret)
        return totp.provisioning_uri(name=self.email, issuer_name=issuer_name)

    def get_qr_code(self):
        """Generate QR code as base64 image"""
        uri = self.get_totp_uri()
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(uri)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        return base64.b64encode(buffer.getvalue()).decode()

    def verify_totp(self, token):
        """Verify TOTP token"""
        if not self.totp_secret or not self.is_2fa_enabled:
            return False

        totp = pyotp.TOTP(self.totp_secret)
        return totp.verify(token, valid_window=1)

    def generate_backup_codes(self, count=8):
        """Generate backup recovery codes"""
        import secrets
        import string

        codes = []
        for _ in range(count):
            code = "".join(
                secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8)
            )
            codes.append(code)

        self.backup_codes = codes
        self.save(update_fields=["backup_codes"])
        return codes

    def use_backup_code(self, code):
        """Use a backup code (one-time use)"""
        if code in self.backup_codes:
            self.backup_codes.remove(code)
            self.save(update_fields=["backup_codes"])
            return True
        return False

    def is_account_locked(self):
        """Check if account is currently locked"""
        if self.account_locked_until:
            return timezone.now() < self.account_locked_until
        return False

    def lock_account(self, duration_minutes=30):
        """Lock account for specified duration"""
        self.account_locked_until = timezone.now() + timezone.timedelta(
            minutes=duration_minutes
        )
        self.save(update_fields=["account_locked_until"])

    def unlock_account(self):
        """Unlock account and reset failed attempts"""
        self.failed_login_attempts = 0
        self.account_locked_until = None
        self.last_failed_login = None
        self.save(
            update_fields=[
                "failed_login_attempts",
                "account_locked_until",
                "last_failed_login",
            ]
        )

    def record_failed_login(self):
        """Record a failed login attempt"""
        self.failed_login_attempts += 1
        self.last_failed_login = timezone.now()

        # Lock account after 5 failed attempts
        if self.failed_login_attempts >= 5:
            self.lock_account()

        self.save(
            update_fields=[
                "failed_login_attempts",
                "last_failed_login",
                "account_locked_until",
            ]
        )

    def record_successful_login(self):
        """Reset failed login attempts on successful login"""
        if self.failed_login_attempts > 0:
            self.failed_login_attempts = 0
            self.last_failed_login = None
            self.save(update_fields=["failed_login_attempts", "last_failed_login"])


class UserSession(models.Model):
    """Track user sessions for security management"""

    user = models.ForeignKey(Admin, on_delete=models.CASCADE, related_name="sessions")
    session_key = models.CharField(max_length=40, unique=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    location = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    last_activity = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-last_activity"]
        indexes = [
            models.Index(fields=["user", "is_active"]),
            models.Index(fields=["session_key"]),
            models.Index(fields=["-last_activity"]),
        ]
        app_label = "portfolio"

    def __str__(self):
        return f"{self.user.email} - {self.ip_address} ({self.created_at})"

    def get_device_info(self):
        """Extract device info from user agent"""

        # Simple device detection
        if "Mobile" in self.user_agent or "Android" in self.user_agent:
            device_type = "Mobile"
        elif "Tablet" in self.user_agent or "iPad" in self.user_agent:
            device_type = "Tablet"
        else:
            device_type = "Desktop"

        # Browser detection
        if "Chrome" in self.user_agent:
            browser = "Chrome"
        elif "Firefox" in self.user_agent:
            browser = "Firefox"
        elif "Safari" in self.user_agent:
            browser = "Safari"
        elif "Edge" in self.user_agent:
            browser = "Edge"
        else:
            browser = "Unknown"

        return {
            "device_type": device_type,
            "browser": browser,
            "user_agent": (
                self.user_agent[:100] + "..."
                if len(self.user_agent) > 100
                else self.user_agent
            ),
        }

    def deactivate(self):
        """Deactivate this session"""
        self.is_active = False
        self.save(update_fields=["is_active"])


class CookieConsent(models.Model):
    """Track user cookie consent preferences"""

    CONSENT_CHOICES = [
        ("necessary", "Necessary"),
        ("functional", "Functional"),
        ("analytics", "Analytics"),
        ("marketing", "Marketing"),
    ]

    session_key = models.CharField(max_length=40, db_index=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()

    # Consent preferences
    necessary = models.BooleanField(
        default=True, help_text="Required cookies, always enabled"
    )
    functional = models.BooleanField(
        default=False, help_text="Functional cookies for enhanced experience"
    )
    analytics = models.BooleanField(
        default=False, help_text="Analytics cookies for site improvement"
    )
    marketing = models.BooleanField(
        default=False, help_text="Marketing cookies for personalized ads"
    )

    consent_given_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(help_text="When this consent expires")

    class Meta:
        ordering = ["-consent_given_at"]
        indexes = [
            models.Index(fields=["session_key"]),
            models.Index(fields=["ip_address"]),
            models.Index(fields=["-consent_given_at"]),
            models.Index(fields=["expires_at"]),
        ]
        app_label = "portfolio"

    def save(self, *args, **kwargs):
        # Set expiration to 1 year from consent date if not set
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(days=365)
        super().save(*args, **kwargs)

    def is_expired(self):
        """Check if consent has expired"""
        return timezone.now() > self.expires_at

    def get_consent_summary(self):
        """Get a summary of consent preferences"""
        return {
            "necessary": self.necessary,
            "functional": self.functional,
            "analytics": self.analytics,
            "marketing": self.marketing,
        }

    def __str__(self):
        return f"Cookie Consent ({self.session_key}) - {self.consent_given_at}"


class DataExportRequest(models.Model):
    """Track data export requests for GDPR compliance"""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    user = models.ForeignKey(
        Admin, on_delete=models.CASCADE, related_name="export_requests"
    )
    email = models.EmailField(help_text="Email where export will be sent")
    request_date = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    file_path = models.CharField(
        max_length=500, blank=True, help_text="Path to generated export file"
    )
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ["-request_date"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["-request_date"]),
        ]
        app_label = "portfolio"

    def __str__(self):
        return f"Data Export for {self.user.email} - {self.status}"


class AccountDeletionRequest(models.Model):
    """Track account deletion requests for GDPR compliance"""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    user = models.ForeignKey(
        Admin, on_delete=models.CASCADE, related_name="deletion_requests"
    )
    email = models.EmailField(help_text="User's email for confirmation")
    reason = models.TextField(blank=True, help_text="Optional reason for deletion")
    confirmation_token = models.CharField(max_length=100, unique=True)

    request_date = models.DateTimeField(default=timezone.now)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    scheduled_deletion = models.DateTimeField(help_text="When account will be deleted")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    # Backup info before deletion
    user_data_backup = models.JSONField(
        default=dict, help_text="Backup of user data before deletion"
    )

    class Meta:
        ordering = ["-request_date"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["confirmation_token"]),
            models.Index(fields=["scheduled_deletion"]),
        ]
        app_label = "portfolio"

    def save(self, *args, **kwargs):
        # Set scheduled deletion to 30 days from request if not set
        if not self.scheduled_deletion:
            self.scheduled_deletion = timezone.now() + timezone.timedelta(days=30)
        super().save(*args, **kwargs)

    def generate_confirmation_token(self):
        """Generate a secure confirmation token"""
        import secrets

        self.confirmation_token = secrets.token_urlsafe(32)
        self.save(update_fields=["confirmation_token"])
        return self.confirmation_token

    def is_expired(self):
        """Check if deletion request has expired (72 hours for confirmation)"""
        if self.status == "pending":
            return timezone.now() > (self.request_date + timezone.timedelta(hours=72))
        return False

    def confirm_deletion(self):
        """Confirm the deletion request"""
        self.status = "confirmed"
        self.confirmed_at = timezone.now()
        self.save(update_fields=["status", "confirmed_at"])

    def cancel_deletion(self):
        """Cancel the deletion request"""
        self.status = "cancelled"
        self.save(update_fields=["status"])

    def __str__(self):
        return f"Account Deletion for {self.user.email} - {self.status}"


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
        indexes = [
            # Primary access patterns
            models.Index(fields=["is_visible", "order"], name="personal_vis_order"),
            models.Index(fields=["key"], name="personal_key"),
            models.Index(fields=["type", "is_visible"], name="personal_type_vis"),
            # Additional performance indexes
            models.Index(
                fields=["is_visible", "type", "order"], name="personal_vis_type_ord"
            ),
            models.Index(fields=["-updated_at"], name="personal_updated_desc"),
        ]
        app_label = "portfolio"

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
        indexes = [
            # Primary access patterns
            models.Index(fields=["is_visible", "order"], name="social_vis_order"),
            models.Index(fields=["platform", "is_visible"], name="social_plat_vis"),
            models.Index(fields=["is_primary"], name="social_primary"),
            # Additional performance indexes
            models.Index(fields=["platform"], name="social_platform"),
            models.Index(
                fields=["is_visible", "platform", "order"], name="social_vis_plat_ord"
            ),
        ]
        app_label = "portfolio"

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
        indexes = [
            models.Index(fields=["category", "is_visible", "order"]),
            models.Index(fields=["is_featured", "-created_at"]),
            models.Index(fields=["is_visible", "category"]),
            models.Index(fields=["rating", "is_visible"]),
        ]
        app_label = "portfolio"

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
        indexes = [
            models.Index(fields=["type", "is_visible", "order"]),
            models.Index(fields=["is_urgent", "-severity_level"]),
            models.Index(fields=["is_featured", "-created_at"]),
            models.Index(fields=["difficulty", "type"]),
        ]
        app_label = "portfolio"

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
        indexes = [
            models.Index(fields=["is_visible", "order"]),
            models.Index(fields=["name"]),
        ]
        app_label = "portfolio"

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
        indexes = [
            models.Index(fields=["status", "-published_at"]),
            models.Index(fields=["category", "status", "-published_at"]),
            models.Index(fields=["author", "-published_at"]),
            models.Index(fields=["is_featured", "status"]),
            models.Index(fields=["slug"]),
        ]
        app_label = "portfolio"

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
        indexes = [
            models.Index(fields=["is_visible", "order"]),
            models.Index(fields=["platform", "is_visible"]),
            models.Index(fields=["is_featured", "-created_at"]),
        ]
        app_label = "portfolio"

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
        app_label = "portfolio"

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
        indexes = [
            models.Index(fields=["category", "is_visible", "order"]),
            models.Index(fields=["type", "category"]),
            models.Index(fields=["is_featured", "-created_at"]),
            models.Index(fields=["is_free", "category"]),
            models.Index(fields=["rating", "is_visible"]),
        ]
        app_label = "portfolio"

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"


# ==========================================================================
# PERFORMANCE MONITORING MODELS
# ==========================================================================


class PerformanceMetric(models.Model):
    METRIC_TYPE_CHOICES = [
        ("lcp", "Largest Contentful Paint"),
        ("fid", "First Input Delay"),
        ("cls", "Cumulative Layout Shift"),
        ("inp", "Interaction to Next Paint"),
        ("ttfb", "Time to First Byte"),
        ("fcp", "First Contentful Paint"),
        ("navigation", "Navigation Timing"),
        ("resource", "Resource Loading"),
        ("memory", "Memory Usage"),
        ("custom", "Custom Metric"),
    ]

    SESSION_CHOICES = [
        ("mobile", "Mobile"),
        ("desktop", "Desktop"),
        ("tablet", "Tablet"),
    ]

    CONNECTION_CHOICES = [
        ("4g", "4G"),
        ("3g", "3G"),
        ("2g", "2G"),
        ("slow-2g", "Slow 2G"),
        ("wifi", "WiFi"),
        ("ethernet", "Ethernet"),
        ("unknown", "Unknown"),
    ]

    # Core metric data
    metric_type = models.CharField(
        max_length=20,
        choices=METRIC_TYPE_CHOICES,
        help_text="Type of performance metric",
    )
    value = models.FloatField(
        help_text="Metric value in appropriate unit (ms, ratio, bytes, etc.)"
    )
    url = models.URLField(
        max_length=500, help_text="Page URL where metric was collected"
    )

    # Context information
    user_agent = models.TextField(blank=True, help_text="Browser user agent string")
    device_type = models.CharField(
        max_length=10,
        choices=SESSION_CHOICES,
        default="desktop",
        help_text="Device type",
    )
    connection_type = models.CharField(
        max_length=10,
        choices=CONNECTION_CHOICES,
        default="unknown",
        help_text="Network connection type",
    )
    screen_resolution = models.CharField(
        max_length=20, blank=True, help_text="Screen resolution (e.g., 1920x1080)"
    )
    viewport_size = models.CharField(
        max_length=20, blank=True, help_text="Viewport size (e.g., 1200x800)"
    )

    # Additional data
    additional_data = models.JSONField(
        default=dict, blank=True, help_text="Additional metric data as JSON"
    )

    # Metadata
    session_id = models.CharField(
        max_length=50, blank=True, help_text="Browser session identifier"
    )
    ip_address = models.GenericIPAddressField(
        blank=True, null=True, help_text="Client IP address"
    )
    country_code = models.CharField(
        max_length=2, blank=True, help_text="Country code (ISO 3166-1 alpha-2)"
    )

    # Timing
    timestamp = models.DateTimeField(
        default=timezone.now, help_text="When the metric was collected"
    )
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-timestamp"]
        verbose_name = "Performance Metric"
        verbose_name_plural = "Performance Metrics"
        indexes = [
            models.Index(fields=["timestamp", "metric_type"]),
            models.Index(fields=["metric_type", "timestamp"]),
            models.Index(fields=["url", "timestamp"]),
            models.Index(fields=["device_type", "timestamp"]),
            models.Index(fields=["session_id"]),
        ]
        app_label = "portfolio"

    def __str__(self):
        return f"{self.get_metric_type_display()}: {self.value} ({self.device_type})"

    @property
    def is_good_score(self):
        """Check if metric value is considered good based on Web Vitals thresholds"""
        from django.conf import settings

        thresholds = getattr(settings, "CORE_WEB_VITALS", {})

        if self.metric_type == "lcp":
            return (
                self.value <= thresholds.get("LCP_THRESHOLD", 2.5) * 1000
            )  # Convert to ms
        elif self.metric_type == "fid":
            return (
                self.value <= thresholds.get("FID_THRESHOLD", 0.1) * 1000
            )  # Convert to ms
        elif self.metric_type == "cls":
            return self.value <= thresholds.get("CLS_THRESHOLD", 0.1)
        elif self.metric_type == "inp":
            return (
                self.value <= thresholds.get("INP_THRESHOLD", 0.2) * 1000
            )  # Convert to ms
        elif self.metric_type == "ttfb":
            return (
                self.value <= thresholds.get("TTFB_THRESHOLD", 0.8) * 1000
            )  # Convert to ms
        return None


# ==========================================================================
# PUSH NOTIFICATIONS MODELS
# ==========================================================================


class WebPushSubscription(models.Model):
    # Subscription data from browser Push API
    endpoint = models.URLField(unique=True, help_text="Push service endpoint URL")
    p256dh = models.TextField(help_text="P-256 ECDH public key (base64 encoded)")
    auth = models.TextField(help_text="Authentication secret (base64 encoded)")

    # User context (optional)
    user_agent = models.TextField(blank=True, help_text="Browser user agent string")
    browser = models.CharField(
        max_length=50, blank=True, help_text="Browser name (Chrome, Firefox, etc.)"
    )
    platform = models.CharField(
        max_length=50, blank=True, help_text="Operating system/platform"
    )

    # Notification preferences
    enabled = models.BooleanField(
        default=True,
        help_text="Whether notifications are enabled for this subscription",
    )
    topics = models.JSONField(
        default=list, blank=True, help_text="List of subscribed notification topics"
    )

    # Metadata
    ip_address = models.GenericIPAddressField(
        blank=True, null=True, help_text="IP address when subscription was created"
    )
    country_code = models.CharField(
        max_length=2, blank=True, help_text="Country code (ISO 3166-1 alpha-2)"
    )

    # Delivery tracking
    total_sent = models.IntegerField(
        default=0, help_text="Total notifications sent to this subscription"
    )
    total_delivered = models.IntegerField(
        default=0, help_text="Total notifications successfully delivered"
    )
    total_failed = models.IntegerField(
        default=0, help_text="Total failed delivery attempts"
    )
    last_success = models.DateTimeField(
        blank=True, null=True, help_text="Last successful notification delivery"
    )
    last_failure = models.DateTimeField(
        blank=True, null=True, help_text="Last failed notification delivery"
    )
    failure_reason = models.CharField(
        max_length=200, blank=True, help_text="Reason for last failure"
    )

    # Timing
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Web Push Subscription"
        verbose_name_plural = "Web Push Subscriptions"
        indexes = [
            models.Index(fields=["enabled", "created_at"]),
            models.Index(fields=["browser"]),
            models.Index(fields=["last_success"]),
        ]
        app_label = "portfolio"

    def __str__(self):
        browser_info = f" ({self.browser})" if self.browser else ""
        return (
            f"Push Subscription{browser_info} - {self.created_at.strftime('%Y-%m-%d')}"
        )

    @property
    def is_active(self):
        """Check if subscription is active based on recent delivery success"""
        if not self.enabled:
            return False

        # If we've never tried to send, consider it active
        if self.total_sent == 0:
            return True

        # If recent failures without success, consider inactive
        if self.last_failure and self.last_success:
            return self.last_success > self.last_failure
        elif self.last_failure and not self.last_success:
            # Check if failure is recent (within last 7 days)
            from datetime import timedelta

            return self.last_failure > timezone.now() - timedelta(days=7)

        return True

    def record_delivery_success(self):
        """Record successful notification delivery"""
        self.total_delivered += 1
        self.last_success = timezone.now()
        self.failure_reason = ""
        self.save(update_fields=["total_delivered", "last_success", "failure_reason"])

    def record_delivery_failure(self, reason=""):
        """Record failed notification delivery"""
        self.total_failed += 1
        self.last_failure = timezone.now()
        self.failure_reason = reason[:200]  # Truncate to field length
        self.save(update_fields=["total_failed", "last_failure", "failure_reason"])

    def increment_sent_count(self):
        """Increment the total sent counter"""
        self.total_sent += 1
        self.save(update_fields=["total_sent"])


class NotificationLog(models.Model):
    NOTIFICATION_TYPE_CHOICES = [
        ("blog_post", "New Blog Post"),
        ("project_update", "Project Update"),
        ("system_update", "System Update"),
        ("newsletter", "Newsletter"),
        ("promotion", "Promotion"),
        ("reminder", "Reminder"),
        ("alert", "Alert"),
        ("custom", "Custom"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("sent", "Sent"),
        ("delivered", "Delivered"),
        ("failed", "Failed"),
        ("expired", "Expired"),
    ]

    # Notification content
    title = models.CharField(max_length=200, help_text="Notification title")
    body = models.TextField(help_text="Notification body text")
    icon = models.URLField(blank=True, help_text="Notification icon URL")
    image = models.URLField(blank=True, help_text="Notification image URL")
    badge = models.URLField(blank=True, help_text="Notification badge URL")

    # Notification metadata
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPE_CHOICES,
        default="custom",
        help_text="Type of notification",
    )
    tag = models.CharField(
        max_length=100, blank=True, help_text="Notification tag for grouping"
    )

    # Action buttons
    actions = models.JSONField(
        default=list,
        blank=True,
        help_text="List of action buttons for the notification",
    )

    # URL to open when clicked
    url = models.URLField(
        blank=True, help_text="URL to open when notification is clicked"
    )

    # Targeting
    subscription = models.ForeignKey(
        WebPushSubscription,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        help_text="Specific subscription (if targeted)",
    )
    topics = models.JSONField(
        default=list, blank=True, help_text="Target topics for broadcast notifications"
    )

    # Delivery tracking
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        help_text="Notification delivery status",
    )
    sent_at = models.DateTimeField(
        blank=True, null=True, help_text="When notification was sent"
    )
    delivered_at = models.DateTimeField(
        blank=True, null=True, help_text="When notification was delivered"
    )
    error_message = models.TextField(
        blank=True, help_text="Error message if delivery failed"
    )

    # Additional data
    additional_data = models.JSONField(
        default=dict, blank=True, help_text="Additional notification data"
    )

    # Timing
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Notification Log"
        verbose_name_plural = "Notification Logs"
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["notification_type", "created_at"]),
            models.Index(fields=["subscription", "status"]),
        ]
        app_label = "portfolio"

    def __str__(self):
        target = f"to {self.subscription.browser}" if self.subscription else "broadcast"
        return f"{self.title} {target} - {self.get_status_display()}"


# ==========================================================================
# ERROR LOGGING MODEL
# ==========================================================================


class ErrorLog(models.Model):
    ERROR_LEVEL_CHOICES = [
        ("debug", "Debug"),
        ("info", "Info"),
        ("warning", "Warning"),
        ("error", "Error"),
        ("critical", "Critical"),
    ]

    ERROR_TYPE_CHOICES = [
        ("javascript", "JavaScript Error"),
        ("python", "Python Exception"),
        ("http", "HTTP Error"),
        ("database", "Database Error"),
        ("validation", "Validation Error"),
        ("permission", "Permission Error"),
        ("network", "Network Error"),
        ("performance", "Performance Issue"),
        ("security", "Security Issue"),
        ("other", "Other"),
    ]

    # Error details
    error_type = models.CharField(
        max_length=20,
        choices=ERROR_TYPE_CHOICES,
        default="other",
        help_text="Category of error",
    )
    level = models.CharField(
        max_length=10,
        choices=ERROR_LEVEL_CHOICES,
        default="error",
        help_text="Error severity level",
    )
    message = models.TextField(help_text="Error message")
    stack_trace = models.TextField(
        blank=True, help_text="Full stack trace or error details"
    )

    # Context information
    url = models.URLField(
        blank=True, max_length=500, help_text="URL where error occurred"
    )
    user_agent = models.TextField(blank=True, help_text="Browser user agent string")
    ip_address = models.GenericIPAddressField(
        blank=True, null=True, help_text="Client IP address"
    )

    # Technical details
    file_name = models.CharField(
        max_length=255, blank=True, help_text="Source file where error occurred"
    )
    line_number = models.IntegerField(
        blank=True, null=True, help_text="Line number where error occurred"
    )
    function_name = models.CharField(
        max_length=100, blank=True, help_text="Function/method where error occurred"
    )

    # Additional context
    additional_data = models.JSONField(
        default=dict, blank=True, help_text="Additional error context as JSON"
    )

    # Resolution tracking
    is_resolved = models.BooleanField(
        default=False, help_text="Whether this error has been resolved"
    )
    resolved_at = models.DateTimeField(
        blank=True, null=True, help_text="When error was marked as resolved"
    )
    resolution_notes = models.TextField(
        blank=True, help_text="Notes about error resolution"
    )

    # Occurrence tracking
    occurrence_count = models.IntegerField(
        default=1, help_text="Number of times this error occurred"
    )
    first_occurred = models.DateTimeField(
        default=timezone.now, help_text="When this error first occurred"
    )
    last_occurred = models.DateTimeField(
        default=timezone.now, help_text="When this error last occurred"
    )

    # Timing
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-last_occurred", "-created_at"]
        verbose_name = "Error Log"
        verbose_name_plural = "Error Logs"
        indexes = [
            models.Index(fields=["error_type", "level", "last_occurred"]),
            models.Index(fields=["is_resolved", "last_occurred"]),
            models.Index(fields=["url", "last_occurred"]),
        ]
        app_label = "portfolio"

    def __str__(self):
        return f"{self.get_level_display()}: {self.message[:100]}..."

    def mark_resolved(self, notes=""):
        """Mark error as resolved"""
        self.is_resolved = True
        self.resolved_at = timezone.now()
        if notes:
            self.resolution_notes = notes
        self.save(update_fields=["is_resolved", "resolved_at", "resolution_notes"])

    def increment_occurrence(self):
        """Increment occurrence count and update last occurred time"""
        self.occurrence_count += 1
        self.last_occurred = timezone.now()
        self.save(update_fields=["occurrence_count", "last_occurred"])


# ==========================================================================
# ANALYTICS MODELS
# ==========================================================================


class AnalyticsEvent(models.Model):
    """Privacy-compliant analytics event tracking"""

    EVENT_TYPE_CHOICES = [
        ("page_view", "Page View"),
        ("custom_event", "Custom Event"),
        ("conversion", "Conversion"),
        ("ab_test_assignment", "A/B Test Assignment"),
        ("ab_test_conversion", "A/B Test Conversion"),
        ("funnel_step", "Funnel Step"),
        ("journey_step", "Journey Step"),
    ]

    # Core event data
    event_type = models.CharField(
        max_length=20, choices=EVENT_TYPE_CHOICES, help_text="Type of analytics event"
    )
    event_name = models.CharField(
        max_length=100, blank=True, help_text="Custom event name"
    )
    anonymous_id = models.CharField(
        max_length=50,
        db_index=True,
        help_text="Anonymous session identifier (privacy-compliant)",
    )

    # Page and context information
    page_path = models.CharField(
        max_length=500, blank=True, help_text="Page path (sanitized)"
    )
    page_title = models.CharField(max_length=200, blank=True, help_text="Page title")
    referrer_type = models.CharField(
        max_length=20, blank=True, help_text="Referrer type (search, social, external)"
    )

    # Device and browser info (aggregated, non-identifying)
    device_type = models.CharField(
        max_length=20, blank=True, help_text="Device type (mobile, desktop, tablet)"
    )
    browser_family = models.CharField(
        max_length=50, blank=True, help_text="Browser family (Chrome, Firefox, Safari)"
    )
    os_family = models.CharField(
        max_length=50, blank=True, help_text="Operating system family"
    )

    # Event-specific data (JSON field for flexibility)
    event_data = models.JSONField(
        default=dict, blank=True, help_text="Additional event data (sanitized)"
    )

    # Privacy and compliance
    gdpr_consent = models.BooleanField(
        default=False, help_text="Whether user has given GDPR consent for analytics"
    )
    ip_hash = models.CharField(
        max_length=64,
        blank=True,
        help_text="Hashed IP address (for geographic insights only)",
    )

    # Timing
    timestamp = models.DateTimeField(
        default=timezone.now, db_index=True, help_text="When the event occurred"
    )
    session_start = models.DateTimeField(
        blank=True, null=True, help_text="When the session started"
    )

    # Retention policy
    expires_at = models.DateTimeField(
        help_text="When this data should be automatically deleted"
    )

    class Meta:
        ordering = ["-timestamp"]
        verbose_name = "Analytics Event"
        verbose_name_plural = "Analytics Events"
        indexes = [
            models.Index(fields=["timestamp", "event_type"]),
            models.Index(fields=["anonymous_id", "timestamp"]),
            models.Index(fields=["event_type", "event_name"]),
            models.Index(fields=["page_path", "timestamp"]),
            models.Index(fields=["expires_at"]),
        ]
        app_label = "portfolio"

    def save(self, *args, **kwargs):
        # Set automatic expiration (90 days default for GDPR compliance)
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(days=90)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.event_type}: {self.event_name or self.page_path} at {self.timestamp}"

    @classmethod
    def cleanup_expired(cls):
        """Remove expired analytics data for GDPR compliance"""
        expired_count = cls.objects.filter(expires_at__lt=timezone.now()).delete()[0]
        return expired_count


class UserJourney(models.Model):
    """Privacy-compliant user journey tracking"""

    journey_id = models.CharField(
        max_length=100, unique=True, help_text="Unique journey identifier"
    )
    anonymous_id = models.CharField(
        max_length=50, db_index=True, help_text="Anonymous session identifier"
    )

    # Journey metadata
    started_at = models.DateTimeField(
        default=timezone.now, help_text="When the journey started"
    )
    last_activity = models.DateTimeField(
        auto_now=True, help_text="Last activity in this journey"
    )
    current_step = models.CharField(
        max_length=100, blank=True, help_text="Current step in the journey"
    )

    # Journey analytics
    total_steps = models.IntegerField(
        default=0, help_text="Total number of steps in this journey"
    )
    total_time_spent = models.IntegerField(
        default=0, help_text="Total time spent in seconds"
    )
    is_completed = models.BooleanField(
        default=False, help_text="Whether the journey reached completion"
    )
    completion_type = models.CharField(
        max_length=50, blank=True, help_text="How the journey was completed"
    )

    # Journey path (stored as JSON for analysis)
    journey_path = models.JSONField(
        default=list, help_text="List of steps taken in this journey"
    )

    # Privacy compliance
    gdpr_consent = models.BooleanField(
        default=False, help_text="GDPR consent for journey tracking"
    )
    expires_at = models.DateTimeField(help_text="When this journey data expires")

    class Meta:
        ordering = ["-started_at"]
        verbose_name = "User Journey"
        verbose_name_plural = "User Journeys"
        indexes = [
            models.Index(fields=["anonymous_id", "started_at"]),
            models.Index(fields=["is_completed", "started_at"]),
            models.Index(fields=["current_step"]),
            models.Index(fields=["expires_at"]),
        ]
        app_label = "portfolio"

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(days=90)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Journey {self.journey_id} - {self.total_steps} steps"

    def add_step(self, step_name, page_path=None, timestamp=None):
        """Add a step to the journey"""
        if timestamp is None:
            timestamp = timezone.now()

        step_data = {
            "step_name": step_name,
            "timestamp": timestamp.isoformat(),
            "page_path": page_path,
            "order": len(self.journey_path) + 1,
        }

        self.journey_path.append(step_data)
        self.current_step = step_name
        self.total_steps = len(self.journey_path)
        self.last_activity = timestamp
        self.save()


class ConversionFunnel(models.Model):
    """Conversion funnel tracking and analytics"""

    funnel_id = models.CharField(
        max_length=100, unique=True, help_text="Unique funnel identifier"
    )
    anonymous_id = models.CharField(
        max_length=50, db_index=True, help_text="Anonymous session identifier"
    )
    funnel_name = models.CharField(
        max_length=50,
        db_index=True,
        help_text="Name of the funnel (signup, purchase, etc.)",
    )

    # Funnel progress
    started_at = models.DateTimeField(
        default=timezone.now, help_text="When the funnel was entered"
    )
    last_activity = models.DateTimeField(
        auto_now=True, help_text="Last activity in this funnel"
    )
    current_step = models.CharField(
        max_length=100, blank=True, help_text="Current step in the funnel"
    )
    current_step_order = models.IntegerField(
        default=1, help_text="Order of current step"
    )

    # Completion tracking
    is_completed = models.BooleanField(
        default=False, help_text="Whether the funnel was completed"
    )
    completed_at = models.DateTimeField(
        blank=True, null=True, help_text="When the funnel was completed"
    )
    time_to_complete = models.IntegerField(
        blank=True, null=True, help_text="Time to complete in seconds"
    )

    # Funnel data
    steps_completed = models.JSONField(
        default=list, help_text="List of completed steps with timing"
    )
    drop_off_step = models.CharField(
        max_length=100, blank=True, help_text="Step where user dropped off"
    )

    # Privacy compliance
    gdpr_consent = models.BooleanField(
        default=False, help_text="GDPR consent for funnel tracking"
    )
    expires_at = models.DateTimeField(help_text="When this funnel data expires")

    class Meta:
        ordering = ["-started_at"]
        verbose_name = "Conversion Funnel"
        verbose_name_plural = "Conversion Funnels"
        indexes = [
            models.Index(fields=["funnel_name", "started_at"]),
            models.Index(fields=["anonymous_id", "funnel_name"]),
            models.Index(fields=["is_completed", "funnel_name"]),
            models.Index(fields=["expires_at"]),
        ]
        app_label = "portfolio"

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(days=90)
        super().save(*args, **kwargs)

    def __str__(self):
        status = "completed" if self.is_completed else f"step {self.current_step_order}"
        return f"{self.funnel_name} funnel - {status}"

    def complete_step(self, step_name, step_order, is_final=False):
        """Mark a step as completed"""
        step_data = {
            "step_name": step_name,
            "step_order": step_order,
            "timestamp": timezone.now().isoformat(),
            "time_since_start": (timezone.now() - self.started_at).total_seconds(),
        }

        self.steps_completed.append(step_data)
        self.current_step = step_name
        self.current_step_order = step_order

        if is_final:
            self.is_completed = True
            self.completed_at = timezone.now()
            self.time_to_complete = (timezone.now() - self.started_at).total_seconds()

        self.save()


class ABTestAssignment(models.Model):
    """A/B test variant assignments and tracking"""

    test_name = models.CharField(
        max_length=100, db_index=True, help_text="Name of the A/B test"
    )
    anonymous_id = models.CharField(
        max_length=50, db_index=True, help_text="Anonymous session identifier"
    )
    variant = models.CharField(
        max_length=50, help_text="Assigned variant (A, B, C, etc.)"
    )

    # Assignment details
    assigned_at = models.DateTimeField(
        default=timezone.now, help_text="When the variant was assigned"
    )
    assignment_method = models.CharField(
        max_length=20,
        default="hash",
        help_text="Method used for assignment (hash, random)",
    )

    # Conversion tracking
    has_converted = models.BooleanField(
        default=False, help_text="Whether this user has converted"
    )
    converted_at = models.DateTimeField(
        blank=True, null=True, help_text="When the conversion occurred"
    )
    conversion_type = models.CharField(
        max_length=50, blank=True, help_text="Type of conversion"
    )
    conversion_value = models.FloatField(
        blank=True, null=True, help_text="Value of the conversion"
    )

    # Test data
    test_data = models.JSONField(
        default=dict, blank=True, help_text="Additional test-specific data"
    )

    # Privacy compliance
    gdpr_consent = models.BooleanField(
        default=False, help_text="GDPR consent for A/B testing"
    )
    expires_at = models.DateTimeField(help_text="When this test data expires")

    class Meta:
        ordering = ["-assigned_at"]
        verbose_name = "A/B Test Assignment"
        verbose_name_plural = "A/B Test Assignments"
        unique_together = ["test_name", "anonymous_id"]
        indexes = [
            models.Index(fields=["test_name", "variant"]),
            models.Index(fields=["anonymous_id", "test_name"]),
            models.Index(fields=["has_converted", "test_name"]),
            models.Index(fields=["expires_at"]),
        ]
        app_label = "portfolio"

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(days=90)
        super().save(*args, **kwargs)

    def __str__(self):
        status = "converted" if self.has_converted else "active"
        return f"{self.test_name}: {self.variant} ({status})"

    def record_conversion(self, conversion_type="default", conversion_value=None):
        """Record a conversion for this assignment"""
        self.has_converted = True
        self.converted_at = timezone.now()
        self.conversion_type = conversion_type
        self.conversion_value = conversion_value
        self.save()


# ==========================================================================
# SHORT URL MODEL
# ==========================================================================


class ShortURL(models.Model):
    """Model for URL shortening service"""

    short_code = models.CharField(
        max_length=10, unique=True, help_text="Short code for the URL"
    )
    original_url = models.URLField(max_length=2000, help_text="Original long URL")
    title = models.CharField(
        max_length=200, blank=True, help_text="Optional title for the link"
    )
    description = models.TextField(blank=True, help_text="Optional description")
    password = models.CharField(
        max_length=50, blank=True, help_text="Optional password protection"
    )

    # Tracking
    click_count = models.IntegerField(default=0, help_text="Number of clicks")
    is_active = models.BooleanField(
        default=True, help_text="Whether the short URL is active"
    )

    # Metadata
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(
        blank=True, null=True, help_text="Expiration date (optional)"
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Short URL"
        verbose_name_plural = "Short URLs"
        indexes = [
            models.Index(fields=["short_code"]),
            models.Index(fields=["is_active", "expires_at"]),
        ]
        app_label = "portfolio"

    def __str__(self):
        return f"{self.short_code} -> {self.original_url[:50]}..."

    def increment_click(self):
        """Increment click count"""
        self.click_count += 1
        self.save(update_fields=["click_count"])

    @property
    def is_expired(self):
        """Check if the short URL has expired"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False

    def get_short_url(self):
        """Get the full short URL"""
        from django.conf import settings

        domain = getattr(settings, "DOMAIN", "localhost:8000")
        return f"https://{domain}/s/{self.short_code}"

    def save(self, *args, **kwargs):
        """Generate short code if not exists"""
        if not self.short_code:
            import random
            import string

            # Generate a random short code
            chars = string.ascii_letters + string.digits
            while True:
                code = "".join(random.choice(chars) for _ in range(6))
                if not ShortURL.objects.filter(short_code=code).exists():
                    self.short_code = code
                    break

        super().save(*args, **kwargs)
