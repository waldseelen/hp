"""
Unit tests for SEO Optimization Module

Tests the SEOOptimizer class for meta descriptions, alt text,
title optimization, keyword extraction, and slug generation.

Coverage target: 85%+
"""

import pytest

from apps.main.seo import SEOOptimizer

# ============================================================================
# Meta Description Generation Tests
# ============================================================================


class TestMetaDescriptionGeneration:
    """Test meta description generation from content"""

    def test_generate_meta_description_from_plain_text(self):
        """Should generate description from plain text"""
        content = (
            "This is a sample blog post about Django development. "
            "We cover best practices and optimization techniques. "
            "Perfect for beginners and advanced users."
        )
        description = SEOOptimizer.generate_meta_description(content)

        assert description
        assert len(description) <= 155
        assert "Django development" in description

    def test_generate_meta_description_strips_html(self):
        """Should strip HTML tags from content"""
        content = (
            "<p>This is a <strong>blog post</strong> about <a href='#'>Django</a>.</p>"
        )
        description = SEOOptimizer.generate_meta_description(content)

        assert "<p>" not in description
        assert "<strong>" not in description
        assert "<a" not in description
        assert "blog post" in description

    def test_generate_meta_description_removes_extra_whitespace(self):
        """Should clean extra whitespace and line breaks"""
        content = """This is  a    sample


        text with    multiple   spaces."""
        description = SEOOptimizer.generate_meta_description(content)

        assert "  " not in description  # No double spaces
        assert "\n" not in description

    def test_generate_meta_description_respects_max_length(self):
        """Should not exceed max_length parameter"""
        content = "A " * 200  # Very long content
        description = SEOOptimizer.generate_meta_description(content, max_length=100)

        assert len(description) <= 100

    def test_generate_meta_description_breaks_at_sentence(self):
        """Should prefer breaking at sentence end"""
        content = "This is sentence one. This is sentence two. This is a very long sentence that should be cut off."
        description = SEOOptimizer.generate_meta_description(content, max_length=60)

        # Should end with period (sentence break)
        assert description.endswith(".")
        assert len(description) <= 60

    def test_generate_meta_description_breaks_at_word(self):
        """Should break at word boundary if no good sentence break"""
        content = "This is a very long sentence without any periods at all just keeps going and going"
        description = SEOOptimizer.generate_meta_description(content, max_length=50)

        assert description.endswith("...")
        assert len(description) <= 50
        # Should not cut mid-word
        assert not description[:-3].endswith(" ")

    def test_generate_meta_description_short_content(self):
        """Should return short content as-is"""
        content = "Short description."
        description = SEOOptimizer.generate_meta_description(content)

        assert description == content

    def test_generate_meta_description_empty_content(self):
        """Should handle empty content"""
        description = SEOOptimizer.generate_meta_description("")

        assert description == ""

    def test_generate_meta_description_whitespace_only(self):
        """Should handle whitespace-only content"""
        description = SEOOptimizer.generate_meta_description("   \n\t   ")

        assert description == ""


# ============================================================================
# Alt Text Generation Tests
# ============================================================================


class TestAltTextGeneration:
    """Test alt text generation for images"""

    def test_generate_alt_text_from_filename(self):
        """Should generate descriptive alt text from filename"""
        filename = "django_tutorial_screenshot.png"
        alt_text = SEOOptimizer.generate_alt_text(filename)

        assert "Django" in alt_text
        assert "Tutorial" in alt_text
        assert "Screenshot" in alt_text
        assert "_" not in alt_text  # Underscores removed

    def test_generate_alt_text_removes_common_prefixes(self):
        """Should remove common image prefixes"""
        filenames = [
            "img_profile_photo.jpg",
            "image_header_banner.png",
            "pic_thumbnail.gif",
            "photo_landscape.jpg",
        ]

        for filename in filenames:
            alt_text = SEOOptimizer.generate_alt_text(filename)
            assert not alt_text.lower().startswith("img")
            assert not alt_text.lower().startswith("image")
            assert not alt_text.lower().startswith("pic")
            assert not alt_text.lower().startswith("photo")

    def test_generate_alt_text_removes_size_suffixes(self):
        """Should remove common size suffixes"""
        filename = "product_image_large.jpg"
        alt_text = SEOOptimizer.generate_alt_text(filename)

        assert "large" not in alt_text.lower()
        assert "Product" in alt_text
        assert "Image" in alt_text

    def test_generate_alt_text_replaces_hyphens_with_spaces(self):
        """Should replace hyphens and underscores with spaces"""
        filename = "modern-web-design_concept.png"
        alt_text = SEOOptimizer.generate_alt_text(filename)

        assert "-" not in alt_text
        assert "_" not in alt_text
        assert " " in alt_text

    def test_generate_alt_text_capitalizes_words(self):
        """Should capitalize words properly"""
        filename = "django_rest_api.png"
        alt_text = SEOOptimizer.generate_alt_text(filename)

        # Words should be capitalized
        words = alt_text.split()
        for word in words:
            if word not in ["-"]:  # Ignore separators
                assert word[0].isupper() or word[0].isdigit()

    def test_generate_alt_text_with_context(self):
        """Should add context to alt text"""
        filename = "screenshot.png"
        context = "Django Admin Dashboard"
        alt_text = SEOOptimizer.generate_alt_text(filename, context=context)

        assert context in alt_text
        assert "Screenshot" in alt_text

    def test_generate_alt_text_empty_filename(self):
        """Should handle empty filename"""
        alt_text = SEOOptimizer.generate_alt_text("")

        assert alt_text == "Image"

    def test_generate_alt_text_filename_without_extension(self):
        """Should handle filename without extension"""
        filename = "profile_picture"
        alt_text = SEOOptimizer.generate_alt_text(filename)

        assert "Profile" in alt_text
        assert "Picture" in alt_text


# ============================================================================
# Title Optimization Tests
# ============================================================================


class TestTitleOptimization:
    """Test page title optimization"""

    def test_optimize_title_appends_site_name(self):
        """Should append site name to title"""
        title = "About Us"
        optimized = SEOOptimizer.optimize_title(title, site_name="MyPortfolio")

        assert "About Us" in optimized
        assert "MyPortfolio" in optimized
        assert "|" in optimized

    def test_optimize_title_doesnt_duplicate_site_name(self):
        """Should not duplicate site name if already present"""
        title = "About Us | MyPortfolio"
        optimized = SEOOptimizer.optimize_title(title, site_name="MyPortfolio")

        # Should not have two occurrences of site name
        assert optimized.count("MyPortfolio") == 1

    def test_optimize_title_respects_max_length(self):
        """Should truncate if exceeds max_length"""
        title = "This is a very long page title that should be truncated"
        optimized = SEOOptimizer.optimize_title(
            title, site_name="Portfolio", max_length=40
        )

        assert len(optimized) <= 40

    def test_optimize_title_keeps_site_name_when_truncating(self):
        """Should prioritize keeping site name when truncating"""
        title = "This is a very long page title"
        optimized = SEOOptimizer.optimize_title(
            title, site_name="MyPortfolio", max_length=40
        )

        # Site name should still be present
        assert "MyPortfolio" in optimized
        assert "|" in optimized

    def test_optimize_title_empty_title(self):
        """Should return site name if title is empty"""
        optimized = SEOOptimizer.optimize_title("", site_name="MyPortfolio")

        assert optimized == "MyPortfolio"

    def test_optimize_title_case_insensitive_duplicate_check(self):
        """Should check for duplicate site name case-insensitively"""
        title = "About Us | myportfolio"
        optimized = SEOOptimizer.optimize_title(title, site_name="MyPortfolio")

        # Should not duplicate (case-insensitive check)
        assert optimized.lower().count("myportfolio") == 1


# ============================================================================
# Keyword Extraction Tests
# ============================================================================


class TestKeywordExtraction:
    """Test keyword extraction from content"""

    def test_extract_keywords_from_content(self):
        """Should extract meaningful keywords"""
        content = "Django development is great. Python programming with Django framework is powerful. Django web applications are scalable."
        keywords = SEOOptimizer.extract_keywords(content)

        assert "django" in keywords
        assert "python" in keywords
        # Stop words should not be included
        assert "is" not in keywords
        assert "the" not in keywords

    def test_extract_keywords_strips_html(self):
        """Should strip HTML before extracting keywords"""
        content = "<p>Django <strong>development</strong> is great.</p>"
        keywords = SEOOptimizer.extract_keywords(content)

        assert "django" in keywords
        assert "development" in keywords

    def test_extract_keywords_respects_max_keywords(self):
        """Should limit number of keywords"""
        content = " ".join([f"word{i}" for i in range(100)])  # 100 unique words
        keywords = SEOOptimizer.extract_keywords(content, max_keywords=5)

        assert len(keywords) <= 5

    def test_extract_keywords_filters_stop_words(self):
        """Should filter common stop words"""
        content = "the and or but in on at to for of with by from is are was were"
        keywords = SEOOptimizer.extract_keywords(content)

        # All these should be filtered out
        assert len(keywords) == 0

    def test_extract_keywords_filters_short_words(self):
        """Should filter words shorter than 3 characters"""
        content = "a an to by at in on up django development"
        keywords = SEOOptimizer.extract_keywords(content)

        assert "a" not in keywords
        assert "to" not in keywords
        assert "django" in keywords

    def test_extract_keywords_returns_by_frequency(self):
        """Should return most frequent keywords first"""
        content = "django " * 10 + "python " * 5 + "web " * 3
        keywords = SEOOptimizer.extract_keywords(content, max_keywords=3)

        # Should be ordered by frequency
        assert keywords[0] == "django"
        assert keywords[1] == "python"

    def test_extract_keywords_empty_content(self):
        """Should handle empty content"""
        keywords = SEOOptimizer.extract_keywords("")

        assert keywords == []

    def test_extract_keywords_only_stop_words(self):
        """Should return empty list if only stop words present"""
        content = "the and or but in on at"
        keywords = SEOOptimizer.extract_keywords(content)

        assert keywords == []


# ============================================================================
# Slug Generation Tests
# ============================================================================


class TestSlugGeneration:
    """Test SEO-friendly slug generation"""

    def test_generate_slug_from_text(self):
        """Should generate URL-friendly slug"""
        text = "Django Tutorial for Beginners"
        slug = SEOOptimizer.generate_slug(text)

        assert slug == "django-tutorial-for-beginners"

    def test_generate_slug_removes_special_characters(self):
        """Should remove special characters"""
        text = "Django & Python @ 2024!"
        slug = SEOOptimizer.generate_slug(text)

        assert "&" not in slug
        assert "@" not in slug
        assert "!" not in slug

    def test_generate_slug_replaces_spaces_with_hyphens(self):
        """Should replace spaces with hyphens"""
        text = "My Blog Post"
        slug = SEOOptimizer.generate_slug(text)

        assert " " not in slug
        assert "-" in slug

    def test_generate_slug_removes_leading_trailing_hyphens(self):
        """Should remove leading/trailing hyphens"""
        text = "---Django Tutorial---"
        slug = SEOOptimizer.generate_slug(text)

        assert not slug.startswith("-")
        assert not slug.endswith("-")

    def test_generate_slug_collapses_multiple_hyphens(self):
        """Should collapse multiple hyphens into one"""
        text = "Django   Tutorial   For   Beginners"
        slug = SEOOptimizer.generate_slug(text)

        assert "--" not in slug

    def test_generate_slug_respects_max_length(self):
        """Should truncate if exceeds max_length"""
        text = "This is a very long title that should be truncated to fit within max length"
        slug = SEOOptimizer.generate_slug(text, max_length=30)

        assert len(slug) <= 30

    def test_generate_slug_breaks_at_hyphen_when_truncating(self):
        """Should prefer breaking at hyphen when truncating"""
        text = "Django Web Development Tutorial"
        slug = SEOOptimizer.generate_slug(text, max_length=20)

        # Should not end with partial word
        assert not slug[-1].isalpha() or slug.count("-") >= 1

    def test_generate_slug_empty_text(self):
        """Should handle empty text"""
        slug = SEOOptimizer.generate_slug("")

        assert slug == ""

    def test_generate_slug_lowercase_conversion(self):
        """Should convert to lowercase"""
        text = "DJANGO TUTORIAL"
        slug = SEOOptimizer.generate_slug(text)

        assert slug.islower()

    def test_generate_slug_underscores_to_hyphens(self):
        """Should convert underscores to hyphens"""
        text = "django_web_development"
        slug = SEOOptimizer.generate_slug(text)

        assert "_" not in slug
        assert "django-web-development" == slug


# ============================================================================
# Edge Case Tests
# ============================================================================


class TestSEOOptimizerEdgeCases:
    """Test edge cases and error handling"""

    def test_meta_description_with_unicode(self):
        """Should handle Unicode characters"""
        content = "Django 开发教程 - Beginners Guide"
        description = SEOOptimizer.generate_meta_description(content)

        assert "Django" in description
        assert "Beginners" in description

    def test_alt_text_with_numbers(self):
        """Should handle filenames with numbers"""
        filename = "screenshot_2024_v2.png"
        alt_text = SEOOptimizer.generate_alt_text(filename)

        assert "2024" in alt_text
        assert "V2" in alt_text

    def test_title_optimization_only_site_name(self):
        """Should handle when title equals site name"""
        optimized = SEOOptimizer.optimize_title("MyPortfolio", site_name="MyPortfolio")

        # Should not duplicate
        assert optimized.count("MyPortfolio") == 1

    def test_keywords_with_punctuation(self):
        """Should handle content with heavy punctuation"""
        content = "Django, Python, Web-Development. Framework! Awesome!!!"
        keywords = SEOOptimizer.extract_keywords(content)

        assert "django" in keywords
        assert "python" in keywords
        assert "framework" in keywords

    def test_slug_with_apostrophes(self):
        """Should handle apostrophes in text"""
        text = "Django's Best Practices"
        slug = SEOOptimizer.generate_slug(text)

        assert "'" not in slug
        assert "django" in slug.lower()

    def test_meta_description_very_short_sentences(self):
        """Should handle very short sentences"""
        content = "A. B. C. D. E. F. G. H. I. J."
        description = SEOOptimizer.generate_meta_description(content, max_length=10)

        assert len(description) <= 10

    def test_alt_text_only_numbers(self):
        """Should handle filename that's only numbers"""
        filename = "123456.jpg"
        alt_text = SEOOptimizer.generate_alt_text(filename)

        assert alt_text  # Should not be empty
        assert "123456" in alt_text

    def test_slug_only_special_characters(self):
        """Should handle text with only special characters"""
        text = "!@#$%^&*()"
        slug = SEOOptimizer.generate_slug(text)

        assert slug == ""  # All filtered out
