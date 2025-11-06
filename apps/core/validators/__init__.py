"""
Validation Framework
===================

Centralized validation framework for consistent validation across the application.

Usage:
    from apps.core.validators import BaseValidator, ValidationResult
    from apps.core.validators.registry import ValidatorRegistry

    @ValidatorRegistry.register('my_validator')
    class MyValidator(BaseValidator):
        def validate(self, value, **kwargs):
            # Your validation logic
            return ValidationResult(True)
"""

from .base import BaseValidator, ValidationResult
from .registry import ValidatorRegistry

__all__ = [
    "BaseValidator",
    "ValidationResult",
    "ValidatorRegistry",
]

__version__ = "1.0.0"
