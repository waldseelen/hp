"""Test suite for portfolio views."""

from django.test import Client, TestCase
from django.urls import reverse

from apps.tools.models import Tool


class ToolModelTests(TestCase):
    """Test Tool model."""

    def test_tool_creation(self):
        """Test basic tool creation."""
        tool = Tool.objects.create(
            title="Test Tool",
            description="Test description",
            category="Development",
            url="https://test.com",
            is_visible=True,
        )
        self.assertEqual(tool.title, "Test Tool")
        self.assertTrue(tool.is_visible)


class ProjectsViewTests(TestCase):
    """Test projects view."""

    def setUp(self):
        """Create test data."""
        self.client = Client()
        Tool.objects.create(
            title="Test Tool",
            description="Description",
            category="Development",
            url="https://test.com",
            is_visible=True,
            is_favorite=True,
        )

    def test_projects_page_loads(self):
        """Test projects page loads successfully."""
        response = self.client.get(reverse("main:projects"))
        self.assertEqual(response.status_code, 200)

    def test_projects_uses_correct_template(self):
        """Test correct template is used."""
        response = self.client.get(reverse("main:projects"))
        self.assertTemplateUsed(response, "pages/portfolio/projects.html")


class ProjectDetailTests(TestCase):
    """Test project detail view."""

    def setUp(self):
        """Create test data."""
        self.client = Client()
        self.tool = Tool.objects.create(
            title="Test Project",
            description="Description",
            category="Development",
            url="https://test.com",
            is_visible=True,
            slug="test-project",
        )

    def test_project_detail_loads(self):
        """Test project detail page loads."""
        response = self.client.get(
            reverse("main:project_detail", kwargs={"slug": self.tool.slug})
        )
        self.assertEqual(response.status_code, 200)

    def test_project_detail_404_for_nonexistent(self):
        """Test 404 for non-existent project."""
        response = self.client.get(
            reverse("main:project_detail", kwargs={"slug": "nonexistent-slug"})
        )
        self.assertEqual(response.status_code, 404)
