"""
Management command to analyze database performance and query optimization.
"""

import time

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection
from django.test.utils import override_settings

from apps.blog.models import Post
from apps.contact.models import ContactMessage
from apps.main.models import AITool, PersonalInfo, SocialLink


class Command(BaseCommand):
    help = "Analyze database performance and query optimization"

    def add_arguments(self, parser):
        parser.add_argument(
            "--test-queries",
            action="store_true",
            help="Run performance tests on common queries",
        )
        parser.add_argument(
            "--check-indexes",
            action="store_true",
            help="Check existing database indexes",
        )
        parser.add_argument(
            "--verbose", action="store_true", help="Show detailed query information"
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("DATABASE PERFORMANCE ANALYSIS"))
        self.stdout.write("=" * 60)

        if options.get("check_indexes"):
            self.check_database_indexes()

        if options.get("test_queries"):
            self.test_query_performance(verbose=options.get("verbose"))

        self.analyze_model_queries()

    def check_database_indexes(self):
        """Check existing database indexes."""
        self.stdout.write("\n" + "=" * 40)
        self.stdout.write("DATABASE INDEXES ANALYSIS")
        self.stdout.write("=" * 40)

        with connection.cursor() as cursor:
            # Get index information for SQLite
            if "sqlite" in settings.DATABASES["default"]["ENGINE"]:
                cursor.execute(
                    """
                    SELECT name, sql
                    FROM sqlite_master
                    WHERE type = 'index'
                    AND name NOT LIKE 'sqlite_%'
                    ORDER BY name
                """
                )

                indexes = cursor.fetchall()
                self.stdout.write(f"Found {len(indexes)} custom indexes:")

                for name, sql in indexes:
                    if sql:  # Skip auto-indexes without SQL
                        self.stdout.write(f"  [INDEX] {name}")
                        if sql.lower().startswith("create"):
                            # Extract table name from SQL
                            parts = sql.split()
                            if "ON" in parts:
                                on_index = parts.index("ON")
                                if on_index + 1 < len(parts):
                                    table_name = parts[on_index + 1].split("(")[0]
                                    self.stdout.write(f"    Table: {table_name}")

            else:
                # PostgreSQL index query
                cursor.execute(
                    """
                    SELECT
                        schemaname,
                        tablename,
                        indexname,
                        indexdef
                    FROM pg_indexes
                    WHERE schemaname = 'public'
                    ORDER BY tablename, indexname
                """
                )

                indexes = cursor.fetchall()
                self.stdout.write(f"Found {len(indexes)} indexes:")

                current_table = None
                for schema, table, name, definition in indexes:
                    if table != current_table:
                        self.stdout.write(f"\n  TABLE: {table}")
                        current_table = table
                    self.stdout.write(f"    [INDEX] {name}")

    def test_query_performance(self, verbose=False):
        """Test performance of common queries."""
        self.stdout.write("\n" + "=" * 40)
        self.stdout.write("QUERY PERFORMANCE TESTING")
        self.stdout.write("=" * 40)

        queries_to_test = [
            {
                "name": "Blog Posts - Published Only",
                "query": lambda: list(
                    Post.objects.filter(status="published").order_by("-published_at")[
                        :10
                    ]
                ),
                "description": "Get latest 10 published blog posts",
            },
            {
                "name": "Blog Posts - By Author",
                "query": lambda: list(
                    Post.objects.filter(author_id=1, status="published").order_by(
                        "-published_at"
                    )[:5]
                ),
                "description": "Get posts by specific author",
            },
            {
                "name": "Blog Posts - Popular Posts",
                "query": lambda: list(
                    Post.objects.filter(status="published").order_by("-view_count")[:5]
                ),
                "description": "Get most popular posts",
            },
            {
                "name": "Personal Info - Visible Only",
                "query": lambda: list(
                    PersonalInfo.objects.filter(is_visible=True).order_by("order")
                ),
                "description": "Get visible personal information",
            },
            {
                "name": "Social Links - Visible Only",
                "query": lambda: list(
                    SocialLink.objects.filter(is_visible=True).order_by("order")
                ),
                "description": "Get visible social links",
            },
            {
                "name": "AI Tools - Featured",
                "query": lambda: list(
                    AITool.objects.filter(is_featured=True, is_visible=True)
                ),
                "description": "Get featured AI tools",
            },
            {
                "name": "Contact Messages - Recent",
                "query": lambda: list(
                    ContactMessage.objects.filter(is_read=False).order_by(
                        "-created_at"
                    )[:20]
                ),
                "description": "Get recent unread messages",
            },
        ]

        query_results = []

        for query_info in queries_to_test:
            # Reset connection queries tracking
            if hasattr(connection, "queries"):
                connection.queries.clear()

            start_time = time.time()

            # Execute query
            try:
                with override_settings(DEBUG=True):
                    result = query_info["query"]()
                    end_time = time.time()

                    execution_time = (
                        end_time - start_time
                    ) * 1000  # Convert to milliseconds
                    query_count = (
                        len(connection.queries) if hasattr(connection, "queries") else 1
                    )

                    query_results.append(
                        {
                            "name": query_info["name"],
                            "description": query_info["description"],
                            "execution_time": execution_time,
                            "query_count": query_count,
                            "result_count": (
                                len(result) if hasattr(result, "__len__") else 1
                            ),
                            "queries": (
                                connection.queries.copy()
                                if hasattr(connection, "queries")
                                else []
                            ),
                            "status": "SUCCESS",
                        }
                    )

                    # Show immediate results
                    status_color = (
                        self.style.SUCCESS
                        if execution_time < 100
                        else (
                            self.style.WARNING
                            if execution_time < 500
                            else self.style.ERROR
                        )
                    )

                    self.stdout.write(f"\n{query_info['name']}:")
                    self.stdout.write(f"  Description: {query_info['description']}")
                    self.stdout.write(
                        "  Execution Time: " + status_color(f"{execution_time:.2f}ms")
                    )
                    self.stdout.write(f"  Query Count: {query_count}")
                    self.stdout.write(
                        f"  Results: {len(result) if hasattr(result, '__len__') else 1} records"
                    )

                    if verbose and hasattr(connection, "queries"):
                        for i, query in enumerate(connection.queries, 1):
                            self.stdout.write(f"  SQL {i}: {query['sql']}")
                            self.stdout.write(f"    Time: {query['time']}s")

            except Exception as e:
                query_results.append(
                    {
                        "name": query_info["name"],
                        "description": query_info["description"],
                        "execution_time": 0,
                        "query_count": 0,
                        "result_count": 0,
                        "error": str(e),
                        "status": "ERROR",
                    }
                )

                self.stdout.write(
                    f"\n{query_info['name']}: " + self.style.ERROR(f"ERROR - {e}")
                )

        # Summary
        self.show_performance_summary(query_results)

    def show_performance_summary(self, results):
        """
        Show performance summary

        REFACTORED: Complexity reduced from D:22 to A:2
        """
        from .utils import PerformanceSummaryGenerator

        generator = PerformanceSummaryGenerator(self)
        generator.show_summary(results)

    def analyze_model_queries(self):
        """Analyze common query patterns for models."""
        self.stdout.write("\n" + "=" * 40)
        self.stdout.write("MODEL QUERY PATTERN ANALYSIS")
        self.stdout.write("=" * 40)

        models_to_analyze = [
            ("Post", Post, ["status", "author", "published_at", "created_at"]),
            ("PersonalInfo", PersonalInfo, ["is_visible", "type", "order"]),
            ("SocialLink", SocialLink, ["is_visible", "platform", "order"]),
            ("AITool", AITool, ["category", "is_visible", "is_featured"]),
            ("ContactMessage", ContactMessage, ["is_read", "created_at"]),
        ]

        for model_name, model_class, key_fields in models_to_analyze:
            self.stdout.write(f"\n{model_name} Model:")

            # Get record count
            try:
                count = model_class.objects.count()
                self.stdout.write(f"  Records: {count}")
            except Exception as e:
                self.stdout.write(f"  Records: Error - {e}")
                continue

            # Analyze each key field
            for field in key_fields:
                try:
                    distinct_count = (
                        model_class.objects.values(field).distinct().count()
                    )
                    self.stdout.write(
                        f"  Field '{field}': {distinct_count} distinct values"
                    )
                except Exception as e:
                    self.stdout.write(f"  Field '{field}': Error - {e}")

        # Index recommendations
        self.stdout.write("\nINDEX RECOMMENDATIONS:")
        self.stdout.write(
            "- Blog Posts: Consider composite index on (status, published_at DESC)"
        )
        self.stdout.write("- Personal Info: Index on (is_visible, order) is optimal")
        self.stdout.write(
            "- Social Links: Index on (is_visible, platform, order) recommended"
        )
        self.stdout.write(
            "- Contact Messages: Index on (is_read, created_at DESC) for admin views"
        )

    def get_database_stats(self):
        """Get database statistics."""
        with connection.cursor() as cursor:
            if "sqlite" in settings.DATABASES["default"]["ENGINE"]:
                # SQLite stats
                cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
                table_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='index'")
                index_count = cursor.fetchone()[0]

                return {
                    "tables": table_count,
                    "indexes": index_count,
                    "database_type": "SQLite",
                }
            else:
                # PostgreSQL stats
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM information_schema.tables
                    WHERE table_schema = 'public'
                """
                )
                table_count = cursor.fetchone()[0]

                cursor.execute(
                    """
                    SELECT COUNT(*) FROM pg_indexes
                    WHERE schemaname = 'public'
                """
                )
                index_count = cursor.fetchone()[0]

                return {
                    "tables": table_count,
                    "indexes": index_count,
                    "database_type": "PostgreSQL",
                }
