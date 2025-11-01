"""
Template tags for blog functionality
"""

from django import template

from apps.blog.models import Post

register = template.Library()


@register.inclusion_tag("blog/widgets/popular_posts.html")
def popular_posts(limit=5, widget_title="Popular Posts"):
    """
    Display popular posts widget

    Usage: {% popular_posts limit=5 widget_title="Most Read" %}
    """
    posts = Post.objects.popular(limit=limit)
    return {"posts": posts, "widget_title": widget_title, "limit": limit}


@register.inclusion_tag("blog/widgets/trending_posts.html")
def trending_posts(days=30, limit=5, widget_title="Trending Posts"):
    """
    Display trending posts widget (popular in recent days)

    Usage: {% trending_posts days=7 limit=5 %}
    """
    posts = Post.objects.trending(days=days, limit=limit)
    return {"posts": posts, "widget_title": widget_title, "days": days, "limit": limit}


@register.inclusion_tag("blog/widgets/recent_posts.html")
def recent_posts(limit=5, widget_title="Recent Posts"):
    """
    Display recent posts widget

    Usage: {% recent_posts limit=5 %}
    """
    posts = Post.objects.published().order_by("-published_at")[:limit]
    return {"posts": posts, "widget_title": widget_title, "limit": limit}


@register.inclusion_tag("blog/widgets/archive_widget.html")
def blog_archive(widget_title="Archive"):
    """
    Display blog archive widget (posts grouped by year/month)

    Usage: {% blog_archive %}
    """
    from django.db.models import Count
    from django.db.models.functions import TruncMonth

    # Group posts by month and year
    archive_data = (
        Post.objects.published()
        .annotate(month=TruncMonth("published_at"))
        .values("month")
        .annotate(count=Count("id"))
        .order_by("-month")[:24]
    )  # Last 24 months

    return {"archive_data": archive_data, "widget_title": widget_title}


@register.simple_tag
def post_reading_time(post):
    """
    Get reading time for a post

    Usage: {% post_reading_time post %}
    """
    return post.get_reading_time()


@register.simple_tag
def post_word_count(post):
    """
    Get word count for a post

    Usage: {% post_word_count post %}
    """
    return post.word_count


@register.filter
def reading_time_text(minutes):
    """
    Convert reading time to readable text

    Usage: {{ post.get_reading_time|reading_time_text }}
    """
    if minutes < 1:
        return "< 1 min read"
    elif minutes == 1:
        return "1 min read"
    else:
        return f"{minutes} min read"


@register.simple_tag
def get_related_posts(post, limit=3):
    """
    Get related posts for a given post

    Usage: {% get_related_posts post limit=5 as related %}
    """
    return post.get_related_posts(limit=limit)


@register.inclusion_tag("blog/widgets/related_content.html")
def related_content_widget(post, limit=5, widget_title="Related Content"):
    """
    Display related content widget (cross-content type recommendations)

    Usage: {% related_content_widget post limit=6 %}
    """
    related_content = post.get_similar_content(limit=limit)

    return {
        "related_content": related_content,
        "widget_title": widget_title,
        "current_post": post,
        "limit": limit,
    }


@register.inclusion_tag("blog/widgets/related_posts.html")
def related_posts_widget(post, limit=3, widget_title="Related Posts"):
    """
    Display related posts widget

    Usage: {% related_posts_widget post limit=5 %}
    """
    related_posts = post.get_related_posts(limit=limit)

    return {
        "related_posts": related_posts,
        "widget_title": widget_title,
        "current_post": post,
        "limit": limit,
    }


@register.simple_tag
def content_recommendation_score(post1, post2):
    """
    Calculate similarity score between two posts

    Usage: {% content_recommendation_score post1 post2 %}
    """
    if not post1.tags or not post2.tags:
        return 0

    common_tags = set(post1.tags) & set(post2.tags)
    return len(common_tags)
