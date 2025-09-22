#!/usr/bin/env python
"""
Database Query Performance Test Script
Tests common queries to identify potential performance issues.
"""

import os
import sys
import django
import time
from django.db import connection

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portfolio_site.settings.development')
django.setup()

from apps.blog.models import Post
from apps.main.models import (
    PersonalInfo, SocialLink, AITool, CybersecurityResource,
    BlogCategory, BlogPost, MusicPlaylist, UsefulResource,
    PerformanceMetric, WebPushSubscription
)
from apps.tools.models import Tool
from apps.contact.models import ContactMessage

def time_query(query_func, description):
    """Time a database query and return results"""
    print(f"\n[TEST] {description}")
    
    # Clear query log
    connection.queries_log.clear()
    
    start_time = time.time()
    result = query_func()
    end_time = time.time()
    
    # Get query count and time
    query_count = len(connection.queries)
    query_time = end_time - start_time
    
    print(f"Time: {query_time:.4f}s")
    print(f"Queries: {query_count}")
    print(f"Results: {len(result) if hasattr(result, '__len__') else 'N/A'}")
    
    # Show actual SQL queries
    if connection.queries:
        print("SQL Queries:")
        for i, query in enumerate(connection.queries, 1):
            print(f"   {i}. {query['sql'][:100]}...")
    
    return query_time, query_count

def test_blog_queries():
    """Test blog-related queries"""
    print("\n" + "="*60)
    print("BLOG QUERIES PERFORMANCE TEST")
    print("="*60)
    
    # Test 1: Published posts
    def get_published_posts():
        return list(Post.objects.published()[:10])
    
    time_query(get_published_posts, "Get published posts (first 10)")
    
    # Test 2: Posts by author with related data
    def get_posts_with_author():
        return list(Post.objects.select_related('author')[:10])
    
    time_query(get_posts_with_author, "Posts with author (select_related)")

def test_main_queries():
    """Test main app queries"""
    print("\n" + "="*60)
    print("MAIN APP QUERIES PERFORMANCE TEST")
    print("="*60)
    
    # Test 1: Visible personal info
    def get_visible_personal_info():
        return list(PersonalInfo.objects.filter(is_visible=True).order_by('order'))
    
    time_query(get_visible_personal_info, "Get visible personal info")
    
    # Test 2: Social links
    def get_social_links():
        return list(SocialLink.objects.filter(is_visible=True).order_by('order'))
    
    time_query(get_social_links, "Get visible social links")
    
    # Test 3: Featured AI tools
    def get_featured_ai_tools():
        return list(AITool.objects.filter(is_featured=True, is_visible=True))
    
    time_query(get_featured_ai_tools, "Get featured AI tools")

def test_tools_queries():
    """Test tools queries"""
    print("\n" + "="*60)
    print("TOOLS QUERIES PERFORMANCE TEST")
    print("="*60)
    
    # Test 1: Visible tools by category
    def get_tools_by_category():
        return list(Tool.objects.filter(is_visible=True).order_by('category', 'title'))
    
    time_query(get_tools_by_category, "Get tools by category")
    
    # Test 2: Favorite tools
    def get_favorite_tools():
        return list(Tool.objects.filter(is_favorite=True, is_visible=True))
    
    time_query(get_favorite_tools, "Get favorite tools")

def test_contact_queries():
    """Test contact queries"""
    print("\n" + "="*60)
    print("CONTACT QUERIES PERFORMANCE TEST")
    print("="*60)
    
    # Test 1: Unread messages
    def get_unread_messages():
        return list(ContactMessage.objects.filter(is_read=False).order_by('-created_at'))
    
    time_query(get_unread_messages, "Get unread contact messages")

def test_performance_queries():
    """Test performance monitoring queries"""
    print("\n" + "="*60)
    print("PERFORMANCE MONITORING QUERIES TEST")
    print("="*60)
    
    # Test 1: Recent performance metrics
    def get_recent_metrics():
        return list(PerformanceMetric.objects.filter(
            metric_type='lcp'
        ).order_by('-timestamp')[:10])
    
    time_query(get_recent_metrics, "Get recent LCP metrics")

def run_all_tests():
    """Run all performance tests"""
    print("STARTING DATABASE QUERY PERFORMANCE ANALYSIS")
    print("="*80)
    
    total_start = time.time()
    
    test_blog_queries()
    test_main_queries()
    test_tools_queries()
    test_contact_queries()
    test_performance_queries()
    
    total_time = time.time() - total_start
    
    print("\n" + "="*80)
    print(f"ALL TESTS COMPLETED IN {total_time:.4f}s")
    print("="*80)
    
    # Show database info
    print(f"\nDatabase Info:")
    print(f"   Engine: {connection.vendor}")
    print(f"   Database: {connection.settings_dict['NAME']}")
    
    # Recommendations
    print(f"\nPerformance Recommendations:")
    print("   - Queries under 0.001s: Excellent")
    print("   - Queries 0.001-0.01s: Good")
    print("   - Queries 0.01-0.1s: Acceptable")
    print("   - Queries over 0.1s: Needs optimization")

if __name__ == "__main__":
    run_all_tests()