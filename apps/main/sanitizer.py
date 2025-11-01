"""
HTML/Markdown Sanitization Module for Content Management

This module provides sanitization utilities for user-generated content
to prevent XSS attacks while preserving safe HTML formatting.
"""

from typing import Dict, List, Optional, Tuple

from django.utils.safestring import mark_safe

import bleach
import markdown


class ContentSanitizer:
    """
    Comprehensive content sanitization for different content types.
    Supports HTML, Markdown, and plain text with appropriate cleaning rules.
    """

    # Allowed HTML tags for rich content
    ALLOWED_TAGS = [
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "p",
        "br",
        "hr",
        "strong",
        "em",
        "u",
        "s",
        "code",
        "a",
        "img",
        "ul",
        "ol",
        "li",
        "blockquote",
        "pre",
        "table",
        "thead",
        "tbody",
        "tr",
        "th",
        "td",
        "div",
        "span",
    ]

    # Allowed HTML attributes
    ALLOWED_ATTRIBUTES: Dict[str, List[str]] = {
        "a": ["href", "title", "target", "rel"],
        "img": ["src", "alt", "title", "width", "height"],
        "table": ["border", "cellpadding", "cellspacing"],
        "th": ["align", "valign"],
        "td": ["align", "valign", "colspan", "rowspan"],
        "div": ["class", "id"],
        "span": ["class", "id"],
        "code": ["class"],
        "pre": ["class"],
    }

    # Protocol whitelist for URLs
    ALLOWED_PROTOCOLS = ["http", "https", "mailto", "ftp"]

    @classmethod
    def sanitize_html(cls, html_content: str, strip_tags: bool = False) -> str:
        """
        Sanitize HTML content to prevent XSS attacks.

        Args:
            html_content: Raw HTML content from user
            strip_tags: If True, removes all tags instead of filtering

        Returns:
            Sanitized HTML string
        """
        if not html_content:
            return ""

        if strip_tags:
            # Remove all HTML tags
            cleaned = bleach.clean(html_content, tags=[], strip=True)
        else:
            # Filter to allowed tags and attributes
            cleaned = bleach.clean(
                html_content,
                tags=cls.ALLOWED_TAGS,
                attributes=cls.ALLOWED_ATTRIBUTES,
                strip=False,
            )

        # Linkify URLs and sanitize links
        cleaned = bleach.linkify(
            cleaned, skip_tags=["code", "pre"], callbacks=[cls._safe_link_callback]
        )

        return cleaned

    @classmethod
    def sanitize_markdown(cls, markdown_content: str) -> str:
        """
        Convert Markdown to safe HTML.

        Args:
            markdown_content: Raw Markdown content

        Returns:
            Sanitized HTML from Markdown
        """
        if not markdown_content:
            return ""

        # Convert Markdown to HTML
        html_content = markdown.markdown(
            markdown_content,
            extensions=["tables", "fenced_code", "codehilite", "toc"],
            extension_configs={
                "codehilite": {"use_pygments": False, "linenums": False}
            },
        )

        # Sanitize the resulting HTML
        return cls.sanitize_html(html_content)

    @classmethod
    def sanitize_plain_text(
        cls, text_content: str, preserve_breaks: bool = True
    ) -> str:
        """
        Sanitize plain text content.

        Args:
            text_content: Plain text content
            preserve_breaks: If True, converts newlines to <br> tags

        Returns:
            Sanitized text (optionally with HTML line breaks)
        """
        if not text_content:
            return ""

        # Remove all HTML tags first
        cleaned = bleach.clean(text_content, tags=[], strip=True)

        if preserve_breaks:
            # Preserve line breaks as HTML
            cleaned = cleaned.replace("\n\n", "</p><p>")
            cleaned = cleaned.replace("\n", "<br>")
            cleaned = f"<p>{cleaned}</p>"

        return cleaned

    @classmethod
    def sanitize_by_type(cls, content: str, content_type: str) -> str:
        """
        Sanitize content based on its type.

        Args:
            content: The content to sanitize
            content_type: Type of content ('html', 'markdown', 'text')

        Returns:
            Sanitized content
        """
        content_type = content_type.lower()

        if content_type == "html":
            return cls.sanitize_html(content)
        elif content_type == "markdown":
            return cls.sanitize_markdown(content)
        elif content_type == "text":
            return cls.sanitize_plain_text(content)
        else:
            # Default to HTML sanitization
            return cls.sanitize_html(content)

    @classmethod
    def _safe_link_callback(cls, attrs, new: bool = False) -> Optional[Dict]:
        """
        Callback for linkify to ensure safe links.

        Args:
            attrs: Link attributes
            new: Whether this is a new link

        Returns:
            Filtered attributes or None to remove link
        """
        # Get the href
        href_key = (None, "href")
        href = attrs.get(href_key)

        if not href:
            return attrs

        # Ensure external links open in new tab
        if href.startswith("http"):
            attrs[(None, "target")] = "_blank"
            attrs[(None, "rel")] = "noopener noreferrer"

        # Remove dangerous protocols
        for protocol in ["javascript", "data", "vbscript"]:
            if href.lower().startswith(f"{protocol}:"):
                # Return empty dict to strip dangerous link
                return {}

        return attrs @ classmethod

    def extract_text(cls, html_content: str, length: Optional[int] = None) -> str:
        """
        Extract plain text from HTML content.

        Args:
            html_content: HTML content
            length: Optional maximum length

        Returns:
            Plain text extracted from HTML
        """
        # Remove all HTML tags
        text = bleach.clean(html_content, tags=[], strip=True)

        # Strip whitespace
        text = " ".join(text.split())

        if length:
            text = text[:length]
            if len(text) == length and not text.endswith(" "):
                text = text.rsplit(" ", 1)[0] + "..."

        return text

    @classmethod
    def validate_html(cls, html_content: str) -> Tuple[bool, Optional[str]]:
        """
        Validate HTML content for safety.

        Args:
            html_content: HTML to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not html_content:
            return True, None

        try:
            # Try to sanitize
            sanitized = cls.sanitize_html(html_content)

            # Check if content was stripped (potential issue)
            if len(sanitized) == 0 and len(html_content) > 0:
                return False, "HTML content was completely stripped during sanitization"

            return True, None
        except Exception as e:
            return False, f"HTML validation error: {str(e)}"


# Convenience functions for use in templates and views
def sanitize_html(content: str) -> str:
    """Convenience function for HTML sanitization."""
    return mark_safe(ContentSanitizer.sanitize_html(content))


def sanitize_markdown(content: str) -> str:
    """Convenience function for Markdown sanitization."""
    return mark_safe(ContentSanitizer.sanitize_markdown(content))


def sanitize_content(content: str, content_type: str = "html") -> str:
    """Convenience function for content sanitization by type."""
    return mark_safe(ContentSanitizer.sanitize_by_type(content, content_type))
