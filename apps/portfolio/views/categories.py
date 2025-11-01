"""
Category page views for different content types
"""

from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.generic import DetailView, ListView

from apps.blog.models import Post
from apps.main.filters import BlogFilter, ContentFilter, ProjectFilter
from apps.main.models import AITool, BlogCategory, Project


@method_decorator(cache_page(60 * 15), name="dispatch")  # Cache for 15 minutes
class BlogCategoryListView(ListView):
    """List all blog categories"""

    model = BlogCategory
    template_name = "categories/blog_categories.html"
    context_object_name = "categories"

    def get_queryset(self):
        return (
            BlogCategory.objects.filter(is_visible=True, show_in_menu=True)
            .annotate(post_count=Count("posts", filter=Q(posts__status="published")))
            .order_by("order", "display_name")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get featured categories
        featured_categories = self.get_queryset().filter(is_featured=True)[:6]

        # Get categories by parent
        parent_categories = self.get_queryset().filter(parent_category__isnull=True)

        context.update(
            {
                "featured_categories": featured_categories,
                "parent_categories": parent_categories,
                "total_categories": self.get_queryset().count(),
                "total_posts": Post.objects.filter(status="published").count(),
            }
        )

        return context


class BlogCategoryDetailView(DetailView):
    """Detail view for a specific blog category"""

    model = BlogCategory
    template_name = "categories/blog_category_detail.html"
    context_object_name = "category"
    slug_field = "name"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return BlogCategory.objects.filter(is_visible=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = self.get_object()

        # Get posts in this category
        posts_queryset = Post.objects.filter(
            category=category, status="published"
        ).select_related("author", "category")

        # Apply filters from request
        blog_filter = BlogFilter(posts_queryset)

        # Filter by tags if specified
        tags = self.request.GET.get("tags", "")
        if tags:
            blog_filter = blog_filter.filter_by_tags(tags)

        # Filter by date range
        date_range = self.request.GET.get("date_range", "")
        if date_range:
            if date_range == "custom":
                start_date = self.request.GET.get("start_date")
                end_date = self.request.GET.get("end_date")
                blog_filter = blog_filter.filter_by_date_range(start_date, end_date)
            else:
                from apps.main.filters import apply_date_range_filter

                posts_queryset = apply_date_range_filter(
                    posts_queryset, date_range, "published_at"
                )
                blog_filter = BlogFilter(posts_queryset)

        # Sort posts
        sort_by = self.request.GET.get("sort", "published_at")
        sort_direction = (
            "desc" if sort_by.startswith("-") else "desc"
        )  # Default to desc for dates
        blog_filter = blog_filter.sort_by(sort_by.lstrip("-"), sort_direction)

        filtered_posts = blog_filter.get_queryset()

        # Paginate posts
        page = self.request.GET.get("page", 1)
        paginator = Paginator(filtered_posts, 12)
        page_obj = paginator.get_page(page)

        # Get related categories
        related_categories = BlogCategory.objects.filter(
            is_visible=True, parent_category=category.parent_category
        ).exclude(id=category.id)[:6]

        # Get popular tags for this category
        category_tags = self._get_category_tags(category)

        context.update(
            {
                "posts": page_obj,
                "page_obj": page_obj,
                "total_posts": filtered_posts.count(),
                "related_categories": related_categories,
                "category_tags": category_tags,
                "applied_filters": {
                    "tags": tags,
                    "date_range": date_range,
                    "sort": sort_by,
                },
            }
        )

        return context

    def _get_category_tags(self, category):
        """Get popular tags for posts in this category"""
        posts = Post.objects.filter(
            category=category, status="published", tags__isnull=False
        )

        tag_counts = {}
        for post in posts:
            if post.tags:
                for tag in post.tags:
                    if tag.strip():
                        tag_counts[tag.strip()] = tag_counts.get(tag.strip(), 0) + 1

        # Sort by frequency and return top 15
        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
        return [{"name": tag, "count": count} for tag, count in sorted_tags[:15]]


class AIToolCategoryView(ListView):
    """AI Tools category page"""

    model = AITool
    template_name = "categories/ai_tools.html"
    context_object_name = "tools"
    paginate_by = 24

    def get_queryset(self):
        queryset = AITool.objects.filter(is_visible=True)

        # Apply filters
        content_filter = ContentFilter(queryset)

        # Filter by category
        category = self.request.GET.get("category")
        if category:
            content_filter = content_filter.filter_by_category([category])

        # Filter by tags
        tags = self.request.GET.get("tags")
        if tags:
            content_filter = content_filter.filter_by_tags(tags)

        # Filter by featured
        featured_only = self.request.GET.get("featured") == "true"
        content_filter = content_filter.filter_by_featured(featured_only)

        # Filter by free/paid
        is_free = self.request.GET.get("free")
        if is_free == "true":
            queryset = content_filter.get_queryset().filter(is_free=True)
        elif is_free == "false":
            queryset = content_filter.get_queryset().filter(is_free=False)
        else:
            queryset = content_filter.get_queryset()

        # Sort
        sort_by = self.request.GET.get("sort", "category")
        content_filter = ContentFilter(queryset).sort_by(sort_by)

        return content_filter.get_queryset()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get categories with counts
        categories = []
        for choice in AITool.CATEGORY_CHOICES:
            count = AITool.objects.filter(category=choice[0], is_visible=True).count()
            if count > 0:
                categories.append(
                    {"code": choice[0], "name": choice[1], "count": count}
                )

        # Get featured tools
        featured_tools = AITool.objects.filter(
            is_visible=True, is_featured=True
        ).order_by("order")[:8]

        # Get popular tags
        popular_tags = self._get_popular_ai_tags()

        context.update(
            {
                "categories": categories,
                "featured_tools": featured_tools,
                "popular_tags": popular_tags,
                "applied_filters": {
                    "category": self.request.GET.get("category", ""),
                    "tags": self.request.GET.get("tags", ""),
                    "featured": self.request.GET.get("featured", ""),
                    "free": self.request.GET.get("free", ""),
                    "sort": self.request.GET.get("sort", "category"),
                },
                "filter_options": {
                    "categories": [
                        {"value": c[0], "label": c[1]} for c in AITool.CATEGORY_CHOICES
                    ],
                    "sort_options": [
                        {"value": "category", "label": "Category"},
                        {"value": "name", "label": "Name A-Z"},
                        {"value": "-name", "label": "Name Z-A"},
                        {"value": "rating", "label": "Highest Rated"},
                        {"value": "-created_at", "label": "Newest First"},
                    ],
                },
            }
        )

        return context

    def _get_popular_ai_tags(self):
        """Get popular tags for AI tools"""
        tools = AITool.objects.filter(is_visible=True, tags__isnull=False)
        tag_counts = {}

        for tool in tools:
            if tool.tags:
                tags = tool.tags.split(",")
                for tag in tags:
                    tag = tag.strip()
                    if tag:
                        tag_counts[tag] = tag_counts.get(tag, 0) + 1

        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
        return [{"name": tag, "count": count} for tag, count in sorted_tags[:20]]


class ProjectCategoryView(ListView):
    """Projects category page"""

    model = Project
    template_name = "categories/projects.html"
    context_object_name = "projects"
    paginate_by = 12

    def get_queryset(self):
        queryset = Project.objects.filter(is_visible=True)

        # Apply filters
        project_filter = ProjectFilter(queryset)

        # Filter by status
        status = self.request.GET.getlist("status")
        if status:
            project_filter = project_filter.filter_by_status(status)

        # Filter by technologies
        tech = self.request.GET.get("tech")
        if tech:
            project_filter = project_filter.filter_by_tech_stack(tech)

        # Filter by difficulty
        min_difficulty = self.request.GET.get("min_difficulty")
        max_difficulty = self.request.GET.get("max_difficulty")
        if min_difficulty or max_difficulty:
            project_filter = project_filter.filter_by_difficulty(
                int(min_difficulty) if min_difficulty else None,
                int(max_difficulty) if max_difficulty else None,
            )

        # Filter by open source
        open_source_only = self.request.GET.get("open_source") == "true"
        project_filter = project_filter.filter_by_open_source(open_source_only)

        # Filter by featured
        featured_only = self.request.GET.get("featured") == "true"
        project_filter = project_filter.filter_by_featured(featured_only)

        # Sort
        sort_by = self.request.GET.get("sort", "-created_at")
        direction = "desc" if sort_by.startswith("-") else "asc"
        project_filter = project_filter.sort_by(sort_by.lstrip("-"), direction)

        return project_filter.get_queryset()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get project statistics
        stats = {
            "total_projects": Project.objects.filter(is_visible=True).count(),
            "completed_projects": Project.objects.filter(
                is_visible=True, status="completed"
            ).count(),
            "active_projects": Project.objects.filter(
                is_visible=True, status__in=["development", "testing"]
            ).count(),
            "open_source_projects": Project.objects.filter(
                is_visible=True, is_open_source=True
            ).count(),
        }

        # Get featured projects
        featured_projects = Project.objects.filter(
            is_visible=True, is_featured=True
        ).order_by("order")[:6]

        # Get popular technologies
        popular_tech = self._get_popular_technologies()

        # Get status distribution
        status_distribution = []
        for choice in Project.STATUS_CHOICES:
            count = Project.objects.filter(is_visible=True, status=choice[0]).count()
            if count > 0:
                status_distribution.append(
                    {"status": choice[0], "label": choice[1], "count": count}
                )

        context.update(
            {
                "stats": stats,
                "featured_projects": featured_projects,
                "popular_tech": popular_tech,
                "status_distribution": status_distribution,
                "applied_filters": {
                    "status": self.request.GET.getlist("status"),
                    "tech": self.request.GET.get("tech", ""),
                    "min_difficulty": self.request.GET.get("min_difficulty", ""),
                    "max_difficulty": self.request.GET.get("max_difficulty", ""),
                    "open_source": self.request.GET.get("open_source", ""),
                    "featured": self.request.GET.get("featured", ""),
                    "sort": self.request.GET.get("sort", "-created_at"),
                },
                "filter_options": {
                    "statuses": [
                        {"value": s[0], "label": s[1]} for s in Project.STATUS_CHOICES
                    ],
                    "difficulty_levels": [
                        {"value": 1, "label": "Kolay"},
                        {"value": 2, "label": "Orta"},
                        {"value": 3, "label": "Zor"},
                        {"value": 4, "label": "Uzman"},
                        {"value": 5, "label": "Master"},
                    ],
                    "sort_options": [
                        {"value": "-created_at", "label": "Newest First"},
                        {"value": "created_at", "label": "Oldest First"},
                        {"value": "title", "label": "Title A-Z"},
                        {"value": "-title", "label": "Title Z-A"},
                        {"value": "difficulty_level", "label": "Easiest First"},
                        {"value": "-difficulty_level", "label": "Hardest First"},
                        {"value": "-view_count", "label": "Most Popular"},
                    ],
                },
            }
        )

        return context

    def _get_popular_technologies(self):
        """Get popular technologies used in projects"""
        projects = Project.objects.filter(is_visible=True, tech_stack__isnull=False)
        tech_counts = {}

        for project in projects:
            if project.tech_stack:
                for tech in project.tech_stack:
                    tech = tech.strip()
                    if tech:
                        tech_counts[tech] = tech_counts.get(tech, 0) + 1

        sorted_tech = sorted(tech_counts.items(), key=lambda x: x[1], reverse=True)
        return [{"name": tech, "count": count} for tech, count in sorted_tech[:20]]


def category_api(request, category_type):
    """API endpoint for category data"""
    if not request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"error": "Invalid request"}, status=400)

    try:
        if category_type == "blog":
            categories = (
                BlogCategory.objects.filter(is_visible=True)
                .annotate(
                    post_count=Count("posts", filter=Q(posts__status="published"))
                )
                .values("name", "display_name", "post_count", "description")
            )

        elif category_type == "ai_tools":
            categories = []
            for choice in AITool.CATEGORY_CHOICES:
                count = AITool.objects.filter(
                    category=choice[0], is_visible=True
                ).count()
                categories.append(
                    {"name": choice[0], "display_name": choice[1], "count": count}
                )

        elif category_type == "projects":
            categories = []
            for choice in Project.STATUS_CHOICES:
                count = Project.objects.filter(
                    status=choice[0], is_visible=True
                ).count()
                categories.append(
                    {"name": choice[0], "display_name": choice[1], "count": count}
                )
        else:
            return JsonResponse({"error": "Invalid category type"}, status=400)

        return JsonResponse({"categories": list(categories), "total": len(categories)})

    except Exception as e:
        return JsonResponse(
            {"error": f"Error fetching categories: {str(e)}"}, status=500
        )
