"""
Tags Validator
=============

Validates tag lists or comma-separated strings.
Reduces complexity from 11 to ≤6 through helper extraction.
"""

from typing import List, Optional, Union

from apps.core.validators.base import BaseValidator, ValidationResult
from apps.core.validators.registry import ValidatorRegistry


@ValidatorRegistry.register("tags")
class TagsValidator(BaseValidator):
    """
    Validate tag lists or comma-separated strings.

    Features:
    - Accepts both List[str] and "comma,separated,string"
    - Validates tag count (max_tags)
    - Validates individual tag length (max_length)
    - Normalizes input automatically

    Args:
        max_tags: Maximum number of tags allowed (default: 10)
        max_length: Maximum length per tag (default: 50)

    Example:
        >>> validator = TagsValidator(max_tags=5, max_length=30)
        >>> result = validator(["python", "django", "web"])
        >>> result.is_valid
        True
        >>> result.metadata['tag_count']
        3
        >>>
        >>> result = validator("python,django," + "x" * 100)
        >>> result.is_valid
        False
        >>> result.error
        'Tag exceeds maximum length of 30 characters'
    """

    def __init__(self, max_tags: int = 10, max_length: int = 50):
        """
        Initialize tags validator.

        Args:
            max_tags: Maximum number of tags allowed
            max_length: Maximum length per individual tag
        """
        super().__init__()
        self.max_tags = max_tags
        self.max_length = max_length

    def validate(self, tags: Union[List[str], str], **kwargs) -> ValidationResult:
        """
        Validate tags with ≤6 complexity.

        Args:
            tags: List of tags or comma-separated string
            **kwargs: Optional overrides:
                - max_tags: Override instance max_tags
                - max_length: Override instance max_length

        Returns:
            ValidationResult with tag_count in metadata if valid
        """
        # Allow runtime overrides
        max_tags = kwargs.get("max_tags", self.max_tags)
        max_length = kwargs.get("max_length", self.max_length)

        # Step 1: Normalize input (complexity: 3)
        tag_list = self._normalize_input(tags)
        if tag_list is None:
            return ValidationResult(
                False, "Tags must be a list or comma-separated string"
            )

        # Empty is valid
        if not tag_list:
            return ValidationResult(True, metadata={"tag_count": 0})

        # Step 2: Validate count (complexity: 2)
        count_result = self._validate_count(tag_list, max_tags)
        if not count_result.is_valid:
            return count_result

        # Step 3: Validate individual tags (complexity: 4)
        for tag in tag_list:
            tag_result = self._validate_individual_tag(tag, max_length)
            if not tag_result.is_valid:
                return tag_result

        # Success
        return ValidationResult(
            True, metadata={"tag_count": len(tag_list), "tags": tag_list}
        )

    def _normalize_input(self, tags: Union[List[str], str]) -> Optional[List[str]]:
        """
        Normalize tags input to list format.

        Complexity: 3 (if-elif-else chain)

        Args:
            tags: List or comma-separated string

        Returns:
            List of tags, or None if invalid type
        """
        if not tags:
            return []

        if isinstance(tags, str):
            return [tag.strip() for tag in tags.split(",") if tag.strip()]

        if isinstance(tags, list):
            return tags

        return None

    def _validate_count(self, tags: List[str], max_tags: int) -> ValidationResult:
        """
        Validate tag count.

        Complexity: 2 (single conditional)

        Args:
            tags: List of tags
            max_tags: Maximum allowed count

        Returns:
            ValidationResult
        """
        if len(tags) > max_tags:
            return ValidationResult(
                False, f"Maximum {max_tags} tags allowed. You provided {len(tags)}."
            )
        return ValidationResult(True)

    def _validate_individual_tag(self, tag: str, max_length: int) -> ValidationResult:
        """
        Validate single tag.

        Complexity: 4 (sequential conditionals)

        Args:
            tag: Individual tag to validate
            max_length: Maximum allowed length

        Returns:
            ValidationResult
        """
        if not isinstance(tag, str):
            return ValidationResult(False, "Each tag must be a string")

        if not tag.strip():
            return ValidationResult(False, "Empty tags are not allowed")

        if len(tag) > max_length:
            return ValidationResult(
                False,
                f"Tag exceeds maximum length of {max_length} characters. "
                f"Tag: '{tag[:20]}...' (length: {len(tag)})",
            )

        return ValidationResult(True)
