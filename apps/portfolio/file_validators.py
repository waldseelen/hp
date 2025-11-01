"""
File upload security validators
"""

import hashlib
import os

from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible

try:
    import magic

    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False

try:
    from PIL import Image

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


@deconstructible
class FileTypeValidator:
    """
    Validates file type by checking both extension and MIME type
    """

    def __init__(self, allowed_types=None, max_size=5 * 1024 * 1024):  # 5MB default
        self.allowed_types = allowed_types or {
            "image/jpeg": [".jpg", ".jpeg"],
            "image/png": [".png"],
            "image/gif": [".gif"],
            "image/webp": [".webp"],
            "application/pdf": [".pdf"],
        }
        self.max_size = max_size

    def __call__(self, file):
        # Check file size
        if file.size > self.max_size:
            raise ValidationError(
                f"File size {file.size} bytes exceeds maximum allowed size of {self.max_size} bytes."
            )

        # Get file extension
        file_extension = os.path.splitext(file.name)[1].lower()

        # Read file content to check MIME type
        file.seek(0)
        file_content = file.read(2048)  # Read first 2KB for MIME detection
        file.seek(0)  # Reset file pointer

        # Check MIME type using python-magic if available
        mime_type = None
        if MAGIC_AVAILABLE:
            try:
                mime_type = magic.from_buffer(file_content, mime=True)
            except Exception:
                pass

        # Validate against allowed types
        allowed_extensions = []
        for allowed_mime, extensions in self.allowed_types.items():
            allowed_extensions.extend(extensions)

            # If we have MIME type, check it
            if mime_type and mime_type == allowed_mime and file_extension in extensions:
                return  # Valid file

        # If no MIME type available, just check extension
        if not mime_type and file_extension in allowed_extensions:
            return  # Valid file (fallback)

        raise ValidationError(
            f'Invalid file type. Allowed types: {", ".join(allowed_extensions)}. '
            f'Detected type: {mime_type or "unknown"}'
        )


@deconstructible
class ImageValidator(FileTypeValidator):
    """
    Enhanced validator specifically for images
    """

    def __init__(
        self,
        max_size=5 * 1024 * 1024,
        max_width=4000,
        max_height=4000,
        min_width=50,
        min_height=50,
    ):
        super().__init__(
            allowed_types={
                "image/jpeg": [".jpg", ".jpeg"],
                "image/png": [".png"],
                "image/gif": [".gif"],
                "image/webp": [".webp"],
            },
            max_size=max_size,
        )
        self.max_width = max_width
        self.max_height = max_height
        self.min_width = min_width
        self.min_height = min_height

    def __call__(self, file):
        # First, run basic file validation
        super().__call__(file)

        try:
            # Reset file pointer and check if it's a valid image
            file.seek(0)

            # Use PIL to validate and get image dimensions if available
            if not PIL_AVAILABLE:
                return  # Skip additional validation if PIL not available

            with Image.open(file) as img:
                width, height = img.size

                # Check dimensions
                if width < self.min_width or height < self.min_height:
                    raise ValidationError(
                        f"Image dimensions {width}x{height} are too small. "
                        f"Minimum size: {self.min_width}x{self.min_height}px"
                    )

                if width > self.max_width or height > self.max_height:
                    raise ValidationError(
                        f"Image dimensions {width}x{height} are too large. "
                        f"Maximum size: {self.max_width}x{self.max_height}px"
                    )

                # Check for potentially malicious images
                if hasattr(img, "verify"):
                    try:
                        img.verify()
                    except Exception:
                        raise ValidationError(
                            "Image file appears to be corrupted or malicious."
                        )

        except (IOError, OSError) as e:
            raise ValidationError(f"Invalid image file: {str(e)}")

        finally:
            file.seek(0)  # Reset file pointer


@deconstructible
class SecureFileValidator:
    """
    Comprehensive file security validator
    """

    DANGEROUS_EXTENSIONS = {
        ".exe",
        ".bat",
        ".cmd",
        ".com",
        ".pif",
        ".scr",
        ".vbs",
        ".js",
        ".jar",
        ".php",
        ".php3",
        ".php4",
        ".php5",
        ".phtml",
        ".asp",
        ".aspx",
        ".jsp",
        ".sh",
        ".py",
        ".pl",
        ".rb",
        ".cgi",
        ".htaccess",
        ".htpasswd",
    }

    EXECUTABLE_SIGNATURES = {
        b"MZ",  # Windows executable
        b"\x7fELF",  # Linux executable
        b"\xcf\xfa\xed\xfe",  # macOS executable
        b"\xca\xfe\xba\xbe",  # Java class file
        b"#!/",  # Script files
    }

    def __init__(self, allowed_types=None, max_size=10 * 1024 * 1024):
        self.allowed_types = allowed_types or {
            "image/jpeg": [".jpg", ".jpeg"],
            "image/png": [".png"],
            "image/gif": [".gif"],
            "image/webp": [".webp"],
            "application/pdf": [".pdf"],
        }
        self.max_size = max_size

    def __call__(self, file):
        # Check file name for suspicious patterns
        filename = file.name.lower()
        file_extension = os.path.splitext(filename)[1]

        # Check for dangerous extensions
        if file_extension in self.DANGEROUS_EXTENSIONS:
            raise ValidationError(
                f'File type "{file_extension}" is not allowed for security reasons.'
            )

        # Check for double extensions (e.g., file.jpg.exe)
        name_parts = filename.split(".")
        if len(name_parts) > 2:
            for part in name_parts[1:-1]:  # Check middle parts
                if f".{part}" in self.DANGEROUS_EXTENSIONS:
                    raise ValidationError(
                        "File with multiple extensions is not allowed."
                    )

        # Check file content for executable signatures
        file.seek(0)
        file_header = file.read(16)  # Read first 16 bytes
        file.seek(0)

        for signature in self.EXECUTABLE_SIGNATURES:
            if file_header.startswith(signature):
                raise ValidationError(
                    "File contains executable code and is not allowed."
                )

        # Check file size
        if file.size > self.max_size:
            raise ValidationError(
                f"File size {file.size} bytes exceeds maximum allowed size of {self.max_size} bytes."
            )

        # Check file name length and characters
        if len(filename) > 255:
            raise ValidationError(
                "Filename is too long. Maximum 255 characters allowed."
            )

        # Check for null bytes and control characters
        if "\x00" in filename or any(
            ord(c) < 32 for c in filename if c not in "\t\n\r"
        ):
            raise ValidationError("Filename contains invalid characters.")

        # Run basic type validation
        FileTypeValidator(self.allowed_types, self.max_size)(file)


def scan_uploaded_file(file_path):
    """
    Additional security scan for uploaded files
    """
    try:
        # Calculate file hash for integrity checking
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)

        file_hash = hasher.hexdigest()

        # Log file upload for audit trail
        import logging

        logger = logging.getLogger(__name__)
        logger.info(
            f"File uploaded: {os.path.basename(file_path)}, SHA256: {file_hash}"
        )

        return file_hash

    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Error scanning uploaded file {file_path}: {e}")
        return None


# Common validator instances
image_validator = ImageValidator(max_size=5 * 1024 * 1024)  # 5MB for images
secure_file_validator = SecureFileValidator(
    max_size=10 * 1024 * 1024
)  # 10MB for general files
small_image_validator = ImageValidator(
    max_size=2 * 1024 * 1024, max_width=2000, max_height=2000
)  # 2MB for smaller images
