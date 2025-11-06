"""
Input Validation & Sanitization Tests
=====================================

Tests for comprehensive input validation framework.
"""

from django.test import TestCase

import pytest

from apps.core.validation.input_sanitizer import (
    InputSanitizer,
    InputValidator,
    ValidationPipeline,
)


class TestInputSanitizer(TestCase):
    """Test input sanitization methods"""

    def test_sanitize_text_removes_html_tags(self):
        """Test that HTML tags are stripped"""
        dirty_text = "<script>alert('xss')</script>Hello"
        clean_text = InputSanitizer.sanitize_text(dirty_text)

        assert "<script>" not in clean_text
        assert "Hello" in clean_text

    def test_sanitize_text_escapes_special_chars(self):
        """Test that special characters are escaped"""
        text = "Hello <world> & 'test'"
        clean_text = InputSanitizer.sanitize_text(text)

        assert "&lt;" in clean_text or "<" not in clean_text
        assert "&gt;" in clean_text or ">" not in clean_text

    def test_sanitize_text_enforces_max_length(self):
        """Test max length enforcement"""
        long_text = "a" * 1000
        clean_text = InputSanitizer.sanitize_text(long_text, max_length=100)

        assert len(clean_text) <= 100

    def test_sanitize_text_removes_null_bytes(self):
        """Test null byte removal"""
        text_with_null = "Hello\x00World"
        clean_text = InputSanitizer.sanitize_text(text_with_null)

        assert "\x00" not in clean_text

    def test_sanitize_html_removes_dangerous_tags(self):
        """Test dangerous HTML tag removal"""
        html = "<p>Safe</p><script>alert('xss')</script><p>More safe</p>"
        clean_html = InputSanitizer.sanitize_html(html)

        assert "<script>" not in clean_html
        assert "<p>" in clean_html

    def test_sanitize_html_removes_dangerous_attributes(self):
        """Test dangerous attribute removal"""
        html = '<a href="#" onclick="alert(\'xss\')">Link</a>'
        clean_html = InputSanitizer.sanitize_html(html)

        assert "onclick" not in clean_html

    def test_sanitize_html_removes_javascript_protocol(self):
        """Test javascript: protocol removal"""
        html = "<a href=\"javascript:alert('xss')\">Link</a>"
        clean_html = InputSanitizer.sanitize_html(html)

        assert "javascript:" not in clean_html

    def test_sanitize_url_validates_protocol(self):
        """Test URL protocol validation"""
        valid_url = "https://example.com"
        invalid_url = "javascript:alert('xss')"

        assert InputSanitizer.sanitize_url(valid_url) is not None
        assert InputSanitizer.sanitize_url(invalid_url) is None

    def test_sanitize_url_rejects_data_protocol(self):
        """Test data: protocol rejection"""
        data_url = "data:text/html,<script>alert('xss')</script>"

        assert InputSanitizer.sanitize_url(data_url) is None

    def test_sanitize_url_validates_format(self):
        """Test URL format validation"""
        valid_url = "https://example.com/path?query=value"
        invalid_url = "not a url"

        assert InputSanitizer.sanitize_url(valid_url) == valid_url
        assert InputSanitizer.sanitize_url(invalid_url) is None

    def test_sanitize_email_validates_format(self):
        """Test email validation"""
        valid_email = "user@example.com"
        invalid_email = "not-an-email"

        assert InputSanitizer.sanitize_email(valid_email) == valid_email.lower()
        assert InputSanitizer.sanitize_email(invalid_email) is None

    def test_sanitize_email_normalizes_case(self):
        """Test email case normalization"""
        email = "User@EXAMPLE.COM"
        sanitized = InputSanitizer.sanitize_email(email)

        assert sanitized == "user@example.com"

    def test_sanitize_filename_prevents_path_traversal(self):
        """Test path traversal prevention"""
        malicious_filename = "../../etc/passwd"
        safe_filename = InputSanitizer.sanitize_filename(malicious_filename)

        assert ".." not in safe_filename
        assert "/" not in safe_filename
        assert "\\" not in safe_filename

    def test_sanitize_filename_removes_dangerous_chars(self):
        """Test dangerous character removal"""
        filename = "file<name>:test.txt"
        safe_filename = InputSanitizer.sanitize_filename(filename)

        assert "<" not in safe_filename
        assert ">" not in safe_filename
        assert ":" not in safe_filename

    def test_sanitize_filename_limits_length(self):
        """Test filename length limiting"""
        long_filename = "a" * 300 + ".txt"
        safe_filename = InputSanitizer.sanitize_filename(long_filename)

        assert len(safe_filename) <= 255

    def test_sanitize_integer_validates_range(self):
        """Test integer range validation"""
        value = InputSanitizer.sanitize_integer(150, min_value=0, max_value=100)

        assert value == 100  # Clamped to max

    def test_sanitize_integer_handles_invalid_input(self):
        """Test invalid integer input handling"""
        value = InputSanitizer.sanitize_integer("not a number")

        assert value is None

    def test_sanitize_float_validates_range(self):
        """Test float range validation"""
        value = InputSanitizer.sanitize_float(150.5, min_value=0.0, max_value=100.0)

        assert value == 100.0  # Clamped to max


class TestInputValidator(TestCase):
    """Test input validation methods"""

    def test_validate_required_fields_success(self):
        """Test required fields validation - success case"""
        data = {"name": "John", "email": "john@example.com"}
        required = ["name", "email"]

        is_valid, error = InputValidator.validate_required_fields(data, required)

        assert is_valid is True
        assert error is None

    def test_validate_required_fields_missing(self):
        """Test required fields validation - missing field"""
        data = {"name": "John"}
        required = ["name", "email"]

        is_valid, error = InputValidator.validate_required_fields(data, required)

        assert is_valid is False
        assert "email" in error

    def test_validate_field_type_success(self):
        """Test field type validation - success case"""
        data = {"age": 25}

        is_valid, error = InputValidator.validate_field_type(data, "age", int)

        assert is_valid is True
        assert error is None

    def test_validate_field_type_failure(self):
        """Test field type validation - wrong type"""
        data = {"age": "twenty-five"}

        is_valid, error = InputValidator.validate_field_type(data, "age", int)

        assert is_valid is False
        assert "type" in error.lower()

    def test_validate_string_length_success(self):
        """Test string length validation - success case"""
        data = {"name": "John Doe"}

        is_valid, error = InputValidator.validate_string_length(
            data, "name", min_length=2, max_length=50
        )

        assert is_valid is True
        assert error is None

    def test_validate_string_length_too_short(self):
        """Test string length validation - too short"""
        data = {"name": "J"}

        is_valid, error = InputValidator.validate_string_length(
            data, "name", min_length=2
        )

        assert is_valid is False
        assert "at least" in error

    def test_validate_string_length_too_long(self):
        """Test string length validation - too long"""
        data = {"name": "a" * 100}

        is_valid, error = InputValidator.validate_string_length(
            data, "name", max_length=50
        )

        assert is_valid is False
        assert "at most" in error

    def test_validate_number_range_success(self):
        """Test number range validation - success case"""
        data = {"age": 25}

        is_valid, error = InputValidator.validate_number_range(
            data, "age", min_value=0, max_value=120
        )

        assert is_valid is True
        assert error is None

    def test_validate_number_range_too_low(self):
        """Test number range validation - below minimum"""
        data = {"age": -5}

        is_valid, error = InputValidator.validate_number_range(data, "age", min_value=0)

        assert is_valid is False
        assert "at least" in error

    def test_validate_number_range_too_high(self):
        """Test number range validation - above maximum"""
        data = {"age": 150}

        is_valid, error = InputValidator.validate_number_range(
            data, "age", max_value=120
        )

        assert is_valid is False
        assert "at most" in error

    def test_validate_choice_success(self):
        """Test choice validation - success case"""
        data = {"status": "active"}
        allowed = ["active", "inactive", "pending"]

        is_valid, error = InputValidator.validate_choice(data, "status", allowed)

        assert is_valid is True
        assert error is None

    def test_validate_choice_invalid(self):
        """Test choice validation - invalid choice"""
        data = {"status": "unknown"}
        allowed = ["active", "inactive", "pending"]

        is_valid, error = InputValidator.validate_choice(data, "status", allowed)

        assert is_valid is False
        assert "must be one of" in error

    def test_validate_pattern_success(self):
        """Test pattern validation - success case"""
        data = {"phone": "123-456-7890"}
        pattern = r"^\d{3}-\d{3}-\d{4}$"

        is_valid, error = InputValidator.validate_pattern(
            data, "phone", pattern, "phone format"
        )

        assert is_valid is True
        assert error is None

    def test_validate_pattern_failure(self):
        """Test pattern validation - invalid pattern"""
        data = {"phone": "invalid"}
        pattern = r"^\d{3}-\d{3}-\d{4}$"

        is_valid, error = InputValidator.validate_pattern(
            data, "phone", pattern, "phone format"
        )

        assert is_valid is False
        assert "does not match" in error


class TestValidationPipeline(TestCase):
    """Test validation pipeline"""

    def test_pipeline_all_validators_pass(self):
        """Test pipeline with all validators passing"""
        data = {"name": "John Doe", "age": 25, "email": "john@example.com"}

        pipeline = ValidationPipeline()
        pipeline.add_validator(
            lambda d: InputValidator.validate_required_fields(d, ["name", "age"])
        )
        pipeline.add_validator(
            lambda d: InputValidator.validate_field_type(d, "age", int)
        )
        pipeline.add_validator(
            lambda d: InputValidator.validate_number_range(d, "age", min_value=0)
        )

        is_valid, errors = pipeline.validate(data)

        assert is_valid is True
        assert len(errors) == 0

    def test_pipeline_some_validators_fail(self):
        """Test pipeline with some validators failing"""
        data = {"name": "John Doe", "age": -5}

        pipeline = ValidationPipeline()
        pipeline.add_validator(
            lambda d: InputValidator.validate_required_fields(d, ["name", "age"])
        )
        pipeline.add_validator(
            lambda d: InputValidator.validate_field_type(d, "age", int)
        )
        pipeline.add_validator(
            lambda d: InputValidator.validate_number_range(d, "age", min_value=0)
        )

        is_valid, errors = pipeline.validate(data)

        assert is_valid is False
        assert len(errors) > 0
        assert any("at least" in error for error in errors)

    def test_pipeline_chaining(self):
        """Test pipeline method chaining"""
        data = {"name": "John", "age": 25}

        pipeline = (
            ValidationPipeline()
            .add_validator(
                lambda d: InputValidator.validate_required_fields(d, ["name"])
            )
            .add_validator(lambda d: InputValidator.validate_field_type(d, "age", int))
        )

        is_valid, errors = pipeline.validate(data)

        assert is_valid is True


class TestXSSProtection(TestCase):
    """Test XSS protection"""

    def test_xss_script_tag_removed(self):
        """Test script tag removal"""
        xss_input = "<script>alert('XSS')</script>Hello"
        sanitized = InputSanitizer.sanitize_text(xss_input)

        assert "<script>" not in sanitized
        assert "alert" not in sanitized or "script" not in sanitized

    def test_xss_img_onerror_removed(self):
        """Test img onerror handler removal"""
        xss_html = "<img src=x onerror=\"alert('XSS')\">"
        sanitized = InputSanitizer.sanitize_html(xss_html)

        assert "onerror" not in sanitized

    def test_xss_javascript_protocol_blocked(self):
        """Test javascript: protocol blocking"""
        xss_url = "javascript:alert('XSS')"
        sanitized = InputSanitizer.sanitize_url(xss_url)

        assert sanitized is None

    def test_xss_data_protocol_blocked(self):
        """Test data: protocol blocking"""
        xss_url = "data:text/html,<script>alert('XSS')</script>"
        sanitized = InputSanitizer.sanitize_url(xss_url)

        assert sanitized is None
