"""
File validation utilities for the main app
"""

import os

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def image_validator(file):
    """
    Validate image files
    """
    valid_extensions = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"]
    ext = os.path.splitext(file.name)[1].lower()

    if ext not in valid_extensions:
        raise ValidationError(
            _("Unsupported file extension. Allowed extensions: %(extensions)s"),
            params={"extensions": ", ".join(valid_extensions)},
        )

    # Check file size (max 5MB)
    if file.size > 5 * 1024 * 1024:
        raise ValidationError(_("File size must not exceed 5MB."))


def document_validator(file):
    """
    Validate document files
    """
    valid_extensions = [".pdf", ".doc", ".docx", ".txt", ".rtf"]
    ext = os.path.splitext(file.name)[1].lower()

    if ext not in valid_extensions:
        raise ValidationError(
            _("Unsupported file extension. Allowed extensions: %(extensions)s"),
            params={"extensions": ", ".join(valid_extensions)},
        )

    # Check file size (max 10MB)
    if file.size > 10 * 1024 * 1024:
        raise ValidationError(_("File size must not exceed 10MB."))


def video_validator(file):
    """
    Validate video files
    """
    valid_extensions = [".mp4", ".avi", ".mov", ".wmv", ".flv", ".webm"]
    ext = os.path.splitext(file.name)[1].lower()

    if ext not in valid_extensions:
        raise ValidationError(
            _("Unsupported file extension. Allowed extensions: %(extensions)s"),
            params={"extensions": ", ".join(valid_extensions)},
        )

    # Check file size (max 50MB)
    if file.size > 50 * 1024 * 1024:
        raise ValidationError(_("File size must not exceed 50MB."))
