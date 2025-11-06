"""
SQL Injection Protection Tests
===============================

Tests for SQL injection protection utilities.
"""

from django.test import TestCase

import pytest

from apps.core.validation.sql_protection import (
    DatabaseQueryValidator,
    SafeRawQueryBuilder,
    SQLInjectionProtection,
)


class TestSQLInjectionProtection(TestCase):
    """Test SQL injection detection"""

    def test_is_suspicious_clean_input(self):
        """Test clean input passes"""
        clean_inputs = [
            "john_doe",
            "user@example.com",
            "Normal search term",
            "Product 123",
        ]

        for input_str in clean_inputs:
            is_suspicious, reason = SQLInjectionProtection.is_suspicious_input(
                input_str
            )
            assert is_suspicious is False

    def test_is_suspicious_sql_keywords(self):
        """Test SQL keyword detection"""
        sql_keywords = [
            "DROP TABLE users",
            "DELETE FROM accounts",
            "UNION SELECT password",
            "EXEC sp_dropdatabase",
        ]

        for sql_input in sql_keywords:
            is_suspicious, reason = SQLInjectionProtection.is_suspicious_input(
                sql_input
            )
            assert is_suspicious is True
            assert reason is not None

    def test_is_suspicious_sql_comments(self):
        """Test SQL comment detection"""
        comment_inputs = [
            "admin' --",
            "user /* comment */ OR 1=1",
            "test #comment",
        ]

        for comment_input in comment_inputs:
            is_suspicious, reason = SQLInjectionProtection.is_suspicious_input(
                comment_input
            )
            assert is_suspicious is True

    def test_is_suspicious_injection_patterns(self):
        """Test injection pattern detection"""
        injection_patterns = [
            "' OR '1'='1",
            "admin'; DROP TABLE users--",
            "1' AND '1'='1",
            "' OR 1=1--",
        ]

        for pattern in injection_patterns:
            is_suspicious, reason = SQLInjectionProtection.is_suspicious_input(pattern)
            assert is_suspicious is True

    def test_sanitize_search_term_removes_wildcards(self):
        """Test wildcard removal"""
        search_term = "test%search_term"
        sanitized = SQLInjectionProtection.sanitize_search_term(search_term)

        assert "%" not in sanitized
        assert "_" not in sanitized

    def test_sanitize_search_term_removes_null_bytes(self):
        """Test null byte removal"""
        search_term = "test\x00term"
        sanitized = SQLInjectionProtection.sanitize_search_term(search_term)

        assert "\x00" not in sanitized

    def test_sanitize_search_term_enforces_length(self):
        """Test length enforcement"""
        long_term = "a" * 1000
        sanitized = SQLInjectionProtection.sanitize_search_term(long_term)

        assert len(sanitized) <= 500

    def test_build_safe_filter_dict_allowed_fields(self):
        """Test filter dict with allowed fields"""
        user_input = {"status": "active", "category": "electronics"}
        allowed_fields = ["status", "category"]

        safe_dict, warnings = SQLInjectionProtection.build_safe_filter_dict(
            user_input, allowed_fields
        )

        assert safe_dict == user_input
        assert len(warnings) == 0

    def test_build_safe_filter_dict_disallowed_fields(self):
        """Test filter dict with disallowed fields"""
        user_input = {"status": "active", "password": "hack"}
        allowed_fields = ["status", "category"]

        safe_dict, warnings = SQLInjectionProtection.build_safe_filter_dict(
            user_input, allowed_fields
        )

        assert "password" not in safe_dict
        assert len(warnings) > 0

    def test_validate_order_by_field_allowed(self):
        """Test ORDER BY validation with allowed field"""
        field = "created_at"
        allowed_fields = ["created_at", "updated_at", "title"]

        is_valid, error = SQLInjectionProtection.validate_order_by_field(
            field, allowed_fields
        )

        assert is_valid is True
        assert error is None

    def test_validate_order_by_field_disallowed(self):
        """Test ORDER BY validation with disallowed field"""
        field = "password"
        allowed_fields = ["created_at", "updated_at", "title"]

        is_valid, error = SQLInjectionProtection.validate_order_by_field(
            field, allowed_fields
        )

        assert is_valid is False
        assert error is not None

    def test_validate_order_by_field_descending(self):
        """Test ORDER BY validation with DESC suffix"""
        field = "-created_at"
        allowed_fields = ["created_at", "updated_at"]

        is_valid, error = SQLInjectionProtection.validate_order_by_field(
            field, allowed_fields
        )

        assert is_valid is True


class TestSafeRawQueryBuilder(TestCase):
    """Test safe raw query building"""

    def test_escape_identifier_safe(self):
        """Test safe identifier escaping"""
        safe_identifiers = ["users", "user_profiles", "product_123"]

        for identifier in safe_identifiers:
            escaped = SafeRawQueryBuilder.escape_identifier(identifier)
            assert escaped is not None

    def test_escape_identifier_dangerous(self):
        """Test dangerous identifier rejection"""
        dangerous_identifiers = [
            "users; DROP TABLE",
            "users--",
            "users/*comment*/",
        ]

        for identifier in dangerous_identifiers:
            escaped = SafeRawQueryBuilder.escape_identifier(identifier)
            assert escaped is None

    def test_build_parameterized_query_valid(self):
        """Test valid parameterized query"""
        query = "SELECT * FROM users WHERE id = %s AND status = %s"
        params = (1, "active")

        is_valid, error = SafeRawQueryBuilder.build_parameterized_query(query, params)

        assert is_valid is True
        assert error is None

    def test_build_parameterized_query_mismatch(self):
        """Test parameter count mismatch"""
        query = "SELECT * FROM users WHERE id = %s AND status = %s"
        params = (1,)  # Only 1 param, but query needs 2

        is_valid, error = SafeRawQueryBuilder.build_parameterized_query(query, params)

        assert is_valid is False
        assert "mismatch" in error.lower()


class TestDatabaseQueryValidator(TestCase):
    """Test database query validation"""

    def test_validate_limit_offset_valid(self):
        """Test valid LIMIT and OFFSET"""
        limit = 50
        offset = 100

        validated_limit, validated_offset, error = (
            DatabaseQueryValidator.validate_limit_offset(limit, offset)
        )

        assert validated_limit == limit
        assert validated_offset == offset
        assert error is None

    def test_validate_limit_offset_limit_too_high(self):
        """Test LIMIT exceeds maximum"""
        limit = 5000  # Exceeds 1000 max
        offset = 0

        validated_limit, validated_offset, error = (
            DatabaseQueryValidator.validate_limit_offset(limit, offset)
        )

        assert validated_limit == 1000  # Clamped to max
        assert error is not None

    def test_validate_limit_offset_negative_offset(self):
        """Test negative OFFSET"""
        limit = 50
        offset = -10

        validated_limit, validated_offset, error = (
            DatabaseQueryValidator.validate_limit_offset(limit, offset)
        )

        assert validated_offset == 0  # Reset to 0
        assert error is not None

    def test_validate_id_list_valid(self):
        """Test valid ID list"""
        id_list = [1, 2, 3, 4, 5]

        is_valid, error = DatabaseQueryValidator.validate_id_list(id_list)

        assert is_valid is True
        assert error is None

    def test_validate_id_list_too_many(self):
        """Test ID list exceeds maximum"""
        id_list = list(range(150))  # 150 items (exceeds 100 max)

        is_valid, error = DatabaseQueryValidator.validate_id_list(id_list)

        assert is_valid is False
        assert "too many" in error.lower()

    def test_validate_id_list_non_integer(self):
        """Test ID list with non-integer values"""
        id_list = [1, 2, "three", 4]

        is_valid, error = DatabaseQueryValidator.validate_id_list(id_list)

        assert is_valid is False
        assert "integer" in error.lower()

    def test_validate_id_list_negative_id(self):
        """Test ID list with negative values"""
        id_list = [1, 2, -3, 4]

        is_valid, error = DatabaseQueryValidator.validate_id_list(id_list)

        assert is_valid is False


class TestSQLInjectionScenarios(TestCase):
    """Test real-world SQL injection scenarios"""

    def test_scenario_login_bypass(self):
        """Test login bypass attempt"""
        username = "admin' OR '1'='1"

        is_suspicious, reason = SQLInjectionProtection.is_suspicious_input(username)

        assert is_suspicious is True

    def test_scenario_comment_injection(self):
        """Test comment injection attempt"""
        username = "admin'--"

        is_suspicious, reason = SQLInjectionProtection.is_suspicious_input(username)

        assert is_suspicious is True

    def test_scenario_union_attack(self):
        """Test UNION-based attack"""
        search = "product' UNION SELECT username, password FROM users--"

        is_suspicious, reason = SQLInjectionProtection.is_suspicious_input(search)

        assert is_suspicious is True

    def test_scenario_time_based_blind(self):
        """Test time-based blind SQL injection"""
        input_value = "1'; WAITFOR DELAY '00:00:05'--"

        is_suspicious, reason = SQLInjectionProtection.is_suspicious_input(input_value)

        assert is_suspicious is True

    def test_scenario_second_order(self):
        """Test second-order injection pattern"""
        # While this is harder to detect, we should catch obvious patterns
        stored_value = "admin'; DROP TABLE users--"

        is_suspicious, reason = SQLInjectionProtection.is_suspicious_input(stored_value)

        assert is_suspicious is True
