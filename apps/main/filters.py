"""
Advanced filtering system for blog posts, projects and other content
"""

from datetime import datetime, timedelta

from django.db.models import Q
from django.utils import timezone

from apps.blog.models import Post
from apps.main.models import BlogCategory, Project


class ContentFilter:
    """Advanced content filtering system"""

    def __init__(self, queryset):
        self.queryset = queryset
        self.model = queryset.model

    def filter_by_text(self, query):
        """Filter by text search in multiple fields"""
        if not query:
            return self

        text_fields = self._get_text_fields()
        search_q = Q()

        for field in text_fields:
            search_q |= Q(**{f"{field}__icontains": query})

        self.queryset = self.queryset.filter(search_q)
        return self

    def filter_by_tags(self, tags):
        """Filter by tags (supports multiple tags)"""
        if not tags:
            return self

        if isinstance(tags, str):
            tags = [tag.strip() for tag in tags.split(",")]

        tag_field = self._get_tag_field()
        if not tag_field:
            return self

        tag_q = Q()
        for tag in tags:
            if tag.strip():
                tag_q |= Q(**{f"{tag_field}__icontains": tag.strip()})

        if tag_q:
            self.queryset = self.queryset.filter(tag_q)

        return self

    def filter_by_category(self, categories):
        """Filter by categories"""
        if not categories:
            return self

        if isinstance(categories, str):
            categories = [categories]

        category_field = self._get_category_field()
        if category_field:
            if hasattr(self.model._meta.get_field(category_field), "related_model"):
                # Foreign key relationship
                self.queryset = self.queryset.filter(
                    **{f"{category_field}__name__in": categories}
                )
            else:
                # Direct field
                self.queryset = self.queryset.filter(
                    **{f"{category_field}__in": categories}
                )

        return self

    def filter_by_date_range(self, start_date=None, end_date=None):
        """Filter by date range"""
        date_field = self._get_date_field()
        if not date_field:
            return self

        if start_date:
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            self.queryset = self.queryset.filter(**{f"{date_field}__gte": start_date})

        if end_date:
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
            self.queryset = self.queryset.filter(**{f"{date_field}__lte": end_date})

        return self

    def filter_by_status(self, statuses):
        """Filter by status (for content with status field)"""
        if not statuses:
            return self

        if isinstance(statuses, str):
            statuses = [statuses]

        if hasattr(self.model, "status"):
            self.queryset = self.queryset.filter(status__in=statuses)

        return self

    def filter_by_featured(self, featured_only=False):
        """Filter by featured content"""
        if featured_only and hasattr(self.model, "is_featured"):
            self.queryset = self.queryset.filter(is_featured=True)

        return self

    def filter_by_difficulty(self, min_difficulty=None, max_difficulty=None):
        """Filter by difficulty level (for projects)"""
        if hasattr(self.model, "difficulty_level"):
            if min_difficulty:
                self.queryset = self.queryset.filter(
                    difficulty_level__gte=min_difficulty
                )
            if max_difficulty:
                self.queryset = self.queryset.filter(
                    difficulty_level__lte=max_difficulty
                )

        return self

    def filter_by_tech_stack(self, technologies):
        """Filter by technologies (for projects)"""
        if not technologies or not hasattr(self.model, "tech_stack"):
            return self

        if isinstance(technologies, str):
            technologies = [tech.strip() for tech in technologies.split(",")]

        tech_q = Q()
        for tech in technologies:
            if tech.strip():
                tech_q |= Q(tech_stack__icontains=tech.strip())

        if tech_q:
            self.queryset = self.queryset.filter(tech_q)

        return self

    def sort_by(self, sort_field, direction="desc"):
        """Sort results"""
        valid_sort_fields = self._get_sortable_fields()

        if sort_field not in valid_sort_fields:
            sort_field = "created_at"  # Default sort

        if direction == "desc":
            sort_field = f"-{sort_field}"

        self.queryset = self.queryset.order_by(sort_field)
        return self

    def get_queryset(self):
        """Get the filtered queryset"""
        return self.queryset.distinct()

    def _get_text_fields(self):
        """Get text fields to search in for each model"""
        text_fields_map = {
            "Post": ["title", "content", "excerpt"],
            "Project": ["title", "description", "detailed_description"],
            "Tool": ["name", "description", "long_description"],
            "AITool": ["name", "description"],
            "CybersecurityResource": ["title", "description", "content"],
            "UsefulResource": ["name", "description"],
            "BlogPost": ["title", "content", "excerpt"],
        }
        return text_fields_map.get(self.model.__name__, ["title", "description"])

    def _get_tag_field(self):
        """Get tag field name for each model"""
        tag_fields_map = {
            "Post": "tags",
            "Project": "tech_stack",
            "Tool": "tags",
            "AITool": "tags",
            "CybersecurityResource": "tags",
            "UsefulResource": "tags",
            "BlogPost": "tags",
        }
        return tag_fields_map.get(self.model.__name__)

    def _get_category_field(self):
        """Get category field name for each model"""
        category_fields_map = {
            "Post": None,  # Posts don't have categories in this model
            "Project": None,
            "Tool": "category",
            "AITool": "category",
            "CybersecurityResource": "type",
            "UsefulResource": "category",
            "BlogPost": "category",
        }
        return category_fields_map.get(self.model.__name__)

    def _get_date_field(self):
        """Get primary date field for each model"""
        date_fields_map = {
            "Post": "published_at",
            "Project": "created_at",
            "Tool": "created_at",
            "AITool": "created_at",
            "CybersecurityResource": "created_at",
            "UsefulResource": "created_at",
            "BlogPost": "published_at",
        }
        return date_fields_map.get(self.model.__name__, "created_at")

    def _get_sortable_fields(self):
        """Get valid sortable fields for each model"""
        base_fields = ["created_at", "updated_at"]

        sortable_fields_map = {
            "Post": base_fields + ["published_at", "title", "view_count"],
            "Project": base_fields
            + ["title", "view_count", "difficulty_level", "start_date"],
            "Tool": base_fields + ["name", "rating"],
            "AITool": base_fields + ["name", "rating"],
            "CybersecurityResource": base_fields + ["title", "severity_level"],
            "UsefulResource": base_fields + ["name", "rating"],
            "BlogPost": base_fields + ["published_at", "title", "view_count"],
        }
        return sortable_fields_map.get(self.model.__name__, base_fields)


class BlogFilter(ContentFilter):
    """Specialized filter for blog posts"""

    def filter_by_author(self, authors):
        """Filter by author"""
        if not authors:
            return self

        if isinstance(authors, str):
            authors = [authors]

        if hasattr(self.model, "author"):
            self.queryset = self.queryset.filter(author__name__in=authors)

        return self

    def filter_by_reading_time(self, min_time=None, max_time=None):
        """Filter by estimated reading time"""
        if min_time:
            self.queryset = (
                self.queryset.filter(reading_time__gte=min_time)
                if hasattr(self.model, "reading_time")
                else self.queryset
            )

        if max_time:
            self.queryset = (
                self.queryset.filter(reading_time__lte=max_time)
                if hasattr(self.model, "reading_time")
                else self.queryset
            )

        return self

    def filter_published_only(self):
        """Filter to only published posts"""
        if hasattr(self.model, "status"):
            self.queryset = self.queryset.filter(status="published")

        return self

    def filter_by_popularity(self, min_views=None):
        """Filter by popularity (view count)"""
        if min_views and hasattr(self.model, "view_count"):
            self.queryset = self.queryset.filter(view_count__gte=min_views)

        return self


class ProjectFilter(ContentFilter):
    """Specialized filter for projects"""

    def filter_by_status(self, statuses):
        """Filter by project status"""
        if not statuses:
            return self

        if isinstance(statuses, str):
            statuses = [statuses]

        self.queryset = self.queryset.filter(status__in=statuses)
        return self

    def filter_by_open_source(self, open_source_only=False):
        """Filter by open source projects"""
        if open_source_only:
            self.queryset = self.queryset.filter(is_open_source=True)

        return self

    def filter_by_completion_date(self, completed_after=None, completed_before=None):
        """Filter by completion date"""
        if completed_after:
            if isinstance(completed_after, str):
                completed_after = datetime.strptime(completed_after, "%Y-%m-%d").date()
            self.queryset = self.queryset.filter(end_date__gte=completed_after)

        if completed_before:
            if isinstance(completed_before, str):
                completed_before = datetime.strptime(
                    completed_before, "%Y-%m-%d"
                ).date()
            self.queryset = self.queryset.filter(end_date__lte=completed_before)

        return self


def get_filter_options():
    """Get available filter options for the frontend"""
    from apps.main.models import AITool, CybersecurityResource, UsefulResource

    # Get categories for different content types
    blog_categories = []
    try:
        blog_categories = list(
            BlogCategory.objects.filter(is_visible=True).values("name", "display_name")
        )
    except Exception:
        pass

    # Get AI tool categories
    ai_categories = []
    if hasattr(AITool, "CATEGORY_CHOICES"):
        ai_categories = [
            {"value": choice[0], "label": choice[1]}
            for choice in AITool.CATEGORY_CHOICES
        ]

    # Get cybersecurity types
    cyber_types = []
    if hasattr(CybersecurityResource, "TYPE_CHOICES"):
        cyber_types = [
            {"value": choice[0], "label": choice[1]}
            for choice in CybersecurityResource.TYPE_CHOICES
        ]

    # Get useful resource categories
    resource_categories = []
    if hasattr(UsefulResource, "CATEGORY_CHOICES"):
        resource_categories = [
            {"value": choice[0], "label": choice[1]}
            for choice in UsefulResource.CATEGORY_CHOICES
        ]

    # Get project statuses
    project_statuses = []
    if hasattr(Project, "STATUS_CHOICES"):
        project_statuses = [
            {"value": choice[0], "label": choice[1]}
            for choice in Project.STATUS_CHOICES
        ]

    # Get common tags
    popular_tags = get_popular_tags()

    return {
        "blog_categories": blog_categories,
        "ai_categories": ai_categories,
        "cyber_types": cyber_types,
        "resource_categories": resource_categories,
        "project_statuses": project_statuses,
        "popular_tags": popular_tags[:20],  # Top 20 tags
        "date_ranges": [
            {"value": "last_week", "label": "Last Week"},
            {"value": "last_month", "label": "Last Month"},
            {"value": "last_3_months", "label": "Last 3 Months"},
            {"value": "last_year", "label": "Last Year"},
            {"value": "custom", "label": "Custom Range"},
        ],
        "sort_options": [
            {"value": "created_at", "label": "Newest First"},
            {"value": "-created_at", "label": "Oldest First"},
            {"value": "title", "label": "Title A-Z"},
            {"value": "-title", "label": "Title Z-A"},
            {"value": "view_count", "label": "Most Popular"},
            {"value": "-view_count", "label": "Least Popular"},
        ],
    }


def get_popular_tags(limit=50):  # noqa: C901
    """Get most popular tags across all content"""
    tag_counts = {}

    # Collect tags from blog posts
    try:
        posts = Post.objects.filter(status="published", tags__isnull=False)
        for post in posts:
            if post.tags:
                for tag in post.tags:
                    if tag.strip():
                        tag_counts[tag.strip()] = tag_counts.get(tag.strip(), 0) + 1
    except Exception:
        pass

    # Collect tags from projects
    try:
        projects = Project.objects.filter(is_visible=True)
        for project in projects:
            if project.tech_stack:
                for tech in project.tech_stack:
                    if tech.strip():
                        tag_counts[tech.strip()] = tag_counts.get(tech.strip(), 0) + 1
    except Exception:
        pass

    # Sort by frequency
    sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)

    return [{"name": tag, "count": count} for tag, count in sorted_tags[:limit]]


def apply_date_range_filter(queryset, date_range, date_field="created_at"):
    """Apply predefined date range filters"""
    now = timezone.now()

    date_ranges = {
        "last_week": now - timedelta(weeks=1),
        "last_month": now - timedelta(days=30),
        "last_3_months": now - timedelta(days=90),
        "last_year": now - timedelta(days=365),
    }

    if date_range in date_ranges:
        return queryset.filter(**{f"{date_field}__gte": date_ranges[date_range]})

    return queryset
