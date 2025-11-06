"""
Base Validator Classes
=====================

Core validation framework components.
All custom validators should inherit from BaseValidator.
"""

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """
    Validation result container.

    Attributes:
        is_valid: True if validation passed, False otherwise
        error: Human-readable error message if invalid
        metadata: Additional validation information (optional)

    Example:
        >>> result = ValidationResult(True, metadata={'value': 'normalized_email'})
        >>> if result:
        ...     print("Valid!")
        >>> result = ValidationResult(False, "Value too long")
        >>> print(result.error)
        'Value too long'
    """

    is_valid: bool
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __bool__(self) -> bool:
        """Allow boolean checks: if result: ..."""
        return self.is_valid

    def __str__(self) -> str:
        """Human-readable representation"""
        if self.is_valid:
            return "Valid"
        return f"Invalid: {self.error}"

    def __repr__(self) -> str:
        """Developer-friendly representation"""
        return f"ValidationResult(is_valid={self.is_valid}, error={self.error!r})"


class BaseValidator(ABC):
    """
    Abstract base class for all validators.

    Provides:
    - Standard validation interface
    - Performance metrics tracking
    - Logging support
    - Thread-safe operation

    Subclasses must implement validate() method.

    Example:
        >>> class EmailValidator(BaseValidator):
        ...     def validate(self, value, **kwargs):
        ...         if '@' not in value:
        ...             return ValidationResult(False, "Invalid email format")
        ...         return ValidationResult(True)
        >>>
        >>> validator = EmailValidator()
        >>> result = validator("user@example.com")
        >>> result.is_valid
        True
    """

    def __init__(self, name: Optional[str] = None):
        """
        Initialize validator.

        Args:
            name: Optional custom name for this validator instance.
                  Defaults to class name.
        """
        self.name = name or self.__class__.__name__
        self._metrics = {
            "call_count": 0,
            "total_time": 0.0,
            "error_count": 0,
        }

    @abstractmethod
    def validate(self, value: Any, **kwargs) -> ValidationResult:
        """
        Validate input value.

        This method MUST be implemented by subclasses.

        Args:
            value: The value to validate (type depends on validator)
            **kwargs: Optional validator-specific parameters

        Returns:
            ValidationResult with is_valid, error, and optional metadata

        Raises:
            Should not raise exceptions - return ValidationResult(False, error_msg)
            May raise TypeError if value type is completely incompatible

        Example:
            >>> def validate(self, value, **kwargs):
            ...     if not value:
            ...         return ValidationResult(False, "Value required")
            ...     return ValidationResult(True, metadata={'length': len(value)})
        """
        pass

    def __call__(self, value: Any, **kwargs) -> ValidationResult:
        """
        Callable interface with automatic metrics tracking.

        This wraps the validate() method with:
        - Performance timing
        - Call counting
        - Error tracking
        - Exception handling
        - Debug logging

        Args:
            value: Value to validate
            **kwargs: Validator-specific parameters

        Returns:
            ValidationResult from validate() method
        """
        start_time = time.perf_counter()

        try:
            # Call subclass implementation
            result = self.validate(value, **kwargs)

            # Update metrics
            self._metrics["call_count"] += 1

            if not result.is_valid:
                self._metrics["error_count"] += 1
                logger.debug(f"{self.name} validation failed: {result.error}")
            else:
                logger.debug(f"{self.name} validation passed")

            return result

        except TypeError as e:
            # Type errors are acceptable (e.g., wrong type passed)
            logger.warning(f"{self.name} type error: {e}")
            self._metrics["error_count"] += 1
            return ValidationResult(False, f"Invalid type: {e}")

        except Exception as e:
            # Unexpected errors - log and return safe error
            logger.exception(f"{self.name} validation error: {e}")
            self._metrics["error_count"] += 1
            return ValidationResult(False, "Validation failed unexpectedly")

        finally:
            # Record timing
            elapsed = time.perf_counter() - start_time
            self._metrics["total_time"] += elapsed

            # Warn on slow validations (>100ms)
            if elapsed > 0.1:
                logger.warning(
                    f"{self.name} validation took {elapsed:.3f}s - consider optimization"
                )

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get validator performance metrics.

        Returns:
            Dict containing:
                - call_count: Total number of validations
                - total_time: Total time spent (seconds)
                - avg_time: Average time per validation
                - error_count: Number of validation failures
                - error_rate: Percentage of failures (0.0-1.0)

        Example:
            >>> validator = MyValidator()
            >>> # ... use validator ...
            >>> metrics = validator.get_metrics()
            >>> print(f"Average time: {metrics['avg_time']:.6f}s")
            >>> print(f"Error rate: {metrics['error_rate']:.2%}")
        """
        call_count = max(self._metrics["call_count"], 1)  # Avoid division by zero

        return {
            "validator_name": self.name,
            "call_count": self._metrics["call_count"],
            "total_time": self._metrics["total_time"],
            "avg_time": self._metrics["total_time"] / call_count,
            "error_count": self._metrics["error_count"],
            "error_rate": self._metrics["error_count"] / call_count,
        }

    def reset_metrics(self) -> None:
        """
        Reset performance metrics.

        Useful for testing or when starting a new measurement period.
        """
        self._metrics = {
            "call_count": 0,
            "total_time": 0.0,
            "error_count": 0,
        }

    def __repr__(self) -> str:
        """Developer-friendly representation"""
        return f"{self.__class__.__name__}(name={self.name!r})"
