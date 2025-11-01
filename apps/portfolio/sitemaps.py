from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.utils import timezone

from apps.blog.models import Post
from apps.tools.models import Tool

from .models import AITool, CybersecurityResource, UsefulResource


class StaticViewSitemap(Sitemap):
    """Sitemap for static pages"""

    priority = 0.8
    changefreq = "monthly"

    def items(self):
        return [
            "home",
            "main:personal",
            "main:projects",
            "main:ai",
            "main:cybersecurity",
            "main:useful",
            "main:music",
            "contact:form",
            "blog:list",
        ]

    def location(self, item):
        if item == "home":
            return "/"
        return reverse(item)

    def lastmod(self, item):
        # Return current time for dynamic pages
        if item in ["main:projects", "blog:list"]:
            return timezone.now().date()
        return None


class BlogPostSitemap(Sitemap):
    """Sitemap for blog posts"""

    changefreq = "weekly"
    priority = 0.9

    def items(self):
        return Post.objects.filter(
            status="published", published_at__lte=timezone.now()
        ).order_by("-published_at")

    def lastmod(self, obj):
        return obj.updated_at.date() if obj.updated_at else obj.published_at.date()

    def location(self, obj):
        return reverse("blog:detail", args=[obj.slug])


class ProjectSitemap(Sitemap):
    """Sitemap for tools/projects"""

    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Tool.objects.filter(is_visible=True).order_by("-updated_at")

    def lastmod(self, obj):
        return obj.updated_at.date()

    def location(self, obj):
        return reverse("tools:detail", args=[obj.slug])


class ResourceSitemap(Sitemap):
    """Sitemap for various resources (AI tools, cybersecurity, useful)"""

    changefreq = "monthly"
    priority = 0.6

    def items(self):
        resources = []

        # Add AI tools
        ai_tools = AITool.objects.all().order_by("-updated_at")[
            :100
        ]  # Limit for performance
        for tool in ai_tools:
            resources.append(
                {
                    "type": "ai_tool",
                    "obj": tool,
                    "lastmod": tool.updated_at.date(),
                    "url": f"/ai/#{tool.id}",  # Assuming anchor links
                }
            )

        # Add cybersecurity resources
        cyber_resources = CybersecurityResource.objects.filter(
            is_visible=True
        ).order_by("-updated_at")[:100]
        for resource in cyber_resources:
            resources.append(
                {
                    "type": "cyber_resource",
                    "obj": resource,
                    "lastmod": resource.updated_at.date(),
                    "url": f"/cybersecurity/#{resource.id}",
                }
            )

        # Add useful resources
        useful_resources = UsefulResource.objects.filter(is_visible=True).order_by(
            "-updated_at"
        )[:100]
        for resource in useful_resources:
            resources.append(
                {
                    "type": "useful_resource",
                    "obj": resource,
                    "lastmod": resource.updated_at.date(),
                    "url": f"/useful/#{resource.id}",
                }
            )

        return resources

    def lastmod(self, item):
        return item["lastmod"]

    def location(self, item):
        return item["url"]


class FeedSitemap(Sitemap):
    """Sitemap for RSS feeds"""

    changefreq = "daily"
    priority = 0.5

    def items(self):
        return [
            "main:combined_feed",
            "main:blog_feed",
            "main:projects_feed",
        ]

    def location(self, item):
        return reverse(item)

    def lastmod(self, item):
        return timezone.now().date()


# Sitemap registry
sitemaps = {
    "static": StaticViewSitemap,
    "blog": BlogPostSitemap,
    "projects": ProjectSitemap,
    "resources": ResourceSitemap,
    "feeds": FeedSitemap,
}
