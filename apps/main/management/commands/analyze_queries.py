"""
Management command to analyze database queries and identify N+1 patterns
Usage: python manage.py analyze_queries
"""

import time
from collections import Counter

from django.core.management.base import BaseCommand
from django.db import connection, reset_queries
from django.test.utils import override_settings
from django.utils import timezone

from apps.blog.models import Post
from apps.main.models import AITool, BlogPost, CybersecurityResource
from apps.portfolio.models import Admin, UserSession


class Command(BaseCommand):
    help = "Analyze database queries to identify N+1 patterns and slow queries"

    def add_arguments(self, parser):
        parser.add_argument(
            "--threshold",
            type=float,
            default=0.05,
            help="Query time threshold in seconds (default: 0.05)",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Show detailed query information",
        )

    @override_settings(DEBUG=True)
    def handle(self, *args, **options):  # noqa: C901
        threshold = options["threshold"]
        verbose = options["verbose"]

        self.stdout.write(self.style.SUCCESS("=" * 70))
        self.stdout.write(self.style.SUCCESS("📊 Database Query Analysis Report"))
        self.stdout.write(
            self.style.SUCCESS(
                f"🕐 Analysis Time: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
        )
        self.stdout.write(
            self.style.SUCCESS(f"⚡ Slow Query Threshold: {threshold * 1000:.2f}ms")
        )
        self.stdout.write(self.style.SUCCESS("=" * 70))
        self.stdout.write("")

        # Test scenarios
        test_scenarios = [
            (
                "Blog Posts List (Without Optimization)",
                self.test_blog_posts_unoptimized,
            ),
            ("Blog Posts List (With Optimization)", self.test_blog_posts_optimized),
            (
                "Admin Sessions (Without Optimization)",
                self.test_admin_sessions_unoptimized,
            ),
            ("Admin Sessions (With Optimization)", self.test_admin_sessions_optimized),
            ("AI Tools List", self.test_ai_tools),
        ]

        for scenario_name, test_func in test_scenarios:
            self.stdout.write(self.style.WARNING(f"\n🔍 Testing: {scenario_name}"))
            self.stdout.write("-" * 70)

            reset_queries()
            start_time = time.time()

            try:
                test_func()
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Error: {str(e)}"))
                continue

            end_time = time.time()
            total_time = end_time - start_time

            # Analyze queries
            queries = connection.queries
            query_count = len(queries)

            # Find duplicate queries (N+1 pattern)
            query_patterns = Counter(q["sql"] for q in queries)
            duplicates = {
                sql: count for sql, count in query_patterns.items() if count > 3
            }

            # Find slow queries
            slow_queries = [q for q in queries if float(q["time"]) > threshold]

            # Display summary
            self.stdout.write(f"📈 Total Queries: {query_count}")
            self.stdout.write(f"⏱️  Total Time: {total_time * 1000:.2f}ms")
            self.stdout.write(
                f"🐌 Slow Queries (>{threshold * 1000:.2f}ms): {len(slow_queries)}"
            )
            self.stdout.write(f"🔁 Duplicate Queries (N+1 Risk): {len(duplicates)}")

            if duplicates:
                self.stdout.write(
                    self.style.ERROR("\n⚠️  Potential N+1 Query Patterns Detected:")
                )
                for sql, count in sorted(
                    duplicates.items(), key=lambda x: x[1], reverse=True
                )[:5]:
                    self.stdout.write(f"   • Query repeated {count} times")
                    if verbose:
                        self.stdout.write(f"     SQL: {sql[:100]}...")

            if slow_queries:
                self.stdout.write(
                    self.style.ERROR(f"\n⚠️  Slow Queries (>{threshold * 1000:.2f}ms):")
                )
                for query in slow_queries[:5]:
                    self.stdout.write(
                        f"   • {float(query['time']) * 1000:.2f}ms - {query['sql'][:100]}..."
                    )

            # Performance rating
            if query_count <= 20 and len(slow_queries) == 0 and len(duplicates) == 0:
                self.stdout.write(self.style.SUCCESS("✅ Excellent: Well optimized!"))
            elif query_count <= 50 and len(slow_queries) < 3:
                self.stdout.write(
                    self.style.WARNING("⚠️  Good: Minor optimizations possible")
                )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        "❌ Needs Optimization: Consider using select_related/prefetch_related"
                    )
                )

        self.stdout.write(self.style.SUCCESS("\n" + "=" * 70))
        self.stdout.write(self.style.SUCCESS("📋 Analysis Complete!"))
        self.stdout.write(self.style.SUCCESS("=" * 70))

        # Recommendations
        self.stdout.write("\n💡 Optimization Recommendations:")
        self.stdout.write("   1. Use select_related() for ForeignKey relationships")
        self.stdout.write("   2. Use prefetch_related() for ManyToMany relationships")
        self.stdout.write("   3. Add database indexes for frequently queried fields")
        self.stdout.write("   4. Consider query caching for expensive operations")
        self.stdout.write("   5. Use only() or defer() to limit selected fields")
        self.stdout.write("")

    def test_blog_posts_unoptimized(self):
        """Test blog posts without optimization (demonstrates N+1)"""
        posts = Post.objects.filter(status="published")[:10]
        for post in posts:
            # This will trigger N+1 queries
            _ = post.author.name  # Extra query for each post

    def test_blog_posts_optimized(self):
        """Test blog posts with optimization"""
        posts = Post.objects.filter(status="published").select_related("author")[:10]
        for post in posts:
            _ = post.author.name  # No extra queries

    def test_admin_sessions_unoptimized(self):
        """Test admin sessions without optimization"""
        sessions = UserSession.objects.filter(is_active=True)[:10]
        for session in sessions:
            _ = session.user.name  # N+1 query

    def test_admin_sessions_optimized(self):
        """Test admin sessions with optimization"""
        sessions = UserSession.objects.filter(is_active=True).select_related("user")[
            :10
        ]
        for session in sessions:
            _ = session.user.name  # No extra queries

    def test_ai_tools(self):
        """Test AI tools query"""
        tools = AITool.objects.filter(is_visible=True)[:20]
        for tool in tools:
            _ = tool.name
