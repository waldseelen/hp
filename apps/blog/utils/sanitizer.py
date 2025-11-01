"""
HTML/Markdown Sanitization Layer
Prevents XSS attacks and ensures clean content
"""

import logging

import bleach
import markdown
from bleach.css_sanitizer import CSSSanitizer

logger = logging.getLogger(__name__)


# HTML Sanitization Configuration
ALLOWED_TAGS = [
    # Text formatting
    "p",
    "br",
    "strong",
    "em",
    "u",
    "s",
    "del",
    "ins",
    "mark",
    "small",
    "sub",
    "sup",
    "abbr",
    "cite",
    "q",
    "time",
    # Headings
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    # Lists
    "ul",
    "ol",
    "li",
    "dl",
    "dt",
    "dd",
    # Links and media
    "a",
    "img",
    # Code
    "code",
    "pre",
    "kbd",
    "samp",
    "var",
    # Blocks
    "blockquote",
    "hr",
    "div",
    "span",
    "section",
    "article",
    # Tables
    "table",
    "thead",
    "tbody",
    "tfoot",
    "tr",
    "th",
    "td",
    "caption",
    "colgroup",
    "col",
]

ALLOWED_ATTRIBUTES = {
    "*": ["class", "id", "title", "lang", "dir"],
    "a": ["href", "title", "target", "rel", "download"],
    "img": ["src", "alt", "title", "width", "height", "loading"],
    "abbr": ["title"],
    "time": ["datetime"],
    "q": ["cite"],
    "blockquote": ["cite"],
    "td": ["colspan", "rowspan", "headers", "style"],
    "th": ["colspan", "rowspan", "scope", "headers", "style"],
    "col": ["span"],
    "colgroup": ["span"],
    # Allow inline styles only for specific elements
    "span": ["style"],
    "div": ["style"],
    "p": ["style"],
}

# Allowed CSS properties for inline styles
ALLOWED_STYLES = [
    "color",
    "background-color",
    "font-weight",
    "font-style",
    "text-align",
    "text-decoration",
    "margin",
    "margin-top",
    "margin-bottom",
    "margin-left",
    "margin-right",
    "padding",
    "padding-top",
    "padding-bottom",
    "padding-left",
    "padding-right",
]

# Allowed protocols for links
ALLOWED_PROTOCOLS = ["http", "https", "mailto", "tel"]

# CSS Sanitizer instance
css_sanitizer = CSSSanitizer(allowed_css_properties=ALLOWED_STYLES)


def sanitize_html(content: str, strip_comments: bool = True) -> str:
    """
    Sanitize HTML content to prevent XSS attacks.

    Args:
        content: Raw HTML content to sanitize
        strip_comments: Whether to remove HTML comments (default: True)

    Returns:
        Sanitized HTML string

    Example:
        >>> from apps.blog.utils.sanitizer import sanitize_html
        >>> dangerous_html = '<script>alert("XSS")</script><p>Safe content</p>'
        >>> clean_html = sanitize_html(dangerous_html)
        >>> # Result: '<p>Safe content</p>'
    """
    if not content:
        return ""

    try:
        cleaned = bleach.clean(
            content,
            tags=ALLOWED_TAGS,
            attributes=ALLOWED_ATTRIBUTES,
            css_sanitizer=css_sanitizer,
            protocols=ALLOWED_PROTOCOLS,
            strip=True,  # Strip disallowed tags instead of escaping
            strip_comments=strip_comments,
        )

        # Additional cleanup: remove empty paragraphs and divs
        cleaned = cleaned.replace("<p></p>", "").replace("<div></div>", "")

        return cleaned

    except Exception as e:
        logger.error(f"HTML sanitization error: {str(e)}")
        # Return empty string on error to be safe
        return ""


def linkify_content(content: str) -> str:
    """
    Convert plain text URLs to clickable links.

    Args:
        content: HTML content with potential plain text URLs

    Returns:
        HTML with linkified URLs

    Example:
        >>> text = '<p>Visit https://example.com for more info</p>'
        >>> linkify_content(text)
        '<p>Visit <a href="https://example.com">https://example.com</a> for more info</p>'
    """
    if not content:
        return ""

    try:
        return bleach.linkify(
            content,
            callbacks=[bleach.callbacks.nofollow, bleach.callbacks.target_blank],
            skip_tags=["pre", "code"],
            parse_email=True,
        )
    except Exception as e:
        logger.error(f"Linkify error: {str(e)}")
        return content


def markdown_to_html(markdown_content: str, safe: bool = True) -> str:
    """
    Convert Markdown to HTML with optional sanitization.

    Args:
        markdown_content: Markdown formatted text
        safe: Whether to sanitize output HTML (default: True)

    Returns:
        HTML string

    Example:
        >>> md = "# Hello\\n\\nThis is **bold** text."
        >>> markdown_to_html(md)
        '<h1>Hello</h1>\\n<p>This is <strong>bold</strong> text.</p>'
    """
    if not markdown_content:
        return ""

    try:
        # Configure markdown extensions
        extensions = [
            "fenced_code",  # ```code blocks```
            "tables",  # GitHub-style tables
            "nl2br",  # Newlines to <br>
            "sane_lists",  # Better list handling
            "codehilite",  # Syntax highlighting
            "toc",  # Table of contents
        ]

        extension_configs = {
            "codehilite": {
                "css_class": "highlight",
                "linenums": False,
            }
        }

        # Convert markdown to HTML
        html = markdown.markdown(
            markdown_content,
            extensions=extensions,
            extension_configs=extension_configs,
        )

        # Sanitize if requested
        if safe:
            html = sanitize_html(html)

        return html

    except Exception as e:
        logger.error(f"Markdown conversion error: {str(e)}")
        return ""


def extract_plain_text(html_content: str, max_length: int = None) -> str:
    """
    Extract plain text from HTML content.
    Useful for excerpts, meta descriptions, etc.

    Args:
        html_content: HTML content to extract text from
        max_length: Maximum length of returned text (optional)

    Returns:
        Plain text string

    Example:
        >>> html = '<p>Hello <strong>world</strong>!</p>'
        >>> extract_plain_text(html)
        'Hello world!'
    """
    if not html_content:
        return ""

    try:
        # Use bleach to strip all tags
        text = bleach.clean(html_content, tags=[], strip=True)

        # Clean up whitespace
        text = " ".join(text.split())

        # Truncate if needed
        if max_length and len(text) > max_length:
            text = text[:max_length].rsplit(" ", 1)[0] + "..."

        return text

    except Exception as e:
        logger.error(f"Plain text extraction error: {str(e)}")
        return ""


def validate_content_length(
    content: str, min_words: int = 50, max_words: int = 10000
) -> tuple:
    """
    Validate content length based on word count.

    Args:
        content: HTML content to validate
        min_words: Minimum required word count
        max_words: Maximum allowed word count

    Returns:
        Tuple of (is_valid: bool, message: str, word_count: int)

    Example:
        >>> content = '<p>Short text</p>'
        >>> is_valid, message, count = validate_content_length(content, min_words=5)
        >>> # is_valid: False, count: 2
    """
    if not content:
        return False, "Content is empty", 0

    try:
        # Extract plain text and count words
        plain_text = extract_plain_text(content)
        words = plain_text.split()
        word_count = len(words)

        if word_count < min_words:
            return (
                False,
                f"Content too short. Minimum {min_words} words required (found {word_count}).",
                word_count,
            )

        if word_count > max_words:
            return (
                False,
                f"Content too long. Maximum {max_words} words allowed (found {word_count}).",
                word_count,
            )

        return True, "Content length is valid", word_count

    except Exception as e:
        logger.error(f"Content validation error: {str(e)}")
        return False, "Content validation failed", 0


class ContentSanitizer:
    """
    Content sanitization class with configurable settings.
    Use this for advanced scenarios where you need custom sanitization rules.
    """

    def __init__(self, allowed_tags=None, allowed_attributes=None, allowed_styles=None):
        """
        Initialize sanitizer with custom configuration.

        Args:
            allowed_tags: List of allowed HTML tags (optional)
            allowed_attributes: Dict of allowed attributes per tag (optional)
            allowed_styles: List of allowed CSS properties (optional)
        """
        self.allowed_tags = allowed_tags or ALLOWED_TAGS
        self.allowed_attributes = allowed_attributes or ALLOWED_ATTRIBUTES
        self.allowed_styles = allowed_styles or ALLOWED_STYLES
        self.css_sanitizer = CSSSanitizer(allowed_css_properties=self.allowed_styles)

    def clean(self, content: str) -> str:
        """Clean content with custom configuration"""
        if not content:
            return ""

        try:
            return bleach.clean(
                content,
                tags=self.allowed_tags,
                attributes=self.allowed_attributes,
                css_sanitizer=self.css_sanitizer,
                protocols=ALLOWED_PROTOCOLS,
                strip=True,
            )
        except Exception as e:
            logger.error(f"Custom sanitization error: {str(e)}")
            return ""


# Example usage in models:
"""
from apps.blog.utils.sanitizer import sanitize_html, markdown_to_html

class BlogPost(models.Model):
    content_html = models.TextField()
    content_markdown = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        # If markdown content provided, convert to HTML
        if self.content_markdown:
            self.content_html = markdown_to_html(self.content_markdown)

        # Always sanitize HTML content before saving
        self.content_html = sanitize_html(self.content_html)

        super().save(*args, **kwargs)
"""
