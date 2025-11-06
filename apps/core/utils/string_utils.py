"""String manipulation and processing utilities

This module provides centralized string functions used across the application.
"""

import re
import unicodedata
from typing import Optional

from django.utils.text import slugify as django_slugify

__all__ = [
    "slugify",
    "strip_whitespace",
    "normalize_unicode",
    "remove_accents",
    "camel_to_snake",
    "snake_to_camel",
    "truncate_words",
    "extract_numbers",
    "capitalize_words",
]


def slugify(text: str, allow_unicode: bool = False) -> str:
    """Convert text to URL-friendly slug

    Args:
        text: Text to convert
        allow_unicode: Whether to allow Unicode characters (default: False)

    Returns:
        str: URL-friendly slug

    Examples:
        >>> slugify("Hello World!")
        'hello-world'
        >>> slugify("Türkçe Başlık")
        'turkce-baslik'
    """
    if not text:
        return ""

    return django_slugify(text, allow_unicode=allow_unicode)


def strip_whitespace(text: str, preserve_newlines: bool = False) -> str:
    """Strip excessive whitespace from text

    Args:
        text: Text to process
        preserve_newlines: Whether to preserve newline characters

    Returns:
        str: Text with normalized whitespace

    Examples:
        >>> strip_whitespace("Hello    World")
        'Hello World'
        >>> strip_whitespace("Hello\\n\\nWorld", preserve_newlines=True)
        'Hello\\nWorld'
    """
    if not text:
        return ""

    if preserve_newlines:
        # Replace multiple spaces with single space, but keep newlines
        lines = text.split("\n")
        lines = [re.sub(r" +", " ", line.strip()) for line in lines]
        # Remove empty lines
        lines = [line for line in lines if line]
        return "\n".join(lines)
    else:
        # Replace all whitespace with single space
        return re.sub(r"\s+", " ", text).strip()


def normalize_unicode(text: str) -> str:
    """Normalize Unicode text to NFC form

    Args:
        text: Text to normalize

    Returns:
        str: Normalized Unicode text

    Examples:
        >>> normalize_unicode("café")  # Normalized form
        'café'
    """
    if not text:
        return ""

    return unicodedata.normalize("NFC", text)


def remove_accents(text: str) -> str:
    """Remove accents from text (convert to ASCII)

    Args:
        text: Text with accents

    Returns:
        str: Text without accents

    Examples:
        >>> remove_accents("café")
        'cafe'
        >>> remove_accents("naïve")
        'naive'
    """
    if not text:
        return ""

    # Normalize to NFD (decomposed form)
    nfd = unicodedata.normalize("NFD", text)

    # Remove combining characters (accents)
    return "".join(char for char in nfd if unicodedata.category(char) != "Mn")


def camel_to_snake(text: str) -> str:
    """Convert camelCase to snake_case

    Args:
        text: Text in camelCase

    Returns:
        str: Text in snake_case

    Examples:
        >>> camel_to_snake("myVariableName")
        'my_variable_name'
        >>> camel_to_snake("HTTPResponse")
        'http_response'
    """
    if not text:
        return ""

    # Insert underscore before uppercase letters
    text = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", text)
    # Handle consecutive uppercase letters
    text = re.sub("([a-z0-9])([A-Z])", r"\1_\2", text)

    return text.lower()


def snake_to_camel(text: str, capitalize_first: bool = False) -> str:
    """Convert snake_case to camelCase

    Args:
        text: Text in snake_case
        capitalize_first: Whether to capitalize first letter (PascalCase)

    Returns:
        str: Text in camelCase or PascalCase

    Examples:
        >>> snake_to_camel("my_variable_name")
        'myVariableName'
        >>> snake_to_camel("my_variable_name", capitalize_first=True)
        'MyVariableName'
    """
    if not text:
        return ""

    components = text.split("_")

    if capitalize_first:
        return "".join(word.capitalize() for word in components)
    else:
        return components[0] + "".join(word.capitalize() for word in components[1:])


def truncate_words(text: str, max_words: int = 50, suffix: str = "...") -> str:
    """Truncate text to a maximum number of words

    Args:
        text: Text to truncate
        max_words: Maximum number of words
        suffix: String to append when truncated (default: "...")

    Returns:
        str: Truncated text

    Examples:
        >>> truncate_words("This is a long sentence with many words", max_words=5)
        'This is a long sentence...'
    """
    if not text:
        return ""

    words = text.split()

    if len(words) <= max_words:
        return text

    return " ".join(words[:max_words]) + suffix


def extract_numbers(text: str) -> list[int]:
    """Extract all numbers from text

    Args:
        text: Text containing numbers

    Returns:
        list: List of extracted numbers as integers

    Examples:
        >>> extract_numbers("I have 3 cats and 2 dogs")
        [3, 2]
        >>> extract_numbers("The year is 2024")
        [2024]
    """
    if not text:
        return []

    numbers = re.findall(r"\d+", text)
    return [int(num) for num in numbers]


def capitalize_words(text: str, exclude: Optional[list[str]] = None) -> str:
    """Capitalize first letter of each word (title case)

    Args:
        text: Text to capitalize
        exclude: List of words to exclude from capitalization (e.g., ["and", "or"])

    Returns:
        str: Capitalized text

    Examples:
        >>> capitalize_words("hello world")
        'Hello World'
        >>> capitalize_words("the cat and the dog", exclude=["and", "the"])
        'The Cat and the Dog'
    """
    if not text:
        return ""

    words = text.split()

    if exclude is None:
        exclude = []

    exclude_lower = [word.lower() for word in exclude]

    result = []
    for i, word in enumerate(words):
        if i == 0 or word.lower() not in exclude_lower:
            result.append(word.capitalize())
        else:
            result.append(word.lower())

    return " ".join(result)
