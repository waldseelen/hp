"""
Unit tests for Portfolio Content Models - Part 1.

Tests cover:
- PersonalInfo (JSON validation, type choices, ordering)
- SocialLink (13 platforms, URL validation, platform-specific rules)
- AITool (9 categories, ratings, featured tools)
- CybersecurityResource (8 types, 4 difficulty levels, severity)

Target: 24 comprehensive tests for content management.
"""

import json

from django.core.exceptions import ValidationError
from django.utils import timezone

import pytest

from apps.portfolio.models import (
    AITool,
    CybersecurityResource,
    PersonalInfo,
    SocialLink,
)

# ============================================================================
# PERSONALINFO MODEL TESTS (JSON Validation, Type Choices)
# ============================================================================


@pytest.mark.django_db
class TestPersonalInfoModel:
    """Test PersonalInfo model - JSON validation and type handling."""

    def test_personalinfo_creation_text(self):
        """Test basic PersonalInfo creation with text type."""
        info = PersonalInfo.objects.create(
            key="full_name",
            value="John Doe",
            type="text",
        )
        assert info.key == "full_name"
        assert info.value == "John Doe"
        assert info.type == "text"
        assert info.is_visible

    def test_personalinfo_creation_json(self):
        """Test PersonalInfo creation with JSON type."""
        json_data = json.dumps({"skills": ["Python", "Django", "React"]})
        info = PersonalInfo.objects.create(
            key="skills",
            value=json_data,
            type="json",
        )
        assert info.type == "json"
        # Should be able to parse JSON
        parsed = json.loads(info.value)
        assert "skills" in parsed
        assert len(parsed["skills"]) == 3

    def test_personalinfo_json_validation_success(self):
        """Test JSON validation succeeds with valid JSON."""
        valid_json = json.dumps({"key": "value", "number": 123})
        info = PersonalInfo(
            key="valid_json",
            value=valid_json,
            type="json",
        )
        info.clean()  # Should not raise

    def test_personalinfo_json_validation_failure(self):
        """Test JSON validation fails with invalid JSON."""
        invalid_json = "{ invalid json }"
        info = PersonalInfo(
            key="invalid_json",
            value=invalid_json,
            type="json",
        )
        with pytest.raises(ValidationError) as exc_info:
            info.clean()
        assert "value" in exc_info.value.message_dict
        assert "Invalid JSON format" in str(exc_info.value)

    def test_personalinfo_ordering(self):
        """Test PersonalInfo ordering by order field."""
        PersonalInfo.objects.create(key="third", value="3", order=3)
        PersonalInfo.objects.create(key="first", value="1", order=1)
        PersonalInfo.objects.create(key="second", value="2", order=2)

        ordered = list(PersonalInfo.objects.all())
        assert ordered[0].key == "first"
        assert ordered[1].key == "second"
        assert ordered[2].key == "third"

    def test_personalinfo_visibility_filtering(self):
        """Test filtering by is_visible flag."""
        PersonalInfo.objects.create(key="visible", value="yes", is_visible=True)
        PersonalInfo.objects.create(key="hidden", value="no", is_visible=False)

        visible = PersonalInfo.objects.filter(is_visible=True)
        assert visible.count() == 1
        assert visible.first().key == "visible"


# ============================================================================
# SOCIALLINK MODEL TESTS (13 Platforms, URL Validation)
# ============================================================================


@pytest.mark.django_db
class TestSocialLinkModel:
    """Test SocialLink model - platform validation and URL rules."""

    def test_sociallink_github_valid(self):
        """Test valid GitHub URL."""
        link = SocialLink(
            platform="github",
            url="https://github.com/testuser",
        )
        link.clean()  # Should not raise
        link.save()
        assert "github.com" in link.url

    def test_sociallink_github_invalid(self):
        """Test invalid GitHub URL (missing github.com)."""
        link = SocialLink(
            platform="github",
            url="https://gitlab.com/testuser",
        )
        with pytest.raises(ValidationError) as exc_info:
            link.clean()
        assert "github.com" in str(exc_info.value).lower()

    def test_sociallink_linkedin_valid(self):
        """Test valid LinkedIn URL."""
        link = SocialLink(
            platform="linkedin",
            url="https://linkedin.com/in/testuser",
        )
        link.clean()
        link.save()
        assert "linkedin.com" in link.url

    def test_sociallink_linkedin_invalid(self):
        """Test invalid LinkedIn URL."""
        link = SocialLink(
            platform="linkedin",
            url="https://facebook.com/testuser",
        )
        with pytest.raises(ValidationError):
            link.clean()

    def test_sociallink_twitter_valid_twitter_domain(self):
        """Test valid Twitter URL with twitter.com."""
        link = SocialLink(
            platform="twitter",
            url="https://twitter.com/testuser",
        )
        link.clean()
        link.save()
        assert "twitter.com" in link.url

    def test_sociallink_twitter_valid_x_domain(self):
        """Test valid Twitter URL with x.com."""
        link = SocialLink(
            platform="twitter",
            url="https://x.com/testuser",
        )
        link.clean()
        link.save()
        assert "x.com" in link.url

    def test_sociallink_twitter_invalid(self):
        """Test invalid Twitter URL (neither twitter.com nor x.com)."""
        link = SocialLink(
            platform="twitter",
            url="https://facebook.com/testuser",
        )
        with pytest.raises(ValidationError):
            link.clean()

    def test_sociallink_email_valid(self):
        """Test valid email link."""
        link = SocialLink(
            platform="email",
            url="test@example.com",
        )
        link.clean()
        link.save()
        # Should auto-add mailto:
        assert link.url.startswith("mailto:")
        assert "test@example.com" in link.url

    def test_sociallink_email_already_mailto(self):
        """Test email link already with mailto:."""
        link = SocialLink(
            platform="email",
            url="mailto:test@example.com",
        )
        link.clean()
        link.save()
        assert link.url == "mailto:test@example.com"

    def test_sociallink_email_invalid(self):
        """Test invalid email address."""
        link = SocialLink(
            platform="email",
            url="invalid-email",
        )
        with pytest.raises(ValidationError):
            link.clean()

    def test_sociallink_generic_url_validation(self):
        """Test generic URL validation for non-platform-specific links."""
        link = SocialLink(
            platform="website",
            url="https://example.com",
        )
        link.clean()
        link.save()
        assert link.url == "https://example.com"

    def test_sociallink_primary_flag_uniqueness(self):
        """Test only one primary link is allowed."""
        link1 = SocialLink.objects.create(
            platform="github",
            url="https://github.com/user1",
            is_primary=True,
        )
        assert link1.is_primary

        link2 = SocialLink.objects.create(
            platform="linkedin",
            url="https://linkedin.com/in/user1",
            is_primary=True,
        )

        # link1 should no longer be primary
        link1.refresh_from_db()
        assert not link1.is_primary
        assert link2.is_primary

    def test_sociallink_ordering(self):
        """Test SocialLink ordering by order field."""
        SocialLink.objects.create(
            platform="github", url="https://github.com/u", order=2
        )
        SocialLink.objects.create(
            platform="linkedin", url="https://linkedin.com/in/u", order=1
        )
        SocialLink.objects.create(
            platform="twitter", url="https://twitter.com/u", order=3
        )

        ordered = list(SocialLink.objects.all())
        assert ordered[0].platform == "linkedin"
        assert ordered[1].platform == "github"
        assert ordered[2].platform == "twitter"


# ============================================================================
# AITOOL MODEL TESTS (9 Categories, Ratings)
# ============================================================================


@pytest.mark.django_db
class TestAIToolModel:
    """Test AITool model - categories, ratings, and features."""

    def test_aitool_creation(self):
        """Test basic AITool creation."""
        tool = AITool.objects.create(
            name="ChatGPT",
            description="AI chatbot by OpenAI",
            url="https://chat.openai.com",
            category="general",
            rating=4.5,
        )
        assert tool.name == "ChatGPT"
        assert tool.category == "general"
        assert tool.rating == 4.5
        assert tool.is_free  # Default True

    def test_aitool_all_categories(self):
        """Test all 9 AI tool categories."""
        categories = [
            "general",
            "visual",
            "video",
            "audio",
            "text",
            "code",
            "research",
            "productivity",
            "other",
        ]
        for cat in categories:
            tool = AITool.objects.create(
                name=f"Tool {cat}",
                description=f"Test tool for {cat}",
                url=f"https://example.com/{cat}",
                category=cat,
            )
            assert tool.category == cat

    def test_aitool_rating_range(self):
        """Test rating values (0-5 scale)."""
        tool = AITool.objects.create(
            name="Test Tool",
            description="Test",
            url="https://example.com",
            rating=5.0,
        )
        assert tool.rating == 5.0

        tool.rating = 0.0
        tool.save()
        assert tool.rating == 0.0

    def test_aitool_featured_flag(self):
        """Test featured tool functionality."""
        tool = AITool.objects.create(
            name="Featured Tool",
            description="Featured",
            url="https://example.com",
            is_featured=True,
        )
        assert tool.is_featured

        featured = AITool.objects.filter(is_featured=True)
        assert featured.count() == 1

    def test_aitool_free_vs_paid(self):
        """Test free vs paid tool distinction."""
        free_tool = AITool.objects.create(
            name="Free Tool",
            description="Free",
            url="https://example.com",
            is_free=True,
        )
        paid_tool = AITool.objects.create(
            name="Paid Tool",
            description="Paid",
            url="https://example.com",
            is_free=False,
        )

        assert free_tool.is_free
        assert not paid_tool.is_free

    def test_aitool_ordering(self):
        """Test AITool ordering by category, order, name."""
        AITool.objects.create(
            name="B Tool",
            description="Test",
            url="https://b.com",
            category="code",
            order=2,
        )
        AITool.objects.create(
            name="A Tool",
            description="Test",
            url="https://a.com",
            category="code",
            order=1,
        )
        AITool.objects.create(
            name="Z Tool",
            description="Test",
            url="https://z.com",
            category="general",
            order=1,
        )

        ordered = list(AITool.objects.all())
        # Should be ordered by category first, then order, then name
        assert ordered[0].name == "A Tool"  # code, order=1
        assert ordered[1].name == "B Tool"  # code, order=2
        assert ordered[2].name == "Z Tool"  # general, order=1


# ============================================================================
# CYBERSECURITYRESOURCE MODEL TESTS (8 Types, 4 Difficulty Levels)
# ============================================================================


@pytest.mark.django_db
class TestCybersecurityResourceModel:
    """Test CybersecurityResource model - types, difficulty, severity."""

    def test_cybersecurity_resource_creation(self):
        """Test basic CybersecurityResource creation."""
        resource = CybersecurityResource.objects.create(
            title="XSS Vulnerability Guide",
            description="Learn about XSS attacks",
            type="tutorial",
            difficulty="beginner",
        )
        assert resource.title == "XSS Vulnerability Guide"
        assert resource.type == "tutorial"
        assert resource.difficulty == "beginner"
        assert resource.severity_level == 1  # Default

    def test_cybersecurity_all_types(self):
        """Test all 8 cybersecurity resource types."""
        types = [
            "tool",
            "threat",
            "standard",
            "practice",
            "news",
            "tutorial",
            "certification",
            "other",
        ]
        for res_type in types:
            resource = CybersecurityResource.objects.create(
                title=f"Test {res_type}",
                description="Test",
                type=res_type,
            )
            assert resource.type == res_type

    def test_cybersecurity_all_difficulty_levels(self):
        """Test all 4 difficulty levels."""
        difficulties = ["beginner", "intermediate", "advanced", "expert"]
        for diff in difficulties:
            resource = CybersecurityResource.objects.create(
                title=f"Test {diff}",
                description="Test",
                difficulty=diff,
            )
            assert resource.difficulty == diff

    def test_cybersecurity_severity_levels(self):
        """Test all 4 severity levels."""
        severities = [
            (1, "Düşük"),
            (2, "Orta"),
            (3, "Yüksek"),
            (4, "Kritik"),
        ]
        for level, _ in severities:
            resource = CybersecurityResource.objects.create(
                title=f"Severity {level}",
                description="Test",
                severity_level=level,
            )
            assert resource.severity_level == level

    def test_cybersecurity_urgent_flag(self):
        """Test urgent threat marking."""
        resource = CybersecurityResource.objects.create(
            title="Urgent Threat",
            description="Critical security threat",
            type="threat",
            is_urgent=True,
            severity_level=4,
        )
        assert resource.is_urgent
        assert resource.severity_level == 4

    def test_cybersecurity_featured_flag(self):
        """Test featured resource functionality."""
        resource = CybersecurityResource.objects.create(
            title="Featured Resource",
            description="Featured",
            is_featured=True,
        )
        assert resource.is_featured

    def test_cybersecurity_ordering_by_urgency_and_severity(self):
        """Test ordering: urgent first, then by severity."""
        # Create resources in different order
        normal = CybersecurityResource.objects.create(
            title="Normal",
            description="Normal",
            is_urgent=False,
            severity_level=2,
        )
        urgent_low = CybersecurityResource.objects.create(
            title="Urgent Low",
            description="Urgent but low severity",
            is_urgent=True,
            severity_level=1,
        )
        urgent_high = CybersecurityResource.objects.create(
            title="Urgent High",
            description="Urgent and high severity",
            is_urgent=True,
            severity_level=4,
        )

        ordered = list(CybersecurityResource.objects.all())
        # Urgent items first (by severity desc), then normal items
        assert ordered[0] == urgent_high  # is_urgent=True, severity=4
        assert ordered[1] == urgent_low  # is_urgent=True, severity=1
        assert ordered[2] == normal  # is_urgent=False, severity=2
