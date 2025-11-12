from django.db.models import Q
from django.views.generic import DetailView, ListView

from .models import Post


class PostListView(ListView):
    """
    Optimized blog post list view with efficient queryset and pagination.

    Features:
    - select_related for author to avoid N+1 queries
    - Search functionality across title, content, and excerpt
    - Pagination with metadata (page numbers, counts)
    - Efficient queryset using published() manager
    """

    model = Post
    template_name = "pages/blog/list.html"
    context_object_name = "posts"
    paginate_by = 10

    def get_queryset(self):
        """
        Get optimized queryset with author prefetched and search applied.

        Returns:
            QuerySet: Filtered and optimized post queryset
        """
        # Start with optimized published posts (already has select_related("author"))
        queryset = Post.objects.published()

        # Apply search filter if provided
        search = self.request.GET.get("search")
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search)
                | Q(content__icontains=search)
                | Q(excerpt__icontains=search)
            )

        return queryset

    def get_context_data(self, **kwargs):
        """
        Add pagination metadata and search query to context.

        Returns:
            dict: Context with posts, pagination info, and search query
        """
        context = super().get_context_data(**kwargs)

        # Add search query for template
        context["search_query"] = self.request.GET.get("search", "")

        # Add pagination metadata
        paginator = context.get("paginator")
        page_obj = context.get("page_obj")

        if paginator and page_obj:
            context["total_posts"] = paginator.count
            context["total_pages"] = paginator.num_pages
            context["current_page"] = page_obj.number

            # Calculate page range for pagination UI (show 5 pages)
            current = page_obj.number
            total = paginator.num_pages
            page_range_start = max(1, current - 2)
            page_range_end = min(total + 1, current + 3)
            context["page_range"] = range(page_range_start, page_range_end)

        return context


class PostDetailView(DetailView):
    """
    Optimized blog post detail view with related posts and view tracking.

    Features:
    - select_related for author to avoid N+1 queries
    - Efficient related posts fetching
    - View count increment (F() expression for race condition safety)
    - SEO metadata (reading time, word count)
    """

    model = Post
    template_name = "pages/blog/detail.html"
    context_object_name = "post"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        """
        Get optimized queryset with author prefetched.

        Returns:
            QuerySet: Published posts with author relationship
        """
        # Use published() manager which already has select_related("author")
        return Post.objects.published()

    def get_object(self, queryset=None):
        """
        Get post object and increment view count safely.

        Returns:
            Post: The requested post instance
        """
        obj = super().get_object(queryset)

        # Increment view count using F() expression (atomic, no race condition)
        obj.increment_view_count()

        # Refresh from DB to get updated view_count for display
        obj.refresh_from_db(fields=["view_count"])

        return obj

    def get_context_data(self, **kwargs):
        """
        Add related posts and metadata to context.

        Returns:
            dict: Context with post, related posts, and metadata
        """
        ctx = super().get_context_data(**kwargs)

        # Get post from context (already retrieved by get_object)
        post = ctx["post"]
        ctx["related_posts"] = post.get_related_posts(limit=3)

        # Add SEO and UX metadata
        ctx["reading_time"] = post.reading_time
        ctx["word_count"] = post.word_count
        ctx["page_title"] = post.title
        ctx["meta_description"] = post.meta_description or post.excerpt

        return ctx
