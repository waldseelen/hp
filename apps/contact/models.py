import re

from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator, MinLengthValidator
from django.db import models
from django.utils import timezone
from django.utils.html import strip_tags


class ContactMessage(models.Model):
    """Contact message model with comprehensive validation"""

    CHANNEL_CHOICES = [
        ("email", "Email"),
        ("calendly", "Plan a call"),
        ("slack", "Slack / Teams invite"),
    ]

    name = models.CharField(
        max_length=100,
        validators=[MinLengthValidator(2)],
        help_text="Full name (2-100 characters)",
    )
    email = models.EmailField(
        validators=[EmailValidator()], help_text="Valid email address"
    )
    subject = models.CharField(
        max_length=200,
        validators=[MinLengthValidator(3)],
        help_text="Message subject (3-200 characters)",
    )
    message = models.TextField(
        validators=[MinLengthValidator(10)],
        help_text="Message content (10-2000 characters)",
    )
    preferred_channel = models.CharField(
        max_length=20,
        choices=CHANNEL_CHOICES,
        default="email",
        help_text="Preferred response channel",
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Contact Message"
        verbose_name_plural = "Contact Messages"
        indexes = [
            models.Index(fields=["is_read", "-created_at"]),
            models.Index(fields=["-created_at"]),
            models.Index(fields=["email", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.name} - {self.subject}"

    def clean(self):
        """Model-level validation"""
        super().clean()

        # Validate name
        if self.name:
            name = strip_tags(self.name).strip()
            if len(name) < 2:
                raise ValidationError(
                    {"name": "Name must be at least 2 characters long."}
                )

            # Check for valid characters
            if not re.match(r"^[a-zA-Z\s\-'\.]+$", name):
                raise ValidationError(
                    {
                        "name": "Name contains invalid characters. Only letters, spaces, hyphens, apostrophes, and dots are allowed."
                    }
                )

        # Validate message length
        if self.message:
            message = strip_tags(self.message).strip()
            if len(message) > 2000:
                raise ValidationError(
                    {"message": "Message must be under 2000 characters."}
                )
            if len(message) < 10:
                raise ValidationError(
                    {"message": "Message must be at least 10 characters long."}
                )

        # Validate subject
        if self.subject:
            subject = strip_tags(self.subject).strip()
            if len(subject) < 3:
                raise ValidationError(
                    {"subject": "Subject must be at least 3 characters long."}
                )

    def save(self, *args, **kwargs):
        """Override save to ensure validation"""
        self.full_clean()
        super().save(*args, **kwargs)
