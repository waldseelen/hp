from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import models
from django.utils import timezone
from django.utils.functional import cached_property

from apps.main.file_validators import image_validator


class ToolManager(models.Manager):
    def favorites(self):
        """Get all favorite tools"""
        return self.filter(is_favorite=True)

    def by_category(self, category):
        """Get tools by category"""
        return self.filter(category__iexact=category)

    def visible(self):
        """Get all visible tools"""
        return self.filter(is_visible=True)

    def get_similar_tools(self, tool, limit=3):
        """Get similar tools based on category and tag similarity

        Args:
            tool: The Tool instance to find similar tools for
            limit: Maximum number of similar tools to return

        Returns:
            List of similar Tool instances, sorted by tag similarity

        Note:
            Optimized to fetch all matching tools in a single query
        """
        # Fetch all similar tools in one query (no related objects to prefetch)
        similar = self.visible().filter(category=tool.category).exclude(pk=tool.pk)

        if tool.tags:
            # Score by tag similarity
            scored_tools = []
            for similar_tool in similar:
                if similar_tool.tags:
                    common_tags = set(tool.tags) & set(similar_tool.tags)
                    if common_tags:
                        scored_tools.append((len(common_tags), similar_tool))

            # Sort by score and return top results
            scored_tools.sort(key=lambda x: x[0], reverse=True)
            return [similar_tool for _, similar_tool in scored_tools[:limit]]

        return list(similar[:limit])


class Tool(models.Model):
    CATEGORY_CHOICES = [
        ("Development", "Development"),
        ("Design", "Design"),
        ("Framework", "Framework"),
        ("Database", "Database"),
        ("DevOps", "DevOps"),
        ("Testing", "Testing"),
        ("Security", "Security"),
        ("Productivity", "Productivity"),
        ("API", "API"),
        ("Cloud", "Cloud"),
        ("Mobile", "Mobile"),
        ("AI/ML", "AI/ML"),
        ("Analytics", "Analytics"),
        ("Other", "Other"),
    ]

    title = models.CharField(max_length=200, help_text="Name of the tool or resource")
    slug = models.SlugField(
        max_length=255,
        unique=True,
        blank=True,
        help_text="URL-friendly version of title",
    )
    description = models.TextField(
        help_text="Detailed description of what this tool does"
    )
    url = models.URLField(help_text="Official URL or link to the tool")
    category = models.CharField(
        max_length=100,
        choices=CATEGORY_CHOICES,
        help_text="Category this tool belongs to",
    )
    tags = models.JSONField(
        blank=True, null=True, help_text="List of tags for this tool (as JSON array)"
    )
    is_favorite = models.BooleanField(
        default=False, help_text="Mark as favorite tool (will appear on home page)"
    )
    is_visible = models.BooleanField(
        default=True, help_text="Whether this tool is visible on the site"
    )
    icon_url = models.URLField(
        blank=True, null=True, help_text="URL to an icon/logo for this tool"
    )
    image = models.ImageField(
        upload_to="tools/",
        blank=True,
        null=True,
        help_text="Upload an image/screenshot for this tool",
        validators=[image_validator],
    )
    pricing = models.CharField(
        max_length=50,
        blank=True,
        help_text="Pricing info (e.g., 'Free', '$10/month', 'Freemium')",
    )
    rating = models.PositiveSmallIntegerField(
        blank=True, null=True, help_text="Personal rating from 1-5 stars"
    )
    last_updated = models.DateField(
        blank=True, null=True, help_text="When this tool info was last updated"
    )
    view_count = models.PositiveIntegerField(
        default=0, help_text="Number of times this tool has been viewed"
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ToolManager()

    class Meta:
        ordering = ["category", "title"]
        verbose_name = "Tool"
        verbose_name_plural = "Tools"
        indexes = [
            models.Index(fields=["category", "title"]),
            models.Index(fields=["is_favorite", "-created_at"]),
            models.Index(fields=["is_visible", "category"]),
        ]

    def clean(self):  # noqa: C901
        # Validate URL
        validator = URLValidator()
        try:
            validator(self.url)
        except ValidationError:
            raise ValidationError({"url": "Please enter a valid URL"})

        # Validate icon URL if provided
        if self.icon_url:
            try:
                validator(self.icon_url)
            except ValidationError:
                raise ValidationError({"icon_url": "Please enter a valid icon URL"})

        # Validate rating range
        if self.rating is not None and (self.rating < 1 or self.rating > 5):
            raise ValidationError({"rating": "Rating must be between 1 and 5"})

        # Validate tags format
        if self.tags:
            if not isinstance(self.tags, list):
                raise ValidationError({"tags": "Tags must be a list of strings"})

            for tag in self.tags:
                if not isinstance(tag, str) or not tag.strip():
                    raise ValidationError(
                        {"tags": "Each tag must be a non-empty string"}
                    )

    def save(self, *args, **kwargs):
        # Generate slug from title if not provided
        if not self.slug:
            from django.utils.text import slugify

            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            # Ensure uniqueness
            while Tool.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug

        # Clean tags list
        if self.tags:
            # Remove empty tags and strip whitespace
            self.tags = [tag.strip().lower() for tag in self.tags if tag.strip()]

        # Update last_updated when saving
        if not self.last_updated:
            self.last_updated = timezone.now().date()

        self.full_clean()
        super().save(*args, **kwargs)

    @cached_property
    def rating_stars(self):
        """Get star rating as string (cached property)

        Returns:
            str: Visual star representation or "No rating"

        Note:
            Cached to avoid repeated string concatenation
        """
        if not self.rating:
            return "No rating"
        return "⭐" * self.rating + "☆" * (5 - self.rating)

    @cached_property
    def is_free(self):
        """Check if the tool is free (cached property)

        Returns:
            bool or None: True if free, False if paid, None if pricing unknown

        Note:
            Cached to avoid repeated string processing
        """
        if not self.pricing:
            return None
        return self.pricing.lower() in ["free", "open source", "freemium"]

    def increment_view_count(self):
        """Increment view count atomically using F() expression"""
        from django.db.models import F

        Tool.objects.filter(pk=self.pk).update(view_count=F("view_count") + 1)

    def get_similar_tools(self, limit=3):
        """Get similar tools based on category and tags (delegates to manager)"""
        return Tool.objects.get_similar_tools(self, limit=limit)

    def __str__(self):
        category_indicator = f"[{self.category}]"
        favorite_indicator = " ⭐" if self.is_favorite else ""
        visible_indicator = "" if self.is_visible else " 🔒"

        return (
            f"{self.title} {category_indicator}{favorite_indicator}{visible_indicator}"
        )
