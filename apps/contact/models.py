from django.db import models
from django.utils import timezone


class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Contact Message"
        verbose_name_plural = "Contact Messages"
        indexes = [
            models.Index(fields=['is_read', '-created_at']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['email', '-created_at']),
        ]

    def __str__(self):
        return f"{self.name} - {self.subject}"
