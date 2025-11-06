"""
File Upload Security Utilities
==============================

Comprehensive file upload validation and sanitization.
Protects against:
- Malicious file uploads
- Path traversal attacks
- File type confusion
- Executable uploads
"""

import mimetypes
import os
from typing import List, Optional, Tuple

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile

import magic


class FileUploadValidator:
    """
    Secure file upload validator.

    Validates:
    - File extensions
    - MIME types (using magic numbers, not just extension)
    - File size
    - Filename safety
    """

    # Allowed file extensions by category
    ALLOWED_EXTENSIONS = {
        "image": [".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"],
        "document": [".pdf", ".doc", ".docx", ".txt", ".md", ".odt"],
        "archive": [".zip", ".tar", ".gz", ".bz2"],
        "code": [".py", ".js", ".html", ".css", ".json", ".xml"],
    }

    # Allowed MIME types by category
    ALLOWED_MIMETYPES = {
        "image": [
            "image/jpeg",
            "image/png",
            "image/gif",
            "image/webp",
            "image/svg+xml",
        ],
        "document": [
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "text/plain",
            "text/markdown",
        ],
        "archive": [
            "application/zip",
            "application/x-tar",
            "application/gzip",
        ],
        "code": [
            "text/x-python",
            "text/javascript",
            "text/html",
            "text/css",
            "application/json",
            "application/xml",
        ],
    }

    # Dangerous extensions that should never be allowed
    DANGEROUS_EXTENSIONS = [
        ".exe",
        ".bat",
        ".cmd",
        ".com",
        ".pif",
        ".scr",
        ".vbs",
        ".js",
        ".jar",
        ".msi",
        ".dll",
        ".so",
        ".sh",
        ".bash",
        ".ps1",
        ".app",
        ".deb",
        ".rpm",
    ]

    # Maximum file sizes by category (in bytes)
    MAX_FILE_SIZES = {
        "image": 10 * 1024 * 1024,  # 10MB
        "document": 25 * 1024 * 1024,  # 25MB
        "archive": 50 * 1024 * 1024,  # 50MB
        "code": 1 * 1024 * 1024,  # 1MB
    }

    @classmethod
    def validate_file(
        cls,
        uploaded_file: UploadedFile,
        allowed_category: str = "image",
        custom_max_size: Optional[int] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Comprehensive file validation.

        Args:
            uploaded_file: Django UploadedFile object
            allowed_category: Category of allowed files
            custom_max_size: Custom maximum file size (optional)

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Validate filename
        is_valid, error = cls.validate_filename(uploaded_file.name)
        if not is_valid:
            return (False, error)

        # Validate file extension
        is_valid, error = cls.validate_extension(uploaded_file.name, allowed_category)
        if not is_valid:
            return (False, error)

        # Validate file size
        max_size = custom_max_size or cls.MAX_FILE_SIZES.get(
            allowed_category, 10 * 1024 * 1024
        )
        is_valid, error = cls.validate_file_size(uploaded_file, max_size)
        if not is_valid:
            return (False, error)

        # Validate MIME type (magic numbers)
        is_valid, error = cls.validate_mime_type(uploaded_file, allowed_category)
        if not is_valid:
            return (False, error)

        return (True, None)

    @classmethod
    def validate_filename(cls, filename: str) -> Tuple[bool, Optional[str]]:
        """
        Validate filename for security issues.

        Complexity reduced from 9 to 7 through helper extraction.

        Args:
            filename: Filename to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not filename:
            return (False, "Filename is required")

        # Check for path traversal attempts
        is_safe, error = cls._check_path_traversal(filename)
        if not is_safe:
            return (False, error)

        # Check for null bytes
        if "\x00" in filename:
            return (False, "Invalid filename: null byte detected")

        # Check for dangerous characters
        is_safe, error = cls._check_dangerous_chars(filename)
        if not is_safe:
            return (False, error)

        # Check filename length
        if len(filename) > 255:
            return (False, "Filename too long (max 255 characters)")

        return (True, None)

    @staticmethod
    def _check_path_traversal(filename: str) -> Tuple[bool, Optional[str]]:
        """
        Check for path traversal patterns.

        Complexity: 2

        Args:
            filename: Filename to check

        Returns:
            Tuple of (is_safe, error_message)
        """
        if ".." in filename or "/" in filename or "\\" in filename:
            return (False, "Invalid filename: path traversal detected")
        return (True, None)

    @staticmethod
    def _check_dangerous_chars(filename: str) -> Tuple[bool, Optional[str]]:
        """
        Check for dangerous characters in filename.

        Complexity: 2

        Args:
            filename: Filename to check

        Returns:
            Tuple of (is_safe, error_message)
        """
        dangerous_chars = ["<", ">", ":", '"', "|", "?", "*"]
        if any(char in filename for char in dangerous_chars):
            return (False, "Invalid filename: contains dangerous characters")
        return (True, None)

    @classmethod
    def validate_extension(
        cls, filename: str, allowed_category: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate file extension.

        Args:
            filename: Filename to validate
            allowed_category: Category of allowed files

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Get file extension
        _, ext = os.path.splitext(filename.lower())

        if not ext:
            return (False, "File must have an extension")

        # Check against dangerous extensions
        if ext in cls.DANGEROUS_EXTENSIONS:
            return (False, f"File type not allowed: {ext}")

        # Check against allowed extensions for category
        allowed_exts = cls.ALLOWED_EXTENSIONS.get(allowed_category, [])
        if ext not in allowed_exts:
            return (
                False,
                f"File extension {ext} not allowed. Allowed: {', '.join(allowed_exts)}",
            )

        return (True, None)

    @staticmethod
    def validate_file_size(
        uploaded_file: UploadedFile, max_size: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate file size.

        Args:
            uploaded_file: Django UploadedFile object
            max_size: Maximum allowed size in bytes

        Returns:
            Tuple of (is_valid, error_message)
        """
        if uploaded_file.size > max_size:
            max_mb = max_size / (1024 * 1024)
            return (False, f"File too large. Maximum size: {max_mb:.1f}MB")

        if uploaded_file.size == 0:
            return (False, "File is empty")

        return (True, None)

    @classmethod
    def validate_mime_type(
        cls, uploaded_file: UploadedFile, allowed_category: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate MIME type using magic numbers (not just extension).

        Args:
            uploaded_file: Django UploadedFile object
            allowed_category: Category of allowed files

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Read first chunk for magic number detection
            uploaded_file.seek(0)
            chunk = uploaded_file.read(2048)
            uploaded_file.seek(0)

            # Detect MIME type using python-magic
            detected_mime = magic.from_buffer(chunk, mime=True)

            # Check against allowed MIME types
            allowed_mimes = cls.ALLOWED_MIMETYPES.get(allowed_category, [])
            if detected_mime not in allowed_mimes:
                return (
                    False,
                    f"File type not allowed: {detected_mime}. Allowed: {', '.join(allowed_mimes)}",
                )

            # Verify MIME type matches extension
            guessed_mime = mimetypes.guess_type(uploaded_file.name)[0]
            if guessed_mime and guessed_mime != detected_mime:
                return (False, "File extension does not match file content")

            return (True, None)

        except Exception as e:
            return (False, f"Error validating file type: {str(e)}")

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename for safe storage.

        Args:
            filename: Original filename

        Returns:
            Sanitized filename
        """
        # Remove path separators
        filename = os.path.basename(filename)

        # Remove null bytes
        filename = filename.replace("\x00", "")

        # Replace spaces with underscores
        filename = filename.replace(" ", "_")

        # Remove dangerous characters
        import re

        filename = re.sub(r'[<>:"|?*]', "", filename)

        # Limit length
        name, ext = os.path.splitext(filename)
        if len(name) > 200:
            name = name[:200]
        filename = name + ext

        return filename or "unnamed"


class ImageUploadValidator(FileUploadValidator):
    """
    Specialized validator for image uploads.

    Additional checks:
    - Image dimensions
    - Image format verification
    """

    @staticmethod
    def validate_image_dimensions(
        uploaded_file: UploadedFile,
        max_width: int = 4000,
        max_height: int = 4000,
        min_width: int = 1,
        min_height: int = 1,
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate image dimensions.

        Args:
            uploaded_file: Django UploadedFile object
            max_width: Maximum image width
            max_height: Maximum image height
            min_width: Minimum image width
            min_height: Minimum image height

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            from PIL import Image

            uploaded_file.seek(0)
            image = Image.open(uploaded_file)
            width, height = image.size
            uploaded_file.seek(0)

            if width > max_width or height > max_height:
                return (False, f"Image too large. Maximum: {max_width}x{max_height}px")

            if width < min_width or height < min_height:
                return (False, f"Image too small. Minimum: {min_width}x{min_height}px")

            return (True, None)

        except Exception as e:
            return (False, f"Invalid image file: {str(e)}")

    @staticmethod
    def validate_image_format(
        uploaded_file: UploadedFile,
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate image format using PIL.

        Args:
            uploaded_file: Django UploadedFile object

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            from PIL import Image

            uploaded_file.seek(0)
            image = Image.open(uploaded_file)
            image.verify()  # Verify it's a valid image
            uploaded_file.seek(0)

            return (True, None)

        except Exception as e:
            return (False, f"Invalid or corrupted image: {str(e)}")
