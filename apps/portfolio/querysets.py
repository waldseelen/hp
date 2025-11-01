"""
Optimized QuerySet managers for improved database performance.
"""

from django.core.cache import cache
from django.db import models
from django.db.models import Count, F, Max, Q
from django.utils import timezone


class OptimizedQuerySetMixin:
    """Mixin to provide common optimization methods."""

    def select_optimized(self, *fields):
        """Optimize select_related calls."""
        return self.select_related(*fields)

    def prefetch_optimized(self, *prefetches):
        """Optimize prefetch_related calls."""
        return self.prefetch_related(*prefetches)

    def with_cache(self, cache_key, timeout=300):
        """Cache queryset results."""

        def get_cached_queryset():
            cached = cache.get(cache_key)
            if cached is not None:
                return cached

            result = list(self)
            cache.set(cache_key, result, timeout)
            return result

        return get_cached_queryset()


class PostQuerySet(models.QuerySet, OptimizedQuerySetMixin):
    """Optimized QuerySet for Blog Post model."""

    def published(self):
        """Get published posts with optimized query."""
        return (
            self.filter(status="published", published_at__lte=timezone.now())
            .select_related("author")
            .order_by("-published_at")
        )

    def by_author(self, author):
        """Get posts by specific author with optimization."""
        return (
            self.filter(author=author, status="published")
            .select_related("author")
            .order_by("-published_at")
        )

    def popular(self, limit=10):
        """Get popular posts efficiently."""
        return (
            self.filter(status="published")
            .select_related("author")
            .order_by("-view_count")[:limit]
        )

    def recent(self, days=30, limit=10):
        """Get recent posts with single query."""
        cutoff_date = timezone.now() - timezone.timedelta(days=days)
        return (
            self.filter(status="published", published_at__gte=cutoff_date)
            .select_related("author")
            .order_by("-published_at")[:limit]
        )

    def with_view_stats(self):
        """Annotate with view statistics."""
        return self.annotate(
            total_views=F("view_count"),
            is_popular=models.Case(
                models.When(view_count__gte=1000, then=models.Value(True)),
                default=models.Value(False),
                output_field=models.BooleanField(),
            ),
        )

    def search(self, query):
        """Full-text search optimization."""
        return (
            self.filter(
                Q(title__icontains=query)
                | Q(content__icontains=query)
                | Q(excerpt__icontains=query)
            )
            .select_related("author")
            .order_by("-published_at")
        )


class PersonalInfoQuerySet(models.QuerySet, OptimizedQuerySetMixin):
    """Optimized QuerySet for Personal Information."""

    def visible(self):
        """Get visible items efficiently."""
        return self.filter(is_visible=True).order_by("order")

    def by_type(self, info_type):
        """Get items by type with caching."""
        return self.filter(type=info_type, is_visible=True).order_by("order")

    def json_data(self):
        """Get JSON type data efficiently."""
        return (
            self.filter(type="json", is_visible=True)
            .values("key", "value")
            .order_by("order")
        )


class SocialLinkQuerySet(models.QuerySet, OptimizedQuerySetMixin):
    """Optimized QuerySet for Social Links."""

    def visible(self):
        """Get visible social links."""
        return self.filter(is_visible=True).order_by("order")

    def primary(self):
        """Get primary social link efficiently."""
        return self.filter(is_primary=True).first()

    def by_platform(self, platform):
        """Get links by platform."""
        return self.filter(platform=platform, is_visible=True).order_by("order")

    def with_stats(self):
        """Include stats data efficiently."""
        return self.filter(is_visible=True, stats__isnull=False).order_by("order")


class AIToolQuerySet(models.QuerySet, OptimizedQuerySetMixin):
    """Optimized QuerySet for AI Tools."""

    def visible(self):
        """Get visible tools."""
        return self.filter(is_visible=True).order_by("category", "order")

    def featured(self):
        """Get featured tools efficiently."""
        return self.filter(is_featured=True, is_visible=True).order_by(
            "-rating", "name"
        )

    def by_category(self, category):
        """Get tools by category with optimization."""
        return self.filter(category=category, is_visible=True).order_by("order", "name")

    def free_tools(self):
        """Get free tools."""
        return self.filter(is_free=True, is_visible=True).order_by("category", "order")

    def top_rated(self, limit=10):
        """Get top rated tools."""
        return self.filter(is_visible=True, rating__gt=0).order_by("-rating", "name")[
            :limit
        ]


class ContactMessageQuerySet(models.QuerySet, OptimizedQuerySetMixin):
    """Optimized QuerySet for Contact Messages."""

    def unread(self):
        """Get unread messages efficiently."""
        return self.filter(is_read=False).order_by("-created_at")

    def recent(self, days=7):
        """Get recent messages."""
        cutoff_date = timezone.now() - timezone.timedelta(days=days)
        return self.filter(created_at__gte=cutoff_date).order_by("-created_at")

    def by_email(self, email):
        """Get messages by email efficiently."""
        return self.filter(email=email).order_by("-created_at")


class PerformanceMetricQuerySet(models.QuerySet, OptimizedQuerySetMixin):
    """Optimized QuerySet for Performance Metrics."""

    def by_type(self, metric_type):
        """Get metrics by type."""
        return self.filter(metric_type=metric_type).order_by("-timestamp")

    def recent(self, hours=24):
        """Get recent metrics."""
        cutoff_time = timezone.now() - timezone.timedelta(hours=hours)
        return self.filter(timestamp__gte=cutoff_time).order_by("-timestamp")

    def good_scores(self):
        """Get metrics with good scores."""
        return self.filter(
            Q(metric_type="lcp", value__lte=2500)
            | Q(metric_type="fid", value__lte=100)
            | Q(metric_type="cls", value__lte=0.1)
            | Q(metric_type="ttfb", value__lte=800)
        ).order_by("-timestamp")

    def device_stats(self):
        """Get device statistics."""
        return (
            self.values("device_type")
            .annotate(
                count=Count("id"),
                avg_value=models.Avg("value"),
                latest=Max("timestamp"),
            )
            .order_by("device_type")
        )

    def url_performance(self, url):
        """Get performance metrics for specific URL."""
        return self.filter(url=url).order_by("-timestamp")


# Manager classes that use the optimized querysets
class PostManager(models.Manager.from_queryset(PostQuerySet)):
    """Manager for Post model with optimized queries."""

    def get_queryset(self):
        return super().get_queryset()


class PersonalInfoManager(models.Manager.from_queryset(PersonalInfoQuerySet)):
    """Manager for PersonalInfo model."""


class SocialLinkManager(models.Manager.from_queryset(SocialLinkQuerySet)):
    """Manager for SocialLink model."""


class AIToolManager(models.Manager.from_queryset(AIToolQuerySet)):
    """Manager for AITool model."""


class ContactMessageManager(models.Manager.from_queryset(ContactMessageQuerySet)):
    """Manager for ContactMessage model."""


class PerformanceMetricManager(models.Manager.from_queryset(PerformanceMetricQuerySet)):
    """Manager for PerformanceMetric model."""


# Utility functions for query optimization
def bulk_update_optimized(model_class, objects, fields, batch_size=1000):
    """Optimized bulk update function."""
    return model_class.objects.bulk_update(objects, fields, batch_size=batch_size)


def bulk_create_optimized(
    model_class, objects, batch_size=1000, ignore_conflicts=False
):
    """Optimized bulk create function."""
    return model_class.objects.bulk_create(
        objects, batch_size=batch_size, ignore_conflicts=ignore_conflicts
    )


def get_or_create_optimized(model_class, defaults=None, **lookup):
    """Optimized get_or_create with caching."""
    cache_key = (
        f"{model_class.__name__}:{'_'.join(f'{k}_{v}' for k, v in lookup.items())}"
    )

    # Try cache first
    cached_result = cache.get(cache_key)
    if cached_result:
        return cached_result, False

    # Fallback to database
    obj, created = model_class.objects.get_or_create(defaults=defaults, **lookup)

    # Cache the result
    cache.set(cache_key, obj, timeout=300)

    return obj, created


class QueryOptimizer:
    """Utility class for query optimization analysis."""

    @staticmethod
    def analyze_query_count(queryset):
        """Analyze query count for a given queryset."""
        from django.db import connection
        from django.test.utils import override_settings

        with override_settings(DEBUG=True):
            initial_query_count = len(connection.queries)
            list(queryset)  # Execute the queryset
            final_query_count = len(connection.queries)

            return final_query_count - initial_query_count

    @staticmethod
    def explain_query(queryset):
        """Get query execution plan (PostgreSQL only)."""
        try:
            return queryset.explain()
        except AttributeError:
            return "Query explanation not available for this database backend"

    @staticmethod
    def profile_queryset(queryset, name="Query"):
        """Profile queryset execution time."""
        import time

        start_time = time.time()
        result = list(queryset)
        end_time = time.time()

        execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
        query_count = QueryOptimizer.analyze_query_count(queryset)

        return {
            "name": name,
            "execution_time_ms": execution_time,
            "query_count": query_count,
            "result_count": len(result),
        }
