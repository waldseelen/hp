from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from django.db.models import Q
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from apps.main.cache_utils import CacheManager, cache_queryset_medium, cache_result
from .models import Post


class PostListView(ListView):
    model = Post
    template_name = 'blog/list.html'
    context_object_name = 'posts'
    paginate_by = 10
    
    def get_queryset(self):
        search = self.request.GET.get('search')
        
        if search:
            # Don't cache search results
            queryset = Post.objects.published()
            queryset = queryset.filter(
                Q(title__icontains=search) | 
                Q(content__icontains=search) |
                Q(excerpt__icontains=search)
            )
            return queryset
        else:
            # Cache regular post listing
            cache_key = CacheManager.make_key(
                CacheManager.PREFIXES['blog_posts'], 
                'published_list'
            )
            
            cached_posts = cache.get(cache_key)
            if cached_posts is not None:
                return cached_posts
            
            queryset = Post.objects.published()
            cache.set(cache_key, queryset, CacheManager.TIMEOUTS['medium'])
            return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        return context


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'
    context_object_name = 'post'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    def get_queryset(self):
        return Post.objects.published()
    
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        
        # Cache related posts
        post_id = self.object.id
        cache_key = CacheManager.make_key(
            CacheManager.PREFIXES['blog_posts'], 
            'related', 
            str(post_id)
        )
        
        cached_related = cache.get(cache_key)
        if cached_related is not None:
            ctx['related_posts'] = cached_related
        else:
            related_posts = self.get_object().get_related_posts(limit=3)
            cache.set(cache_key, related_posts, CacheManager.TIMEOUTS['long'])
            ctx['related_posts'] = related_posts
        
        # Add dynamic breadcrumb for this post
        self.request.breadcrumbs_extra = [
            {'title': self.object.title, 'url': None}
        ]
        
        return ctx
