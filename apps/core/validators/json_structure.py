"""
JSON Structure Validator
=======================

Validates JSON structure against required keys.
Migrated to validation framework with reduced complexity.
"""

from typing import Any, List, Optional

from apps.core.validators.base import BaseValidator, ValidationResult
from apps.core.validators.registry import ValidatorRegistry


@ValidatorRegistry.register("json_structure")
class JSONStructureValidator(BaseValidator):
    """
    Validate JSON structure against required keys.

    Features:
    - Validates dict structure
    - Checks for required keys
    - Provides detailed error messages

    Complexity reduced from 6 to 3.

    Args:
        required_keys: List of required keys (optional, can be set per call)

    Example:
        >>> validator = JSONStructureValidator(required_keys=["name", "email"])
        >>> result = validator({"name": "John", "email": "john@example.com"})
        >>> result.is_valid
        True
        >>>
        >>> result = validator({"name": "John"})
        >>> result.is_valid
        False
        >>> result.error
        'Missing required key: email'
    """

    def __init__(self, required_keys: Optional[List[str]] = None):
        """
        Initialize JSON structure validator.

        Args:
            required_keys: List of required keys
        """
        super().__init__()
        self.required_keys = required_keys or []

    def validate(self, data: Any, **kwargs) -> ValidationResult:
        """
        Validate JSON structure.

        Complexity: 3

        Args:
            data: Data to validate (should be dict)
            **kwargs: Optional overrides:
                - required_keys: Override instance required_keys

        Returns:
            ValidationResult
        """
        # Check if dict
        if not isinstance(data, dict):
            return ValidationResult(False, "Data must be a dictionary")

        # Get required keys
        required_keys = kwargs.get("required_keys", self.required_keys)

        # Check for missing keys
        missing_result = self._check_missing_keys(data, required_keys)
        if not missing_result.is_valid:
            return missing_result

        # Success
        return ValidationResult(
            True, metadata={"key_count": len(data), "keys": list(data.keys())}
        )

    @staticmethod
    def _check_missing_keys(data: dict, required_keys: List[str]) -> ValidationResult:
        """
        Check for missing required keys.

        Complexity: 2

        Args:
            data: Dictionary to check
            required_keys: List of required keys

        Returns:
            ValidationResult
        """
        if not required_keys:
            return ValidationResult(True)

        missing_keys = [key for key in required_keys if key not in data]
        if missing_keys:
            return ValidationResult(False, f"Missing required key: {missing_keys[0]}")

        return ValidationResult(True)
