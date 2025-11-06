"""
Validator Registry
=================

Central registry for all validators in the application.
Allows validators to be registered and retrieved by name.
"""

import logging
from typing import Dict, Optional, Type

from .base import BaseValidator

logger = logging.getLogger(__name__)


class ValidatorRegistry:
    """
    Central registry for validator classes.

    Provides decorator-based registration and retrieval of validators.
    Thread-safe singleton pattern.

    Example:
        >>> @ValidatorRegistry.register('email')
        ... class EmailValidator(BaseValidator):
        ...     def validate(self, value, **kwargs):
        ...         return ValidationResult('@' in value)
        >>>
        >>> # Later, retrieve validator
        >>> EmailValidatorClass = ValidatorRegistry.get('email')
        >>> validator = EmailValidatorClass()
        >>> result = validator("user@example.com")
    """

    _validators: Dict[str, Type[BaseValidator]] = {}
    _instances: Dict[str, BaseValidator] = {}

    @classmethod
    def register(cls, name: str):
        """
        Decorator to register a validator class.

        Args:
            name: Unique identifier for this validator

        Returns:
            Decorator function

        Raises:
            ValueError: If name is already registered
            TypeError: If decorated class is not a BaseValidator subclass

        Example:
            >>> @ValidatorRegistry.register('my_validator')
            ... class MyValidator(BaseValidator):
            ...     def validate(self, value, **kwargs):
            ...         return ValidationResult(True)
        """

        def decorator(validator_class: Type[BaseValidator]):
            # Validate it's a BaseValidator subclass
            if not issubclass(validator_class, BaseValidator):
                raise TypeError(
                    f"{validator_class.__name__} must inherit from BaseValidator"
                )

            # Check for duplicate registration
            if name in cls._validators:
                logger.warning(
                    f"Validator '{name}' is already registered. "
                    f"Overwriting {cls._validators[name].__name__} with {validator_class.__name__}"
                )

            # Register the class
            cls._validators[name] = validator_class
            logger.debug(f"Registered validator: {name} -> {validator_class.__name__}")

            return validator_class

        return decorator

    @classmethod
    def get(cls, name: str) -> Optional[Type[BaseValidator]]:
        """
        Get validator class by name.

        Args:
            name: Validator identifier

        Returns:
            Validator class, or None if not found

        Example:
            >>> ValidatorClass = ValidatorRegistry.get('email')
            >>> if ValidatorClass:
            ...     validator = ValidatorClass()
            ...     result = validator("test@example.com")
        """
        return cls._validators.get(name)

    @classmethod
    def get_instance(cls, name: str, **kwargs) -> Optional[BaseValidator]:
        """
        Get or create singleton validator instance.

        Useful for validators without state that can be reused.

        Args:
            name: Validator identifier
            **kwargs: Arguments to pass to validator constructor (first time only)

        Returns:
            Validator instance, or None if not found

        Example:
            >>> validator = ValidatorRegistry.get_instance('email')
            >>> result = validator("test@example.com")
        """
        # Check if instance already exists
        if name in cls._instances:
            return cls._instances[name]

        # Get class and create instance
        validator_class = cls._validators.get(name)
        if validator_class is None:
            return None

        try:
            instance = validator_class(**kwargs)
            cls._instances[name] = instance
            logger.debug(f"Created singleton instance for validator: {name}")
            return instance
        except Exception as e:
            logger.error(f"Failed to create validator instance '{name}': {e}")
            return None

    @classmethod
    def list_validators(cls) -> list[str]:
        """
        List all registered validator names.

        Returns:
            List of validator names

        Example:
            >>> validators = ValidatorRegistry.list_validators()
            >>> print("Available validators:", validators)
            ['email', 'phone', 'url', 'tags']
        """
        return sorted(cls._validators.keys())

    @classmethod
    def clear(cls) -> None:
        """
        Clear all registered validators.

        Primarily for testing purposes.
        """
        cls._validators.clear()
        cls._instances.clear()
        logger.info("Cleared validator registry")

    @classmethod
    def get_all_metrics(cls) -> Dict[str, Dict]:
        """
        Get metrics for all singleton validator instances.

        Returns:
            Dict mapping validator names to their metrics

        Example:
            >>> metrics = ValidatorRegistry.get_all_metrics()
            >>> for name, data in metrics.items():
            ...     print(f"{name}: {data['call_count']} calls, {data['error_rate']:.2%} errors")
        """
        return {
            name: validator.get_metrics() for name, validator in cls._instances.items()
        }
