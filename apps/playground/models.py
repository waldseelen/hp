import uuid

from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse

User = get_user_model()


class ProgrammingLanguage(models.Model):
    """Supported programming languages"""

    name = models.CharField(max_length=50, unique=True)
    icon = models.CharField(max_length=10, default="⚡")
    tagline = models.CharField(max_length=100)
    extension = models.CharField(max_length=10)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]

    def __str__(self):
        return f"{self.icon} {self.name}"


class CodeTemplate(models.Model):
    """Predefined code templates"""

    name = models.CharField(max_length=100)
    description = models.CharField(max_length=200)
    language = models.ForeignKey(ProgrammingLanguage, on_delete=models.CASCADE)
    emoji = models.CharField(max_length=10, default="📝")
    code = models.TextField()
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_featured", "name"]

    def __str__(self):
        return f"{self.emoji} {self.name} ({self.language.name})"


class CodeSnippet(models.Model):
    """User-created code snippets"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200, blank=True)
    language = models.ForeignKey(ProgrammingLanguage, on_delete=models.CASCADE)
    code = models.TextField()
    output = models.TextField(blank=True)

    # User and sharing
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    is_public = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)

    # Stats
    views = models.IntegerField(default=0)
    likes = models.IntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title or f"Code #{self.id}"

    def get_absolute_url(self):
        return reverse("playground:snippet_detail", kwargs={"pk": self.id})

    @property
    def share_url(self):
        return f"/playground/share/{self.id}/"


class CodeLike(models.Model):
    """User likes for code snippets"""

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    snippet = models.ForeignKey(CodeSnippet, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["user", "snippet"]


class ExecutionResult(models.Model):
    """Code execution results and stats"""

    snippet = models.ForeignKey(CodeSnippet, on_delete=models.CASCADE)
    output = models.TextField()
    error_output = models.TextField(blank=True)
    execution_time = models.FloatField()  # in milliseconds
    memory_usage = models.IntegerField(default=0)  # in KB
    success = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
