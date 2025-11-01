"""
SEO optimization utilities for automatic meta descriptions and alt text
"""

import re

from django.utils.html import strip_tags

# truncate_words is not available in newer Django versions
# from django.utils.text import truncate_words


class SEOOptimizer:
    """SEO optimization helper class"""

    @staticmethod
    def generate_meta_description(content, max_length=155):
        """
        Generate optimized meta description from content

        Args:
            content (str): The content to extract description from
            max_length (int): Maximum length of description (default: 155)

        Returns:
            str: Optimized meta description
        """
        if not content:
            return ""

        # Strip HTML tags
        clean_content = strip_tags(content)

        # Remove extra whitespace and line breaks
        clean_content = re.sub(r"\s+", " ", clean_content).strip()

        # If content is shorter than max_length, return as is
        if len(clean_content) <= max_length:
            return clean_content

        # Find a good breaking point near max_length
        if len(clean_content) > max_length:
            # Try to break at sentence end
            sentences = clean_content.split(". ")
            description = ""
            for sentence in sentences:
                if len(description + sentence + ". ") <= max_length:
                    description += sentence + ". "
                else:
                    break

            # If we got a good sentence break, use it
            if len(description) > max_length * 0.7:  # At least 70% of desired length
                return description.strip()

            # Otherwise, truncate at word boundary
            words = clean_content.split()
            description = ""
            for word in words:
                if (
                    len(description + word + " ") <= max_length - 3
                ):  # Leave space for '...'
                    description += word + " "
                else:
                    break

            return (description.strip() + "...").strip()

        return clean_content

    @staticmethod
    def generate_alt_text(filename, context=""):
        """
        Generate descriptive alt text for images based on filename and context

        Args:
            filename (str): Image filename
            context (str): Additional context about the image

        Returns:
            str: Generated alt text
        """
        if not filename:
            return "Image"

        # Extract base name without extension
        base_name = filename.split(".")[0] if "." in filename else filename

        # Remove common prefixes and suffixes
        base_name = re.sub(
            r"^(img_|image_|pic_|photo_)", "", base_name, flags=re.IGNORECASE
        )
        base_name = re.sub(
            r"_(thumb|thumbnail|small|medium|large|xl)$",
            "",
            base_name,
            flags=re.IGNORECASE,
        )

        # Replace underscores and hyphens with spaces
        alt_text = re.sub(r"[_-]+", " ", base_name)

        # Capitalize words properly
        alt_text = " ".join(word.capitalize() for word in alt_text.split())

        # Add context if provided
        if context:
            context = context.strip()
            if not alt_text.lower().startswith(context.lower()):
                alt_text = f"{context} - {alt_text}"

        # Ensure it's not empty
        if not alt_text.strip():
            alt_text = "Image"

        return alt_text.strip()

    @staticmethod
    def optimize_title(title, site_name="Portfolio", max_length=60):
        """
        Optimize page title for SEO

        Args:
            title (str): Page title
            site_name (str): Site name to append
            max_length (int): Maximum title length

        Returns:
            str: Optimized title
        """
        if not title:
            return site_name

        # If title already contains site name, don't add it again
        if site_name.lower() in title.lower():
            optimized = title
        else:
            optimized = f"{title} | {site_name}"

        # Truncate if too long
        if len(optimized) > max_length:
            # Try to truncate the page title part, keeping the site name
            if "|" in optimized:
                page_title, site_part = optimized.split("|", 1)
                available_length = max_length - len(site_part) - 3  # 3 for ' | '
                if available_length > 10:  # Minimum reasonable title length
                    page_title = page_title.strip()[:available_length].strip()
                    optimized = f"{page_title} | {site_part.strip()}"
                else:
                    optimized = title[:max_length].strip()
            else:
                optimized = title[:max_length].strip()

        return optimized

    @staticmethod
    def extract_keywords(content, max_keywords=10):
        """
        Extract keywords from content for meta keywords tag

        Args:
            content (str): Content to extract keywords from
            max_keywords (int): Maximum number of keywords to return

        Returns:
            list: List of keywords
        """
        if not content:
            return []

        # Strip HTML and clean content
        clean_content = strip_tags(content).lower()

        # Remove common stop words
        stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "from",
            "up",
            "about",
            "into",
            "through",
            "during",
            "before",
            "after",
            "above",
            "below",
            "between",
            "among",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "may",
            "might",
            "must",
            "can",
            "this",
            "that",
            "these",
            "those",
            "i",
            "you",
            "he",
            "she",
            "it",
            "we",
            "they",
        }

        # Extract words (2+ characters, alphanumeric)
        words = re.findall(r"\b[a-zA-Z]{2,}\b", clean_content)

        # Filter stop words and count frequency
        word_freq = {}
        for word in words:
            if word not in stop_words and len(word) > 2:
                word_freq[word] = word_freq.get(word, 0) + 1

        # Sort by frequency and return top keywords
        keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in keywords[:max_keywords]]

    @staticmethod
    def generate_slug(text, max_length=50):
        """
        Generate SEO-friendly slug from text

        Args:
            text (str): Text to convert to slug
            max_length (int): Maximum slug length

        Returns:
            str: SEO-friendly slug
        """
        if not text:
            return ""

        # Convert to lowercase
        slug = text.lower()

        # Replace spaces and special characters with hyphens
        slug = re.sub(r"[^\w\s-]", "", slug)
        slug = re.sub(r"[\s_-]+", "-", slug)

        # Remove leading/trailing hyphens
        slug = slug.strip("-")

        # Truncate if too long
        if len(slug) > max_length:
            # Try to break at hyphen near the limit
            parts = slug[:max_length].split("-")
            if len(parts) > 1:
                slug = "-".join(parts[:-1])
            else:
                slug = slug[:max_length]

        return slug
