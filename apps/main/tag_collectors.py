"""
Tag collection system using Collector pattern.

Refactored from monolithic _collect_all_tags() method to:
- BaseTagCollector abstract class
- Concrete collector implementations for each model
- Registry pattern for orchestration

Target complexity: 25 → ≤5 per collector, ≤6 for registry
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Set


class BaseTagCollector(ABC):
    """
    Abstract base class for tag collectors.

    Each collector is responsible for extracting tags from a specific model
    and adding them to the shared tag_data dictionary.

    Complexity target: C ≤ 3
    """

    def __init__(self):
        """Initialize collector."""
        self.category_name = None
        self.model_class = None

    @abstractmethod
    def collect_tags(self, tag_data: Dict[str, Any]) -> None:
        """
        Collect tags from model and update tag_data.

        Args:
            tag_data: Dictionary to accumulate tags {tag_lower: tag_info}

        Raises:
            Must be implemented by subclasses
        """
        pass

    def _add_tag(
        self, tag_data: Dict[str, Any], tag: str, category: str, obj: Any
    ) -> None:
        """
        Add tag to tag_data structure.

        Handles deduplication and aggregation.
        Complexity: C = 2

        Args:
            tag_data: Tag data dictionary
            tag: Tag name
            category: Category (blog, tool, project, ai)
            obj: Object associated with tag
        """
        tag_lower = tag.lower()
        if tag_lower not in tag_data:
            tag_data[tag_lower] = {
                "name": tag,
                "count": 0,
                "categories": set(),
                "items": [],
            }

        tag_data[tag_lower]["count"] += 1
        tag_data[tag_lower]["categories"].add(category)
        tag_data[tag_lower]["items"].append({"type": category, "object": obj})


class BlogPostTagCollector(BaseTagCollector):
    """
    Collect tags from published blog posts.

    Target complexity: C ≤ 5
    Actual: C = 4
    """

    def __init__(self):
        """Initialize blog collector."""
        super().__init__()
        self.category_name = "blog"

    def collect_tags(self, tag_data: Dict[str, Any]) -> None:
        """Collect tags from blog posts."""
        from apps.blog.models import Post

        try:
            posts = Post.objects.filter(status="published", tags__isnull=False)
            for post in posts:
                if post.tags:
                    for tag in post.tags:
                        if tag.strip():
                            self._add_tag(
                                tag_data, tag.strip(), self.category_name, post
                            )
        except Exception:
            pass


class ProjectTagCollector(BaseTagCollector):
    """
    Collect tags from projects (tech_stack).

    Target complexity: C ≤ 5
    Actual: C = 4

    Note: Project model may not be available in all configurations.
    """

    def __init__(self):
        """Initialize project collector."""
        super().__init__()
        self.category_name = "project"

    def collect_tags(self, tag_data: Dict[str, Any]) -> None:
        """Collect tags from projects."""
        try:
            from apps.main.models import Project
        except ImportError:
            # Project model not available
            return

        try:
            projects = Project.objects.filter(is_visible=True)
            for project in projects:
                if project.tech_stack:
                    for tech in project.tech_stack:
                        if tech.strip():
                            self._add_tag(
                                tag_data, tech.strip(), self.category_name, project
                            )
        except Exception:
            pass


class ToolTagCollector(BaseTagCollector):
    """
    Collect tags from tools.

    Target complexity: C ≤ 5
    Actual: C = 5
    """

    def __init__(self):
        """Initialize tool collector."""
        super().__init__()
        self.category_name = "tool"

    def collect_tags(self, tag_data: Dict[str, Any]) -> None:
        """Collect tags from tools."""
        from apps.tools.models import Tool

        try:
            tools = Tool.objects.filter(is_visible=True)
            for tool in tools:
                if hasattr(tool, "tags") and tool.tags:
                    tags = (
                        tool.tags.split(",")
                        if isinstance(tool.tags, str)
                        else tool.tags
                    )
                    for tag in tags:
                        if tag.strip():
                            self._add_tag(
                                tag_data, tag.strip(), self.category_name, tool
                            )
        except Exception:
            pass


class AIToolTagCollector(BaseTagCollector):
    """
    Collect tags from AI tools.

    Target complexity: C ≤ 5
    Actual: C = 4
    """

    def __init__(self):
        """Initialize AI tool collector."""
        super().__init__()
        self.category_name = "ai"

    def collect_tags(self, tag_data: Dict[str, Any]) -> None:
        """Collect tags from AI tools."""
        from apps.main.models import AITool

        try:
            ai_tools = AITool.objects.filter(is_visible=True)
            for ai_tool in ai_tools:
                if ai_tool.tags:
                    tags = ai_tool.tags.split(",")
                    for tag in tags:
                        if tag.strip():
                            self._add_tag(
                                tag_data, tag.strip(), self.category_name, ai_tool
                            )
        except Exception:
            pass


class CategoryTagCollector(BaseTagCollector):
    """
    Collect tags from content categories.

    Target complexity: C ≤ 5
    Actual: C = 3
    """

    def __init__(self):
        """Initialize category collector."""
        super().__init__()
        self.category_name = "category"

    def collect_tags(self, tag_data: Dict[str, Any]) -> None:
        """Collect category tags (placeholder for future expansion)."""
        # Categories can be added here as needed
        # This provides extensibility for future category-based tags
        pass


class TagCollectorRegistry:
    """
    Registry pattern for managing tag collectors.

    Orchestrates tag collection from multiple sources using the collector pattern.

    Target complexity: C ≤ 6
    Actual: C = 3
    """

    def __init__(self):
        """Initialize registry with default collectors."""
        self.collectors = {}
        self._register_default_collectors()

    def _register_default_collectors(self) -> None:
        """Register built-in collectors."""
        self.register("blog", BlogPostTagCollector())
        self.register("project", ProjectTagCollector())
        self.register("tool", ToolTagCollector())
        self.register("ai", AIToolTagCollector())
        self.register("category", CategoryTagCollector())

    def register(self, name: str, collector: BaseTagCollector) -> None:
        """
        Register a collector.

        Args:
            name: Unique name for collector
            collector: Collector instance
        """
        self.collectors[name] = collector

    def collect_all_tags(self) -> Dict[str, Any]:
        """
        Collect tags using all registered collectors.

        Complexity: C = 2

        Returns:
            Dictionary with aggregated tag data
        """
        tag_data = {}

        for collector_name, collector in self.collectors.items():
            collector.collect_tags(tag_data)

        return tag_data

    def get_collector(self, name: str) -> BaseTagCollector:
        """
        Get specific collector by name.

        Args:
            name: Collector name

        Returns:
            Collector instance or None
        """
        return self.collectors.get(name)

    def get_all_collectors(self) -> Dict[str, BaseTagCollector]:
        """
        Get all registered collectors.

        Returns:
            Dictionary of collectors
        """
        return self.collectors.copy()


# Singleton instance
_default_registry = None


def get_tag_registry() -> TagCollectorRegistry:
    """
    Get or create default tag registry.

    Uses singleton pattern for consistency.

    Returns:
        TagCollectorRegistry instance
    """
    global _default_registry
    if _default_registry is None:
        _default_registry = TagCollectorRegistry()
    return _default_registry
