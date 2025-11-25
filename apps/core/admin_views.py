"""
Custom Admin Views for Modern Admin Panel
"""

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta

from apps.blog.models import Post
from apps.tools.models import Tool
from apps.main.models import (
    BlogPost,
    CybersecurityResource,
    AITool,
    UsefulResource,
)


@staff_member_required
def modern_admin_dashboard(request):
    """
    Modern Admin Dashboard - Ana Sayfa
    """
    # Son 30 gün içindeki istatistikler
    last_30_days = timezone.now() - timedelta(days=30)

    # Blog istatistikleri
    total_blog_posts = Post.objects.count() + BlogPost.objects.count()
    recent_posts = Post.objects.filter(created_at__gte=last_30_days).count()
    published_posts = Post.objects.filter(status='published').count()
    draft_posts = Post.objects.filter(status='draft').count()

    # Tools istatistikleri
    total_tools = Tool.objects.count()
    visible_tools = Tool.objects.filter(is_visible=True).count()

    # AI Tools istatistikleri
    total_ai_tools = AITool.objects.count()
    featured_ai_tools = AITool.objects.filter(is_featured=True).count()

    # Cybersecurity istatistikleri
    total_cyber_resources = CybersecurityResource.objects.count()
    urgent_cyber = CybersecurityResource.objects.filter(is_urgent=True).count()
    critical_cyber = CybersecurityResource.objects.filter(severity_level=4).count()

    # Son aktiviteler
    recent_blog_posts = Post.objects.order_by('-created_at')[:5]
    recent_cyber = CybersecurityResource.objects.order_by('-created_at')[:5]

    context = {
        'page_title': 'Admin Dashboard',
        'stats': {
            'blog': {
                'total': total_blog_posts,
                'recent': recent_posts,
                'published': published_posts,
                'draft': draft_posts,
            },
            'tools': {
                'total': total_tools,
                'visible': visible_tools,
            },
            'ai_tools': {
                'total': total_ai_tools,
                'featured': featured_ai_tools,
            },
            'cybersecurity': {
                'total': total_cyber_resources,
                'urgent': urgent_cyber,
                'critical': critical_cyber,
            },
        },
        'recent_activities': {
            'blog_posts': recent_blog_posts,
            'cyber_resources': recent_cyber,
        },
    }

    return render(request, 'admin/modern/dashboard.html', context)


def modern_admin_login(request):
    """
    Modern Admin Login Page
    """
    # Eğer kullanıcı zaten giriş yapmışsa dashboard'a yönlendir
    if request.user.is_authenticated and request.user.is_staff:
        from django.shortcuts import redirect
        return redirect('modern_admin:dashboard')

    return render(request, 'admin/modern/login.html')


@staff_member_required
def blog_management(request):
    """
    Blog Yönetim Sayfası
    """
    posts = Post.objects.all().order_by('-created_at')
    blog_posts = BlogPost.objects.all().order_by('-created_at')

    context = {
        'page_title': 'Blog Yönetimi',
        'posts': posts,
        'blog_posts': blog_posts,
    }

    return render(request, 'admin/modern/blog.html', context)


@staff_member_required
def cybersecurity_management(request):
    """
    Siber Güvenlik Yönetim Sayfası
    """
    resources = CybersecurityResource.objects.all().order_by('-severity_level', '-created_at')

    # Kategorilere göre grupla
    by_type = resources.values('type').annotate(count=Count('id'))
    by_severity = resources.values('severity_level').annotate(count=Count('id'))

    context = {
        'page_title': 'Siber Güvenlik Yönetimi',
        'resources': resources,
        'stats': {
            'by_type': by_type,
            'by_severity': by_severity,
            'urgent_count': resources.filter(is_urgent=True).count(),
            'total': resources.count(),
        },
    }

    return render(request, 'admin/modern/cybersecurity.html', context)


@staff_member_required
def tools_management(request):
    """
    Tools & AI Tools Yönetim Sayfası
    """
    tools = Tool.objects.all().order_by('category', 'title')
    ai_tools = AITool.objects.all().order_by('category', 'name')
    useful_resources = UsefulResource.objects.all().order_by('category', 'name')

    context = {
        'page_title': 'Tools Yönetimi',
        'tools': tools,
        'ai_tools': ai_tools,
        'useful_resources': useful_resources,
    }

    return render(request, 'admin/modern/tools.html', context)
