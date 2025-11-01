"""
Management command for cache warming strategies.
"""

import time

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.blog.models import Post
from apps.contact.models import ContactMessage
from apps.main.cache import cache_manager
from apps.main.models import AITool, CybersecurityResource, PersonalInfo, SocialLink


class Command(BaseCommand):
    help = "Warm up application caches with frequently accessed data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--type",
            type=str,
            choices=["all", "blog", "main", "api", "templates"],
            default="all",
            help="Type of cache to warm up",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force cache refresh even if data exists",
        )
        parser.add_argument(
            "--stats", action="store_true", help="Show cache statistics after warming"
        )
        parser.add_argument(
            "--timeout",
            type=int,
            default=1800,  # 30 minutes
            help="Cache timeout in seconds",
        )

    def handle(self, *args, **options):
        cache_type = options["type"]
        force_refresh = options["force"]
        show_stats = options["stats"]
        timeout = options["timeout"]

        self.stdout.write(self.style.SUCCESS("CACHE WARMING STARTED"))
        self.stdout.write("=" * 50)

        start_time = time.time()
        total_items = 0

        if cache_type in ["all", "blog"]:
            blog_items = self.warm_blog_cache(timeout, force_refresh)
            total_items += blog_items
            self.stdout.write(f"Blog caches warmed: {blog_items} items")

        if cache_type in ["all", "main"]:
            main_items = self.warm_main_cache(timeout, force_refresh)
            total_items += main_items
            self.stdout.write(f"Main caches warmed: {main_items} items")

        if cache_type in ["all", "api"]:
            api_items = self.warm_api_cache(timeout, force_refresh)
            total_items += api_items
            self.stdout.write(f"API caches warmed: {api_items} items")

        if cache_type in ["all", "templates"]:
            template_items = self.warm_template_cache(timeout, force_refresh)
            total_items += template_items
            self.stdout.write(f"Template caches warmed: {template_items} items")

        end_time = time.time()
        duration = end_time - start_time

        self.stdout.write("=" * 50)
        self.stdout.write(
            self.style.SUCCESS(
                f"CACHE WARMING COMPLETED: {total_items} items in {duration:.2f}s"
            )
        )

        if show_stats:
            self.show_cache_statistics()

    def warm_blog_cache(self, timeout, force_refresh):
        """Warm blog-related caches."""
        count = 0

        # Published posts
        cache_key = "blog_published_posts_recent"
        if force_refresh or not cache_manager.get(cache_key):
            posts = list(
                Post.objects.filter(status="published")
                .select_related("author")
                .order_by("-published_at")[:10]
            )
            cache_manager.set(cache_key, posts, timeout)
            count += len(posts)

        # Popular posts
        cache_key = "blog_popular_posts"
        if force_refresh or not cache_manager.get(cache_key):
            popular_posts = list(
                Post.objects.filter(status="published")
                .select_related("author")
                .order_by("-view_count")[:5]
            )
            cache_manager.set(cache_key, popular_posts, timeout)
            count += len(popular_posts)

        # Recent posts for home page
        cache_key = "home_recent_posts"
        if force_refresh or not cache_manager.get(cache_key):
            recent_posts = list(
                Post.objects.filter(status="published")
                .select_related("author")
                .order_by("-published_at")[:3]
            )
            cache_manager.set(cache_key, recent_posts, timeout)
            count += len(recent_posts)

        # Individual post caches for most viewed posts
        for post in Post.objects.filter(status="published", view_count__gt=0).order_by(
            "-view_count"
        )[:10]:
            cache_key = f"blog_post_{post.slug}"
            if force_refresh or not cache_manager.get(cache_key):
                post_data = {
                    "post": post,
                    "related_posts": post.get_related_posts(),
                    "reading_time": post.get_reading_time(),
                }
                cache_manager.set(cache_key, post_data, timeout)
                count += 1

        return count

    def warm_main_cache(self, timeout, force_refresh):
        """Warm main application caches."""
        count = 0

        # Personal information
        cache_key = "main_personal_info_visible"
        if force_refresh or not cache_manager.get(cache_key):
            personal_info = list(
                PersonalInfo.objects.filter(is_visible=True).order_by("order")
            )
            cache_manager.set(cache_key, personal_info, timeout)
            count += len(personal_info)

        # Social links
        cache_key = "main_social_links_visible"
        if force_refresh or not cache_manager.get(cache_key):
            social_links = list(
                SocialLink.objects.filter(is_visible=True).order_by("order")
            )
            cache_manager.set(cache_key, social_links, timeout)
            count += len(social_links)

        # Featured AI tools
        cache_key = "main_ai_tools_featured"
        if force_refresh or not cache_manager.get(cache_key):
            ai_tools = list(
                AITool.objects.filter(is_featured=True, is_visible=True).order_by(
                    "-rating", "name"
                )
            )
            cache_manager.set(cache_key, ai_tools, timeout)
            count += len(ai_tools)

        # Urgent security resources
        cache_key = "main_security_urgent"
        if force_refresh or not cache_manager.get(cache_key):
            security_resources = list(
                CybersecurityResource.objects.filter(
                    is_urgent=True, is_visible=True
                ).order_by("-severity_level", "-created_at")
            )
            cache_manager.set(cache_key, security_resources, timeout)
            count += len(security_resources)

        # Contact message stats (for admin)
        cache_key = "main_contact_stats"
        if force_refresh or not cache_manager.get(cache_key):
            stats = {
                "total_messages": ContactMessage.objects.count(),
                "unread_messages": ContactMessage.objects.filter(is_read=False).count(),
                "recent_messages": ContactMessage.objects.filter(
                    created_at__gte=timezone.now() - timezone.timedelta(days=7)
                ).count(),
            }
            cache_manager.set(cache_key, stats, timeout)
            count += 1

        return count

    def warm_api_cache(self, timeout, force_refresh):
        """Warm API response caches."""
        count = 0

        # API endpoints data
        api_endpoints = [
            (
                "api_posts_published",
                lambda: Post.objects.filter(status="published")[:20],
            ),
            ("api_personal_info", lambda: PersonalInfo.objects.filter(is_visible=True)),
            ("api_social_links", lambda: SocialLink.objects.filter(is_visible=True)),
            (
                "api_ai_tools_featured",
                lambda: AITool.objects.filter(is_featured=True, is_visible=True),
            ),
        ]

        for cache_key, query_func in api_endpoints:
            if force_refresh or not cache_manager.get(cache_key):
                try:
                    data = list(query_func())
                    cache_manager.set(cache_key, data, timeout)
                    count += len(data) if data else 1
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f"Failed to warm {cache_key}: {e}")
                    )

        return count

    def warm_template_cache(self, timeout, force_refresh):
        """Warm template fragment caches."""
        count = 0

        # Template fragments commonly used
        template_fragments = [
            ("home_hero_section", "components/home/hero.html", {}),
            ("home_about_section", "components/home/about.html", {}),
            ("footer_social_links", "components/footer/social_links.html", {}),
            ("header_navigation", "components/header/navigation.html", {}),
        ]

        for cache_key, template_name, context in template_fragments:
            if force_refresh or not cache_manager.get(cache_key):
                try:
                    from django.template.loader import render_to_string

                    rendered_content = render_to_string(template_name, context)
                    cache_manager.set(cache_key, rendered_content, timeout)
                    count += 1
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Failed to warm template {template_name}: {e}"
                        )
                    )

        return count

    def show_cache_statistics(self):
        """Display cache statistics."""
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write("CACHE STATISTICS")
        self.stdout.write("=" * 50)

        stats = cache_manager.get_stats()

        self.stdout.write(f"Cache Hits: {stats['hits']}")
        self.stdout.write(f"Cache Misses: {stats['misses']}")
        self.stdout.write(f"Hit Ratio: {stats['hit_ratio']}%")
        self.stdout.write(f"Total Operations: {stats['total_operations']}")
        self.stdout.write(f"Cache Sets: {stats['sets']}")
        self.stdout.write(f"Cache Deletes: {stats['deletes']}")
        self.stdout.write(f"Errors: {stats['errors']}")
        self.stdout.write(f"Uptime: {stats['uptime_seconds']:.0f} seconds")

        if stats["recent_errors"]:
            self.stdout.write("\nRecent Errors:")
            for error in stats["recent_errors"]:
                self.stdout.write(f"  {error['key']}: {error['error']}")

        # Show cache backend info
        try:
            from django.conf import settings

            cache_backend = settings.CACHES["default"]["BACKEND"]
            self.stdout.write(f"\nCache Backend: {cache_backend}")

            if "redis" in cache_backend.lower():
                self.stdout.write("Redis Configuration: ✓")
            else:
                self.stdout.write("Redis Configuration: ✗ (Using fallback cache)")

        except Exception as e:
            self.stdout.write(f"Cache Backend Info: Error - {e}")

    def warm_priority_caches(self):
        """Warm high-priority caches that should always be available."""
        priority_caches = [
            ("home_page_data", self.get_home_page_data),
            ("site_navigation", self.get_navigation_data),
            ("footer_data", self.get_footer_data),
        ]

        for cache_key, data_func in priority_caches:
            try:
                data = data_func()
                cache_manager.set(cache_key, data, 3600)  # 1 hour timeout
                self.stdout.write(f"Priority cache warmed: {cache_key}")
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Failed to warm priority cache {cache_key}: {e}")
                )

    def get_home_page_data(self):
        """Get home page data for caching."""
        return {
            "personal_info": PersonalInfo.objects.filter(is_visible=True).order_by(
                "order"
            ),
            "social_links": SocialLink.objects.filter(is_visible=True).order_by(
                "order"
            ),
            "recent_posts": Post.objects.filter(status="published").select_related(
                "author"
            )[:3],
            "featured_tools": AITool.objects.filter(is_featured=True, is_visible=True)[
                :6
            ],
        }

    def get_navigation_data(self):
        """Get navigation data for caching."""
        return {
            "main_nav_items": [
                {"name": "Home", "url": "/", "active": False},
                {"name": "About", "url": "/about/", "active": False},
                {"name": "Blog", "url": "/blog/", "active": False},
                {"name": "Tools", "url": "/tools/", "active": False},
                {"name": "Contact", "url": "/contact/", "active": False},
            ]
        }

    def get_footer_data(self):
        """Get footer data for caching."""
        return {
            "social_links": SocialLink.objects.filter(is_visible=True).order_by(
                "order"
            ),
            "copyright_year": timezone.now().year,
            "quick_links": [
                {"name": "Privacy Policy", "url": "/privacy/"},
                {"name": "Terms of Service", "url": "/terms/"},
                {"name": "Contact", "url": "/contact/"},
            ],
        }
