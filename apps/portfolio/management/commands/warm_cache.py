"""
CACHE WARMING MANAGEMENT COMMAND
================================

Django management command to pre-warm cache with frequently accessed data.
Prevents cache misses for critical application data and improves user experience.

FEATURES:
- Pre-loads essential data into cache
- Configurable cache warming strategies
- Performance monitoring during warming
- Selective warming by data type
- Error handling and logging

USAGE:
    python manage.py warm_cache                    # Warm all cache
    python manage.py warm_cache --type home        # Warm home page data only
    python manage.py warm_cache --type blog        # Warm blog data only
    python manage.py warm_cache --force            # Force refresh existing cache
    python manage.py warm_cache --verbose          # Detailed output
"""

import time
from typing import Dict, Optional

from django.core.cache import cache
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.blog.models import Post
from apps.main.cache_utils import CacheManager
from apps.main.models import BlogCategory, PersonalInfo, SocialLink
from apps.tools.models import Tool


class Command(BaseCommand):
    """
    Management command to warm up application cache with frequently accessed data.
    """

    help = "Warm up application cache with frequently accessed data"

    def add_arguments(self, parser):
        """Add command line arguments"""
        parser.add_argument(
            "--type",
            type=str,
            choices=["all", "home", "blog", "tools", "personal"],
            default="all",
            help="Type of cache data to warm (default: all)",
        )

        parser.add_argument(
            "--force", action="store_true", help="Force refresh existing cache entries"
        )

        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Enable verbose output with timing information",
        )

        parser.add_argument(
            "--timeout",
            type=int,
            default=None,
            help="Cache timeout in seconds (uses default if not specified)",
        )

    def handle(self, *args, **options):
        """Main command handler"""
        start_time = time.time()
        warming_type = options["type"]
        force_refresh = options["force"]
        verbose = options["verbose"]
        custom_timeout = options.get("timeout")

        self.stdout.write(
            self.style.HTTP_INFO(
                f"Starting cache warming process - Type: {warming_type}"
            )
        )

        if verbose:
            self.stdout.write(f"Force refresh: {force_refresh}")
            self.stdout.write(f'Custom timeout: {custom_timeout or "Using defaults"}')

        try:
            # Track statistics
            stats = {"warmed": 0, "skipped": 0, "errors": 0, "total_time": 0}

            # Execute warming based on type
            if warming_type == "all" or warming_type == "home":
                self._warm_home_data(force_refresh, custom_timeout, verbose, stats)

            if warming_type == "all" or warming_type == "blog":
                self._warm_blog_data(force_refresh, custom_timeout, verbose, stats)

            if warming_type == "all" or warming_type == "tools":
                self._warm_tools_data(force_refresh, custom_timeout, verbose, stats)

            if warming_type == "all" or warming_type == "personal":
                self._warm_personal_data(force_refresh, custom_timeout, verbose, stats)

            # Display results
            total_time = time.time() - start_time
            stats["total_time"] = total_time

            self.stdout.write(
                self.style.SUCCESS("\nCache warming completed successfully!")
            )

            self.stdout.write("Statistics:")
            self.stdout.write(f"  - Entries warmed: {stats['warmed']}")
            self.stdout.write(f"  - Entries skipped: {stats['skipped']}")
            self.stdout.write(f"  - Errors encountered: {stats['errors']}")
            self.stdout.write(f"  - Total time: {total_time:.2f}s")

            if verbose and stats["warmed"] > 0:
                avg_time = total_time / stats["warmed"]
                self.stdout.write(f"  - Average time per entry: {avg_time:.3f}s")

        except Exception as e:
            raise CommandError(f"Cache warming failed: {str(e)}")

    def _warm_home_data(
        self, force: bool, timeout: Optional[int], verbose: bool, stats: Dict
    ):
        """Warm cache data for home page"""
        if verbose:
            self.stdout.write("Warming home page data...")

        warming_functions = [
            (
                "personal_info_visible",
                self._get_personal_info,
                CacheManager.TIMEOUTS["long"],
            ),
            (
                "social_links_visible",
                self._get_social_links,
                CacheManager.TIMEOUTS["long"],
            ),
            ("recent_posts", self._get_recent_posts, CacheManager.TIMEOUTS["medium"]),
            (
                "featured_tools",
                self._get_featured_tools,
                CacheManager.TIMEOUTS["medium"],
            ),
            (
                "featured_blog_categories",
                self._get_featured_blog_categories,
                CacheManager.TIMEOUTS["medium"],
            ),
        ]

        for key_suffix, func, default_timeout in warming_functions:
            self._warm_single_entry(
                f"home_{key_suffix}",
                func,
                timeout or default_timeout,
                force,
                verbose,
                stats,
            )

    def _warm_blog_data(
        self, force: bool, timeout: Optional[int], verbose: bool, stats: Dict
    ):
        """Warm cache data for blog"""
        if verbose:
            self.stdout.write("Warming blog data...")

        warming_functions = [
            (
                "published_posts",
                self._get_published_posts,
                CacheManager.TIMEOUTS["medium"],
            ),
            ("popular_posts", self._get_popular_posts, CacheManager.TIMEOUTS["medium"]),
            (
                "blog_categories",
                self._get_blog_categories,
                CacheManager.TIMEOUTS["long"],
            ),
        ]

        for key_suffix, func, default_timeout in warming_functions:
            self._warm_single_entry(
                f"blog_{key_suffix}",
                func,
                timeout or default_timeout,
                force,
                verbose,
                stats,
            )

    def _warm_tools_data(
        self, force: bool, timeout: Optional[int], verbose: bool, stats: Dict
    ):
        """Warm cache data for tools"""
        if verbose:
            self.stdout.write("Warming tools data...")

        warming_functions = [
            ("visible_tools", self._get_visible_tools, CacheManager.TIMEOUTS["medium"]),
            (
                "featured_tools",
                self._get_featured_tools,
                CacheManager.TIMEOUTS["medium"],
            ),
            (
                "tools_by_category",
                self._get_tools_by_category,
                CacheManager.TIMEOUTS["medium"],
            ),
        ]

        for key_suffix, func, default_timeout in warming_functions:
            self._warm_single_entry(
                f"tools_{key_suffix}",
                func,
                timeout or default_timeout,
                force,
                verbose,
                stats,
            )

    def _warm_personal_data(
        self, force: bool, timeout: Optional[int], verbose: bool, stats: Dict
    ):
        """Warm cache data for personal page"""
        if verbose:
            self.stdout.write("Warming personal data...")

        warming_functions = [
            (
                "personal_info_all",
                self._get_personal_info_all,
                CacheManager.TIMEOUTS["long"],
            ),
            ("social_links_all", self._get_social_links, CacheManager.TIMEOUTS["long"]),
        ]

        for key_suffix, func, default_timeout in warming_functions:
            self._warm_single_entry(
                f"personal_{key_suffix}",
                func,
                timeout or default_timeout,
                force,
                verbose,
                stats,
            )

    def _warm_single_entry(
        self,
        cache_key: str,
        data_func,
        timeout: int,
        force: bool,
        verbose: bool,
        stats: Dict,
    ):
        """Warm a single cache entry"""
        start_time = time.time()

        try:
            # Check if already cached (unless forcing refresh)
            if not force and cache.get(cache_key) is not None:
                if verbose:
                    self.stdout.write(f"  [SKIP] Skipped (already cached): {cache_key}")
                stats["skipped"] += 1
                return

            # Fetch and cache data
            data = data_func()
            cache.set(cache_key, data, timeout)

            elapsed = time.time() - start_time
            stats["warmed"] += 1

            if verbose:
                data_size = len(data) if hasattr(data, "__len__") else "N/A"
                self.stdout.write(
                    f"  [OK] Cached: {cache_key} "
                    f"(size: {data_size}, time: {elapsed:.3f}s, timeout: {timeout}s)"
                )

        except Exception as e:
            stats["errors"] += 1
            self.stdout.write(
                self.style.ERROR(f"  [ERROR] Error caching {cache_key}: {str(e)}")
            )

    # Data fetching functions
    def _get_personal_info(self):
        """Get visible personal info"""
        return list(
            PersonalInfo.objects.filter(is_visible=True).order_by("order", "key")
        )

    def _get_personal_info_all(self):
        """Get all personal info for personal page"""
        return list(
            PersonalInfo.objects.filter(
                is_visible=True,
                key__in=["about", "skills", "experience", "education", "bio"],
            ).order_by("order", "key")
        )

    def _get_social_links(self):
        """Get visible social links"""
        return list(
            SocialLink.objects.filter(is_visible=True).order_by("order", "platform")
        )

    def _get_recent_posts(self):
        """Get recent published posts"""
        return list(
            Post.objects.select_related("author")
            .filter(status="published", published_at__lte=timezone.now())
            .order_by("-published_at")[:5]
        )

    def _get_published_posts(self):
        """Get all published posts"""
        return list(
            Post.objects.select_related("author")
            .filter(status="published", published_at__lte=timezone.now())
            .order_by("-published_at")[:20]
        )

    def _get_popular_posts(self):
        """Get popular posts by view count"""
        return list(
            Post.objects.select_related("author")
            .filter(status="published", published_at__lte=timezone.now())
            .order_by("-views", "-published_at")[:10]
        )

    def _get_featured_tools(self):
        """Get featured tools"""
        return list(
            Tool.objects.filter(is_favorite=True, is_visible=True).order_by(
                "category", "title"
            )[:6]
        )

    def _get_visible_tools(self):
        """Get all visible tools"""
        return list(
            Tool.objects.filter(is_visible=True).order_by(
                "-is_favorite", "order", "-created_at"
            )
        )

    def _get_tools_by_category(self):
        """Get tools grouped by category"""
        tools_by_category = {}

        if hasattr(Tool, "CATEGORY_CHOICES"):
            for category_code, category_name in Tool.CATEGORY_CHOICES:
                tools = Tool.objects.filter(
                    category=category_code, is_visible=True
                ).order_by("order", "title")

                if tools.exists():
                    tools_by_category[category_name] = list(tools)

        return tools_by_category

    def _get_blog_categories(self):
        """Get blog categories"""
        return list(
            BlogCategory.objects.filter(is_visible=True).order_by("order", "name")
        )

    def _get_featured_blog_categories(self):
        """Get featured blog categories"""
        return list(
            BlogCategory.objects.filter(is_visible=True).order_by("order", "name")[:6]
        )
