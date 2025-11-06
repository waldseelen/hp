"""
SQL Injection Protection Utilities
==================================

Django ORM already provides excellent SQL injection protection through
parameterized queries. This module provides additional utilities and
best practices for secure database operations.

OWASP A03: Injection protection
"""

import re
from typing import Any, Dict, List, Optional


class SQLInjectionProtection:
    """
    Additional SQL injection protection utilities.

    Note: Django ORM provides built-in protection. These utilities
    are for additional validation and safe raw SQL handling.
    """

    # Suspicious SQL keywords that might indicate injection attempts
    SUSPICIOUS_SQL_KEYWORDS = [
        "DROP",
        "DELETE",
        "TRUNCATE",
        "ALTER",
        "CREATE",
        "EXEC",
        "EXECUTE",
        "UNION",
        "INSERT",
        "UPDATE",
        "--",
        "/*",
        "*/",
        "xp_",
        "sp_",
        "SLEEP",
        "BENCHMARK",
    ]

    # SQL comment patterns
    SQL_COMMENT_PATTERNS = [
        r"--",
        r"/\*",
        r"\*/",
        r"#",
    ]

    @classmethod
    def is_suspicious_input(cls, input_string: str) -> bool:
        """
        Check if input contains suspicious SQL patterns.

        Complexity reduced from 8 to 4 through helper extraction.

        This is a defense-in-depth measure. Django ORM parameterization
        is the primary defense.

        Args:
            input_string: User input to check

        Returns:
            True if suspicious patterns detected
        """
        if not isinstance(input_string, str):
            return False

        # Check all pattern types
        if cls._check_sql_keywords(input_string):
            return True

        if cls._check_comment_patterns(input_string):
            return True

        if cls._check_injection_patterns(input_string):
            return True

        return False

    @classmethod
    def _check_sql_keywords(cls, input_string: str) -> bool:
        """
        Check for suspicious SQL keywords.

        Complexity: 2

        Args:
            input_string: Input to check

        Returns:
            True if keywords found
        """
        upper_input = input_string.upper()
        for keyword in cls.SUSPICIOUS_SQL_KEYWORDS:
            if keyword in upper_input:
                return True
        return False

    @classmethod
    def _check_comment_patterns(cls, input_string: str) -> bool:
        """
        Check for SQL comment patterns.

        Complexity: 2

        Args:
            input_string: Input to check

        Returns:
            True if comment patterns found
        """
        for pattern in cls.SQL_COMMENT_PATTERNS:
            if re.search(pattern, input_string):
                return True
        return False

    @staticmethod
    def _check_injection_patterns(input_string: str) -> bool:
        """
        Check for common SQL injection patterns.

        Complexity: 2

        Args:
            input_string: Input to check

        Returns:
            True if injection patterns found
        """
        injection_patterns = [
            r"'\s*OR\s+'1'\s*=\s*'1",  # ' OR '1'='1
            r"'\s*OR\s+1\s*=\s*1",  # ' OR 1=1
            r"'\s*;",  # '; followed by anything
            r"'\s*--",  # ' -- (SQL comment)
        ]

        for pattern in injection_patterns:
            if re.search(pattern, input_string, re.IGNORECASE):
                return True

        return False

    @staticmethod
    def sanitize_search_term(search_term: str) -> str:
        """
        Sanitize search term for safe database queries.

        Django ORM handles parameterization, but this provides
        additional cleaning for search terms.

        Args:
            search_term: User-provided search term

        Returns:
            Sanitized search term
        """
        if not isinstance(search_term, str):
            return ""

        # Remove null bytes
        search_term = search_term.replace("\x00", "")

        # Remove SQL wildcards that might be misused
        # (Let application explicitly add wildcards if needed)
        search_term = search_term.replace("%", "")
        search_term = search_term.replace("_", "")

        # Trim whitespace
        search_term = search_term.strip()

        # Limit length
        if len(search_term) > 200:
            search_term = search_term[:200]

        return search_term

    @staticmethod
    def build_safe_filter_dict(
        allowed_fields: List[str], user_filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build safe filter dictionary for ORM queries.

        Only allows filtering on whitelisted fields.

        Args:
            allowed_fields: List of field names allowed for filtering
            user_filters: User-provided filter dictionary

        Returns:
            Sanitized filter dictionary
        """
        safe_filters = {}

        for field, value in user_filters.items():
            # Strip ORM lookup suffixes for validation
            base_field = field.split("__")[0]

            if base_field in allowed_fields:
                safe_filters[field] = value

        return safe_filters

    @staticmethod
    def validate_order_by_field(field: str, allowed_fields: List[str]) -> Optional[str]:
        """
        Validate ORDER BY field for safe sorting.

        Args:
            field: Field name for sorting (may include '-' prefix)
            allowed_fields: List of allowed field names

        Returns:
            Validated field name or None if invalid
        """
        # Handle descending sort prefix
        if field.startswith("-"):
            base_field = field[1:]
            prefix = "-"
        else:
            base_field = field
            prefix = ""

        # Validate against whitelist
        if base_field not in allowed_fields:
            return None

        return prefix + base_field


class SafeRawQueryBuilder:
    """
    Utilities for safely building raw SQL queries (when absolutely necessary).

    Prefer Django ORM whenever possible!
    """

    @staticmethod
    def escape_identifier(identifier: str) -> str:
        """
        Escape SQL identifier (table/column name).

        Args:
            identifier: Table or column name

        Returns:
            Escaped identifier
        """
        # Remove any characters that aren't alphanumeric or underscore
        clean_identifier = re.sub(r"[^a-zA-Z0-9_]", "", identifier)

        # Ensure it doesn't start with a number
        if clean_identifier and clean_identifier[0].isdigit():
            clean_identifier = "_" + clean_identifier

        return clean_identifier

    @staticmethod
    def build_parameterized_query(base_query: str, params: List[Any]) -> tuple:
        """
        Helper to ensure parameterized queries are used correctly.

        Args:
            base_query: SQL query with placeholders (%s)
            params: Parameter values

        Returns:
            Tuple of (query, params) for use with cursor.execute()
        """
        # Count placeholders
        placeholder_count = base_query.count("%s")

        if placeholder_count != len(params):
            raise ValueError(
                f"Placeholder count ({placeholder_count}) does not match "
                f"parameter count ({len(params)})"
            )

        return (base_query, params)


class DatabaseQueryValidator:
    """
    Validate database query parameters before execution.
    """

    @staticmethod
    def validate_limit_offset(
        limit: Optional[int] = None, offset: Optional[int] = None, max_limit: int = 1000
    ) -> tuple:
        """
        Validate and sanitize LIMIT and OFFSET values.

        Complexity reduced from 8 to 3 through helper extraction.

        Args:
            limit: LIMIT value
            offset: OFFSET value
            max_limit: Maximum allowed limit

        Returns:
            Tuple of (validated_limit, validated_offset)
        """
        validated_limit = DatabaseQueryValidator._coerce_to_int(
            limit, default=max_limit, min_val=0, max_val=max_limit
        )
        validated_offset = DatabaseQueryValidator._coerce_to_int(
            offset, default=0, min_val=0, max_val=None
        )
        return (validated_limit, validated_offset)

    @staticmethod
    def _coerce_to_int(
        value: Optional[int], default: int, min_val: int, max_val: Optional[int]
    ) -> int:
        """
        Coerce value to integer with bounds checking.

        Complexity: 4

        Args:
            value: Value to coerce
            default: Default if value is None or invalid
            min_val: Minimum allowed value
            max_val: Maximum allowed value (None = no limit)

        Returns:
            Validated integer
        """
        if value is None:
            return default

        try:
            value = int(value)
        except (ValueError, TypeError):
            return default

        if value < min_val:
            return default

        if max_val is not None and value > max_val:
            return max_val

        return value

    @staticmethod
    def validate_id_list(id_list: List[Any], max_items: int = 100) -> List[int]:
        """
        Validate list of IDs for IN queries.

        Args:
            id_list: List of ID values
            max_items: Maximum number of items allowed

        Returns:
            List of validated integer IDs
        """
        if not isinstance(id_list, list):
            return []

        # Limit number of items (prevent DoS)
        if len(id_list) > max_items:
            id_list = id_list[:max_items]

        # Convert to integers, skip invalid values
        validated_ids = []
        for id_value in id_list:
            try:
                validated_ids.append(int(id_value))
            except (ValueError, TypeError):
                continue

        return validated_ids


# Best practices documentation
DJANGO_ORM_BEST_PRACTICES = """
Django ORM SQL Injection Protection Best Practices:

✅ SAFE - Use ORM methods (ALWAYS PREFER):
    User.objects.filter(username=user_input)
    User.objects.get(id=pk)
    User.objects.filter(email__icontains=search_term)

✅ SAFE - Parameterized raw queries:
    cursor.execute("SELECT * FROM users WHERE id = %s", [user_id])

❌ DANGEROUS - String formatting:
    cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
    cursor.execute("SELECT * FROM users WHERE id = " + str(user_id))

❌ DANGEROUS - String interpolation:
    cursor.execute("SELECT * FROM users WHERE id = %s" % user_id)

✅ SAFE - F() expressions for field references:
    from django.db.models import F
    Product.objects.filter(price__gt=F('cost') * 1.2)

✅ SAFE - Q() objects for complex queries:
    from django.db.models import Q
    User.objects.filter(Q(first_name='John') | Q(last_name='Doe'))

⚠️  USE WITH CAUTION - extra():
    # Only use when absolutely necessary, always parameterize
    User.objects.extra(where=["age > %s"], params=[18])

✅ SAFE - Annotation and aggregation:
    from django.db.models import Count, Avg
    User.objects.annotate(post_count=Count('posts'))

REMEMBER: Django ORM's parameterized queries are your primary defense!
"""
