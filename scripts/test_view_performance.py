"""
Quick performance test for optimized views
Tests query count for blog and portfolio views
"""

import os
import sys

import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings.simple")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from django.contrib.auth.models import AnonymousUser
from django.db import connection, reset_queries
from django.test import RequestFactory

from apps.blog.models import Post
from apps.blog.views import PostDetailView, PostListView
from apps.tools.models import Tool


def test_blog_list_view():
    """Test blog list view query count"""
    print("\n" + "=" * 60)
    print("TESTING BLOG LIST VIEW")
    print("=" * 60)

    # Create request
    factory = RequestFactory()
    request = factory.get("/blog/")
    request.user = AnonymousUser()

    # Reset query count
    reset_queries()

    # Execute view
    view = PostListView.as_view()
    response = view(request)

    # Print results
    query_count = len(connection.queries)
    print(f"✓ Query Count: {query_count}")
    print(f"✓ Response Status: {response.status_code}")

    if query_count <= 3:  # 1 for posts, maybe 1-2 for pagination
        print("✓ PASS: Excellent! Low query count")
    elif query_count <= 5:
        print("⚠ OK: Acceptable query count")
    else:
        print("✗ FAIL: Too many queries!")
        print("\nQueries executed:")
        for i, query in enumerate(connection.queries, 1):
            print(f"{i}. {query['sql'][:100]}...")

    return query_count


def test_blog_detail_view():
    """Test blog detail view query count"""
    print("\n" + "=" * 60)
    print("TESTING BLOG DETAIL VIEW")
    print("=" * 60)

    # Get a published post
    post = Post.objects.published().first()
    if not post:
        print("✗ No published posts found. Skipping test.")
        return 0

    # Create request
    factory = RequestFactory()
    request = factory.get(f"/blog/{post.slug}/")
    request.user = AnonymousUser()

    # Reset query count
    reset_queries()

    # Execute view
    view = PostDetailView.as_view()
    response = view(request, slug=post.slug)

    # Print results
    query_count = len(connection.queries)
    print(f"✓ Query Count: {query_count}")
    print(f"✓ Response Status: {response.status_code}")

    if query_count <= 5:  # 1 for post, 1 for view update, 1-3 for related
        print("✓ PASS: Excellent! Low query count")
    elif query_count <= 8:
        print("⚠ OK: Acceptable query count")
    else:
        print("✗ FAIL: Too many queries!")
        print("\nQueries executed:")
        for i, query in enumerate(connection.queries, 1):
            print(f"{i}. {query['sql'][:100]}...")

    return query_count


def test_stats():
    """Print database stats"""
    print("\n" + "=" * 60)
    print("DATABASE STATS")
    print("=" * 60)

    post_count = Post.objects.count()
    published_count = Post.objects.published().count()
    tool_count = Tool.objects.count()
    visible_tool_count = Tool.objects.visible().count()

    print(f"✓ Total Posts: {post_count}")
    print(f"✓ Published Posts: {published_count}")
    print(f"✓ Total Tools: {tool_count}")
    print(f"✓ Visible Tools: {visible_tool_count}")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("VIEW PERFORMANCE TEST")
    print("=" * 60)

    test_stats()

    try:
        blog_list_queries = test_blog_list_view()
        blog_detail_queries = test_blog_detail_view()

        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"✓ Blog List View: {blog_list_queries} queries")
        print(f"✓ Blog Detail View: {blog_detail_queries} queries")
        print("\n✓ ALL TESTS COMPLETED!")

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback

        traceback.print_exc()
