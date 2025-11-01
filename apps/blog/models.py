import re

from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

from apps.main.models import Admin


class PostManager(models.Manager):
    def published(self):
        """Get all published posts"""
        return self.filter(status="published", published_at__lte=timezone.now())

    def by_tag(self, tag):
        """Get posts by tag"""
        return self.filter(tags__icontains=tag)


class Post(models.Model):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("published", "Published"),
        ("unlisted", "Unlisted"),
        ("scheduled", "Scheduled"),
    ]

    title = models.CharField(max_length=200, help_text="The title of the blog post")
    slug = models.SlugField(
        max_length=250,
        unique=True,
        blank=True,
        help_text="URL-friendly version of the title (auto-generated if left blank)",
    )
    excerpt = models.TextField(
        blank=True,
        null=True,
        max_length=500,
        help_text="Brief description/summary of the post (max 500 characters)",
    )
    content = models.TextField(
        blank=True,
        null=True,
        help_text="Main content of the blog post (supports Markdown)",
    )
    featured_image_url = models.URLField(
        blank=True, null=True, help_text="URL to a featured image for this post"
    )
    featured_image = models.ImageField(
        upload_to="blog/images/",
        blank=True,
        null=True,
        help_text="Upload a featured image for this post",
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="draft",
        help_text="Publication status of the post",
    )
    tags = models.JSONField(
        blank=True, null=True, help_text="List of tags for this post (as JSON array)"
    )
    meta_description = models.CharField(
        max_length=160,
        blank=True,
        help_text="SEO meta description (max 160 characters)",
    )
    published_at = models.DateTimeField(
        blank=True, null=True, help_text="When this post was/will be published"
    )
    author = models.ForeignKey(
        Admin,
        on_delete=models.CASCADE,
        related_name="posts",
        help_text="Author of this post",
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    # View tracking
    view_count = models.PositiveIntegerField(default=0)

    objects = PostManager()

    class Meta:
        ordering = ["-published_at", "-created_at"]
        verbose_name = "Blog Post"
        verbose_name_plural = "Blog Posts"
        indexes = [
            models.Index(fields=["status", "-published_at"]),
            models.Index(fields=["author", "-published_at"]),
            models.Index(fields=["slug"]),
        ]

    def clean(self):
        # Validate content is not empty for published posts
        if self.status in ["published", "scheduled"] and not self.content:
            raise ValidationError(
                {"content": "Content is required for published posts"}
            )

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
        # Auto-generate slug from title
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Post.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug

        # Auto-set published_at when status changes to published
        if self.status == "published" and not self.published_at:
            self.published_at = timezone.now()

        # Clean tags list
        if self.tags:
            # Remove empty tags and strip whitespace
            self.tags = [tag.strip() for tag in self.tags if tag.strip()]

        # Auto-generate meta description from excerpt or content
        if not self.meta_description:
            if self.excerpt:
                self.meta_description = self.excerpt[:160]
            elif self.content:
                # Strip HTML/Markdown and get first 160 chars
                clean_content = re.sub(r"[#*`\[\]()]+", "", self.content)
                self.meta_description = clean_content[:160]

        # Run full validation
        self.full_clean()

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("blog:detail", kwargs={"slug": self.slug})

    def get_reading_time(self):
        """Estimate reading time in minutes"""
        if not self.content:
            return 0
        word_count = len(self.content.split())
        # Average reading speed: 200 words per minute
        return max(1, round(word_count / 200))

    def get_related_posts(self, limit=3):
        """Get related posts based on tags"""
        if not self.tags:
            return Post.objects.published().exclude(pk=self.pk)[:limit]

        related = Post.objects.published().exclude(pk=self.pk)

        # Score posts by tag matches
        scored_posts = []
        for post in related:
            if post.tags:
                common_tags = set(self.tags) & set(post.tags)
                if common_tags:
                    scored_posts.append((len(common_tags), post))

        # Sort by score (number of common tags) and return top results
        scored_posts.sort(key=lambda x: x[0], reverse=True)
        return [post for _, post in scored_posts[:limit]]

    def increment_view_count(self):
        """Increment the view count for this post"""
        Post.objects.filter(pk=self.pk).update(view_count=models.F("view_count") + 1)

    @property
    def is_published(self):
        return (
            self.status == "published"
            and self.published_at
            and self.published_at <= timezone.now()
        )

    @property
    def word_count(self):
        """Get word count of the content"""
        if not self.content:
            return 0
        return len(self.content.split())

    def __str__(self):
        status_indicator = ""
        if self.status == "published":
            status_indicator = " ✓"
        elif self.status == "draft":
            status_indicator = " 📝"
        elif self.status == "scheduled":
            status_indicator = " ⏰"

        return f"{self.title}{status_indicator}"
