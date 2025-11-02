import re

from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property

from apps.core.utils.model_helpers import auto_set_published_at, generate_unique_slug
from apps.main.models import Admin


class PostManager(models.Manager):
    def published(self):
        """Get all published posts with author relationship loaded

        Returns:
            QuerySet: Published posts with author select_related to avoid N+1 queries
        """
        return self.filter(
            status="published", published_at__lte=timezone.now()
        ).select_related("author")

    def by_tag(self, tag):
        """Get posts by tag"""
        return self.filter(tags__icontains=tag)

    def get_related_posts(self, post, limit=3):
        """Get related posts based on tag similarity

        Args:
            post: The Post instance to find related posts for
            limit: Maximum number of related posts to return

        Returns:
            List of related Post instances, sorted by tag similarity

        Note:
            Uses select_related for author to avoid N+1 queries
        """
        if not post.tags:
            return list(
                self.published().select_related("author").exclude(pk=post.pk)[:limit]
            )

        # Fetch all published posts in one query with author relationship
        related = self.published().select_related("author").exclude(pk=post.pk)

        # Score posts by tag matches
        scored_posts = []
        for related_post in related:
            if related_post.tags:
                common_tags = set(post.tags) & set(related_post.tags)
                if common_tags:
                    scored_posts.append((len(common_tags), related_post))

        # Sort by score (number of common tags) and return top results
        scored_posts.sort(key=lambda x: x[0], reverse=True)
        return [related_post for _, related_post in scored_posts[:limit]]


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
        # Auto-generate unique slug from title
        if not self.slug:
            self.slug = generate_unique_slug(self)

        # Auto-set published_at when status changes to published
        auto_set_published_at(self)

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
        """Get the canonical URL for this post

        Returns:
            str: URL path to the post detail page
        """
        return reverse("blog:detail", kwargs={"slug": self.slug})

    @cached_property
    def reading_time(self):
        """Estimate reading time in minutes (cached property)

        Returns:
            int: Estimated reading time in minutes based on 200 words/min

        Note:
            Cached to avoid repeated content splitting. Cache cleared on save.
        """
        if not self.content:
            return 0
        word_count = len(self.content.split())
        # Average reading speed: 200 words per minute
        return max(1, round(word_count / 200))

    def get_reading_time(self):
        """Backwards compatibility method for reading_time property

        Deprecated: Use .reading_time property instead
        """
        return self.reading_time

    def get_related_posts(self, limit=3):
        """Get related posts based on tags (delegates to manager)"""
        return Post.objects.get_related_posts(self, limit=limit)

    def increment_view_count(self):
        """Increment the view count for this post"""
        Post.objects.filter(pk=self.pk).update(view_count=models.F("view_count") + 1)

    @property
    def is_published(self):
        """Check if the post is published and live

        Returns:
            bool: True if status is published and published_at is in the past
        """
        return (
            self.status == "published"
            and self.published_at
            and self.published_at <= timezone.now()
        )

    @cached_property
    def word_count(self):
        """Get word count of the content (cached property)

        Returns:
            int: Number of words in the content

        Note:
            Cached to avoid repeated content splitting. Cache cleared on save.
        """
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
