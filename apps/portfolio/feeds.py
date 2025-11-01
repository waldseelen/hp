from django.contrib.syndication.views import Feed
from django.urls import reverse
from django.utils import timezone
from django.utils.feedgenerator import Rss201rev2Feed
from django.utils.html import strip_tags

from apps.blog.models import Post

from .models import Project


class LatestPostsFeed(Feed):
    """
    RSS feed for latest blog posts
    """

    title = "Portfolio Blog"
    link = "/blog/"
    description = "En son blog yazıları ve güncellemeler"
    feed_type = Rss201rev2Feed

    def items(self):
        return Post.objects.filter(
            status="published", published_at__lte=timezone.now()
        ).order_by("-published_at")[:20]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        # Return excerpt if available, otherwise first 200 chars of content
        if item.excerpt:
            return item.excerpt
        elif item.content:
            # Strip HTML tags and get plain text for RSS
            plain_text = strip_tags(item.content)
            return plain_text[:200] + "..." if len(plain_text) > 200 else plain_text
        return "Blog yazısı"

    def item_pubdate(self, item):
        return item.published_at

    def item_link(self, item):
        return reverse("blog:detail", args=[item.slug])

    def item_guid(self, item):
        return f"blog-post-{item.id}-{item.slug}"

    def item_categories(self, item):
        if hasattr(item, "tags") and item.tags:
            return item.tags if isinstance(item.tags, list) else []
        return []


class LatestProjectsFeed(Feed):
    """
    RSS feed for latest projects
    """

    title = "Portfolio Projects"
    link = "/projects/"
    description = "En son projeler ve güncellemeler"
    feed_type = Rss201rev2Feed

    def items(self):
        return Project.objects.filter(is_visible=True).order_by("-updated_at")[:10]

    def item_title(self, item):
        return f"{item.title} - {item.get_status_display()}"

    def item_description(self, item):
        description = item.description
        if item.tech_stack:
            tech_list = ", ".join(item.tech_stack)
            description += f"\n\nKullanılan teknolojiler: {tech_list}"

        if item.progress_percentage:
            description += f"\n\nİlerleme: %{item.progress_percentage}"

        return description

    def item_pubdate(self, item):
        return item.updated_at

    def item_link(self, item):
        return reverse("main:project_detail", args=[item.slug])

    def item_guid(self, item):
        return f"project-{item.id}-{item.slug}"

    def item_categories(self, item):
        categories = [item.get_status_display()]
        if item.tech_stack:
            categories.extend(item.tech_stack)
        return categories


class CombinedFeed(Feed):
    """
    Combined RSS feed for both blog posts and projects
    """

    title = "Portfolio - Blog & Projects"
    link = "/"
    description = "Blog yazıları ve projeler - tam güncelleme akışı"
    feed_type = Rss201rev2Feed

    def items(self):
        # Get recent posts and projects
        recent_posts = Post.objects.filter(
            status="published", published_at__lte=timezone.now()
        ).order_by("-published_at")[:10]

        recent_projects = Project.objects.filter(is_visible=True).order_by(
            "-updated_at"
        )[:5]

        # Combine and sort by date
        items = []

        for post in recent_posts:
            items.append(
                {
                    "type": "post",
                    "object": post,
                    "date": post.published_at,
                    "title": post.title,
                    "description": (
                        post.excerpt if post.excerpt else post.content[:200] + "..."
                    ),
                    "link": reverse("blog:detail", args=[post.slug]),
                    "guid": f"post-{post.id}",
                    "categories": (
                        post.tags if hasattr(post, "tags") and post.tags else []
                    ),
                }
            )

        for project in recent_projects:
            items.append(
                {
                    "type": "project",
                    "object": project,
                    "date": project.updated_at,
                    "title": f"[Proje] {project.title} - {project.get_status_display()}",
                    "description": project.description,
                    "link": reverse("main:project_detail", args=[project.slug]),
                    "guid": f"project-{project.id}",
                    "categories": [project.get_status_display()]
                    + (project.tech_stack if project.tech_stack else []),
                }
            )

        # Sort by date (most recent first)
        items.sort(key=lambda x: x["date"], reverse=True)
        return items[:15]

    def item_title(self, item):
        return item["title"]

    def item_description(self, item):
        return item["description"]

    def item_pubdate(self, item):
        return item["date"]

    def item_link(self, item):
        return item["link"]

    def item_guid(self, item):
        return item["guid"]

    def item_categories(self, item):
        return item["categories"]
