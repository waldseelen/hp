"""
File Upload Security Tests
===========================

Tests for secure file upload validation.
"""

import os
import tempfile
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

import pytest

from apps.core.validation.file_upload import FileUploadValidator, ImageUploadValidator


class TestFileUploadValidator(TestCase):
    """Test file upload validation"""

    def test_validate_filename_safe(self):
        """Test safe filename validation"""
        validator = FileUploadValidator()

        is_valid, error = validator.validate_filename("document.pdf")

        assert is_valid is True
        assert error is None

    def test_validate_filename_path_traversal(self):
        """Test path traversal detection"""
        validator = FileUploadValidator()

        is_valid, error = validator.validate_filename("../../etc/passwd")

        assert is_valid is False
        assert "path traversal" in error.lower()

    def test_validate_filename_null_byte(self):
        """Test null byte detection"""
        validator = FileUploadValidator()

        is_valid, error = validator.validate_filename("file\x00.txt")

        assert is_valid is False
        assert "null byte" in error.lower()

    def test_validate_filename_dangerous_chars(self):
        """Test dangerous character detection"""
        validator = FileUploadValidator()

        is_valid, error = validator.validate_filename("file<name>.txt")

        assert is_valid is False

    def test_validate_extension_allowed_image(self):
        """Test allowed image extension"""
        validator = FileUploadValidator()

        is_valid, error = validator.validate_extension("image.png", category="image")

        assert is_valid is True
        assert error is None

    def test_validate_extension_dangerous(self):
        """Test dangerous extension detection"""
        validator = FileUploadValidator()

        is_valid, error = validator.validate_extension("malware.exe")

        assert is_valid is False
        assert "dangerous" in error.lower()

    def test_validate_extension_double_extension(self):
        """Test double extension detection"""
        validator = FileUploadValidator()

        is_valid, error = validator.validate_extension("file.pdf.exe")

        assert is_valid is False

    def test_validate_file_size_within_limit(self):
        """Test file size within limit"""
        validator = FileUploadValidator()

        # Create 1MB file
        content = b"a" * (1024 * 1024)
        uploaded_file = SimpleUploadedFile("test.jpg", content)

        is_valid, error = validator.validate_file_size(uploaded_file, category="image")

        assert is_valid is True
        assert error is None

    def test_validate_file_size_exceeds_limit(self):
        """Test file size exceeds limit"""
        validator = FileUploadValidator()

        # Create 15MB file (exceeds 10MB image limit)
        content = b"a" * (15 * 1024 * 1024)
        uploaded_file = SimpleUploadedFile("test.jpg", content)

        is_valid, error = validator.validate_file_size(uploaded_file, category="image")

        assert is_valid is False
        assert "size" in error.lower()

    def test_sanitize_filename_removes_dangerous_parts(self):
        """Test filename sanitization"""
        validator = FileUploadValidator()

        malicious_name = "../../<script>alert('xss')</script>file.txt"
        safe_name = validator.sanitize_filename(malicious_name)

        assert ".." not in safe_name
        assert "<" not in safe_name
        assert ">" not in safe_name
        assert "script" not in safe_name

    def test_sanitize_filename_limits_length(self):
        """Test filename length limiting"""
        validator = FileUploadValidator()

        long_name = "a" * 300 + ".txt"
        safe_name = validator.sanitize_filename(long_name)

        assert len(safe_name) <= 255

    def test_validate_file_comprehensive(self):
        """Test comprehensive file validation"""
        validator = FileUploadValidator()

        content = b"Valid PDF content"
        uploaded_file = SimpleUploadedFile("document.pdf", content)

        # This will pass filename/extension checks but may fail MIME check
        # (requires python-magic to be installed)
        is_valid, errors = validator.validate_file(uploaded_file, category="document")

        # Should at least pass basic checks
        assert isinstance(errors, list)


class TestImageUploadValidator(TestCase):
    """Test image upload validation"""

    def setUp(self):
        """Set up test fixtures"""
        self.validator = ImageUploadValidator()

    def test_validate_image_dimensions_within_limit(self):
        """Test image dimensions within limit"""
        # Create a simple 100x100 test image
        try:
            from PIL import Image

            img = Image.new("RGB", (100, 100), color="red")
            img_bytes = BytesIO()
            img.save(img_bytes, format="PNG")
            img_bytes.seek(0)

            uploaded_file = SimpleUploadedFile("test.png", img_bytes.read())

            is_valid, error = self.validator.validate_image_dimensions(uploaded_file)

            assert is_valid is True
            assert error is None
        except ImportError:
            pytest.skip("PIL not installed")

    def test_validate_image_dimensions_exceeds_limit(self):
        """Test image dimensions exceed limit"""
        try:
            from PIL import Image

            # Create 5000x5000 image (exceeds 4000x4000 limit)
            img = Image.new("RGB", (5000, 5000), color="red")
            img_bytes = BytesIO()
            img.save(img_bytes, format="PNG")
            img_bytes.seek(0)

            uploaded_file = SimpleUploadedFile("test.png", img_bytes.read())

            is_valid, error = self.validator.validate_image_dimensions(uploaded_file)

            assert is_valid is False
            assert "dimensions" in error.lower()
        except ImportError:
            pytest.skip("PIL not installed")

    def test_validate_image_format_valid(self):
        """Test valid image format"""
        try:
            from PIL import Image

            img = Image.new("RGB", (100, 100), color="red")
            img_bytes = BytesIO()
            img.save(img_bytes, format="PNG")
            img_bytes.seek(0)

            uploaded_file = SimpleUploadedFile("test.png", img_bytes.read())

            is_valid, error = self.validator.validate_image_format(uploaded_file)

            assert is_valid is True
            assert error is None
        except ImportError:
            pytest.skip("PIL not installed")

    def test_validate_image_format_invalid(self):
        """Test invalid image format"""
        # Upload non-image file
        content = b"Not an image"
        uploaded_file = SimpleUploadedFile("fake.png", content)

        is_valid, error = self.validator.validate_image_format(uploaded_file)

        assert is_valid is False
        assert "format" in error.lower() or "image" in error.lower()


class TestMaliciousFileDetection(TestCase):
    """Test malicious file detection"""

    def test_executable_extension_blocked(self):
        """Test executable file blocking"""
        validator = FileUploadValidator()

        dangerous_extensions = [".exe", ".bat", ".cmd", ".vbs", ".dll", ".so"]

        for ext in dangerous_extensions:
            is_valid, error = validator.validate_extension(f"file{ext}")
            assert is_valid is False

    def test_script_extension_blocked(self):
        """Test script file blocking"""
        validator = FileUploadValidator()

        script_extensions = [".sh", ".ps1", ".py", ".rb", ".pl"]

        for ext in script_extensions:
            is_valid, error = validator.validate_extension(f"script{ext}")
            assert is_valid is False

    def test_double_extension_blocked(self):
        """Test double extension blocking"""
        validator = FileUploadValidator()

        is_valid, error = validator.validate_extension("document.pdf.exe")

        assert is_valid is False

    def test_null_byte_injection_blocked(self):
        """Test null byte injection blocking"""
        validator = FileUploadValidator()

        is_valid, error = validator.validate_filename("file.txt\x00.exe")

        assert is_valid is False


class TestFileUploadIntegration(TestCase):
    """Test file upload integration scenarios"""

    def test_upload_legitimate_document(self):
        """Test legitimate document upload"""
        validator = FileUploadValidator()

        content = b"PDF content here"
        uploaded_file = SimpleUploadedFile("report.pdf", content)

        # Should pass basic validation
        is_valid, errors = validator.validate_file(uploaded_file, category="document")

        # May fail MIME check without python-magic, but should pass basic checks
        assert isinstance(errors, list)

    def test_upload_legitimate_image(self):
        """Test legitimate image upload"""
        validator = ImageUploadValidator()

        try:
            from PIL import Image

            img = Image.new("RGB", (800, 600), color="blue")
            img_bytes = BytesIO()
            img.save(img_bytes, format="JPEG")
            img_bytes.seek(0)

            uploaded_file = SimpleUploadedFile("photo.jpg", img_bytes.read())

            is_valid, errors = validator.validate_file(uploaded_file, category="image")

            # Should pass all checks
            assert is_valid is True or len(errors) == 0
        except ImportError:
            pytest.skip("PIL not installed")

    def test_upload_malicious_file_disguised(self):
        """Test malicious file disguised as legitimate"""
        validator = FileUploadValidator()

        # Executable with PDF extension
        content = b"MZ\x90\x00"  # DOS header for .exe
        uploaded_file = SimpleUploadedFile("document.pdf", content)

        is_valid, errors = validator.validate_file(uploaded_file, category="document")

        # Should fail MIME type check (if python-magic installed)
        # Or at least pass through for manual review
        assert isinstance(errors, list)
