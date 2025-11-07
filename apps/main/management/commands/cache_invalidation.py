"""
Management command for cache invalidation and monitoring
Usage: python manage.py cache_invalidation [--action clear|stats|warm]
"""

from django.core.cache import cache, caches
from django.core.management.base import BaseCommand
from django.db.models import Count
from django.utils import timezone

from apps.blog.models import Post
from apps.main.models import AITool
from apps.main.models import BlogPost as MainBlogPost
from apps.main.models import CybersecurityResource
from apps.portfolio.models import Admin


class Command(BaseCommand):
    help = "Manage cache invalidation, monitoring and warming"

    def add_arguments(self, parser):
        parser.add_argument(
            "--action",
            type=str,
            default="stats",
            choices=["clear", "stats", "warm", "invalidate"],
            help="Action to perform: clear, stats, warm, or invalidate",
        )
        parser.add_argument(
            "--cache",
            type=str,
            default="default",
            help="Cache alias to use (default, query_cache, api_cache, template_cache)",
        )
        parser.add_argument(
            "--pattern",
            type=str,
            help="Key pattern for invalidation (supports wildcards)",
        )

    def handle(self, *args, **options):
        action = options["action"]
        cache_alias = options["cache"]
        pattern = options.get("pattern")

        self.stdout.write(self.style.SUCCESS("=" * 70))
        self.stdout.write(self.style.SUCCESS(f"🗄️  Cache Management - {action.upper()}"))
        self.stdout.write(self.style.SUCCESS(f"📦 Cache Alias: {cache_alias}"))
        self.stdout.write(
            self.style.SUCCESS(
                f"🕐 Time: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
        )
        self.stdout.write(self.style.SUCCESS("=" * 70))
        self.stdout.write("")

        selected_cache = caches[cache_alias]

        if action == "clear":
            self.clear_cache(selected_cache, cache_alias)
        elif action == "stats":
            self.show_stats(selected_cache, cache_alias)
        elif action == "warm":
            self.warm_cache(selected_cache)
        elif action == "invalidate":
            self.invalidate_pattern(selected_cache, pattern)

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 70))
        self.stdout.write(self.style.SUCCESS("✅ Operation Complete!"))
        self.stdout.write(self.style.SUCCESS("=" * 70))

    def clear_cache(self, cache_backend, cache_name):
        """Clear entire cache"""
        self.stdout.write(self.style.WARNING(f"🗑️  Clearing {cache_name} cache..."))
        cache_backend.clear()
        self.stdout.write(
            self.style.SUCCESS(f"✅ {cache_name} cache cleared successfully!")
        )

    def show_stats(self, cache_backend, cache_name):
        """Show cache statistics (if supported by backend)"""
        self.stdout.write(self.style.SUCCESS(f"📊 Cache Statistics for {cache_name}:"))
        self.stdout.write("")

        try:
            # Try to get Redis-specific stats
            if hasattr(cache_backend, "_cache"):
                client = cache_backend._cache.get_client()
                info = client.info("stats")

                self.stdout.write("Redis Stats:")
                self.stdout.write(
                    f"   • Total Connections: {info.get('total_connections_received', 'N/A')}"
                )
                self.stdout.write(
                    f"   • Commands Processed: {info.get('total_commands_processed', 'N/A')}"
                )
                self.stdout.write(
                    f"   • Keyspace Hits: {info.get('keyspace_hits', 'N/A')}"
                )
                self.stdout.write(
                    f"   • Keyspace Misses: {info.get('keyspace_misses', 'N/A')}"
                )

                hits = int(info.get("keyspace_hits", 0))
                misses = int(info.get("keyspace_misses", 0))
                total = hits + misses

                if total > 0:
                    hit_rate = (hits / total) * 100
                    self.stdout.write(f"   • Hit Rate: {hit_rate:.2f}%")

                    if hit_rate >= 80:
                        self.stdout.write(
                            self.style.SUCCESS(f"   ✅ Excellent hit rate!")
                        )
                    elif hit_rate >= 60:
                        self.stdout.write(
                            self.style.WARNING(f"   ⚠️  Good hit rate, can be improved")
                        )
                    else:
                        self.stdout.write(
                            self.style.ERROR(f"   ❌ Low hit rate, needs optimization")
                        )

                # Memory info
                memory_info = client.info("memory")
                used_memory = memory_info.get("used_memory_human", "N/A")
                self.stdout.write(f"   • Memory Used: {used_memory}")

        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f"⚠️  Could not retrieve detailed stats: {str(e)}")
            )
            self.stdout.write(
                "   Cache is operational but stats unavailable (may be using local memory cache)"
            )

    def warm_cache(self, cache_backend):  # noqa: C901
        """Warm cache with frequently accessed data"""
        self.stdout.write(
            self.style.SUCCESS("🔥 Warming cache with frequently accessed data...")
        )
        self.stdout.write("")

        # Warm blog posts
        try:
            posts = Post.objects.filter(status="published").select_related("author")[
                :20
            ]

            for post in posts:
                cache_key = f"blog:post:{post.slug}"
                cache_backend.set(
                    cache_key,
                    {
                        "id": post.id,
                        "title": post.title,
                        "excerpt": post.excerpt,
                        "author": post.author.name,
                        "published_at": (
                            post.published_at.isoformat() if post.published_at else None
                        ),
                    },
                    timeout=3600,
                )

            self.stdout.write(
                self.style.SUCCESS(f"   ✅ Cached {len(posts)} blog posts")
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"   ❌ Error caching blog posts: {str(e)}")
            )

        # Warm AI tools
        try:
            tools = AITool.objects.filter(is_visible=True)[:50]
            cache_key = "ai:tools:list"
            cache_backend.set(cache_key, list(tools.values()), timeout=7200)

            self.stdout.write(self.style.SUCCESS(f"   ✅ Cached {len(tools)} AI tools"))
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"   ❌ Error caching AI tools: {str(e)}")
            )

        # Warm popular tags
        try:
            from django.db.models import Q

            # Get all posts with tags
            posts_with_tags = Post.objects.filter(
                Q(tags__isnull=False) & ~Q(tags=[])
            ).values_list("tags", flat=True)

            # Count tag occurrences
            tag_counts = {}
            for tags in posts_with_tags:
                if tags:
                    for tag in tags:
                        tag_counts[tag] = tag_counts.get(tag, 0) + 1

            # Cache top 20 tags
            popular_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[
                :20
            ]
            cache_backend.set("blog:popular_tags", popular_tags, timeout=7200)

            self.stdout.write(
                self.style.SUCCESS(f"   ✅ Cached {len(popular_tags)} popular tags")
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ Error caching tags: {str(e)}"))

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("🔥 Cache warming complete!"))

    def invalidate_pattern(self, cache_backend, pattern):
        """Invalidate cache keys matching pattern"""
        if not pattern:
            self.stdout.write(self.style.ERROR("❌ Pattern required for invalidation"))
            return

        self.stdout.write(
            self.style.WARNING(f"🗑️  Invalidating keys matching pattern: {pattern}")
        )

        try:
            if hasattr(cache_backend, "delete_pattern"):
                # Redis supports pattern deletion
                deleted = cache_backend.delete_pattern(pattern)
                self.stdout.write(self.style.SUCCESS(f"✅ Deleted {deleted} keys"))
            else:
                self.stdout.write(
                    self.style.WARNING(
                        "⚠️  Pattern deletion not supported by this cache backend"
                    )
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error invalidating cache: {str(e)}")
            )
