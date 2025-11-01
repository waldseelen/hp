from django.db.models import Q
from django.views.generic import DetailView, ListView

from .models import Tool


class ToolListView(ListView):
    model = Tool
    template_name = "pages/tools/list.html"
    context_object_name = "tools"
    paginate_by = 20

    def get_queryset(self):
        queryset = Tool.objects.visible().order_by("category", "title")
        search = self.request.GET.get("search")
        category = self.request.GET.get("category")

        if search:
            queryset = queryset.filter(
                Q(title__icontains=search)
                | Q(description__icontains=search)
                | Q(category__icontains=search)
            )

        if category:
            queryset = queryset.filter(category=category)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_query"] = self.request.GET.get("search", "")
        context["selected_category"] = self.request.GET.get("category", "")
        context["categories"] = (
            Tool.objects.visible()
            .values_list("category", flat=True)
            .distinct()
            .order_by("category")
        )
        context["favorites"] = Tool.objects.visible().filter(is_favorite=True)
        return context


class ToolDetailView(DetailView):
    model = Tool
    template_name = "pages/tools/detail.html"
    context_object_name = "tool"

    def get_queryset(self):
        return Tool.objects.visible()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # Add dynamic breadcrumb for this tool
        self.request.breadcrumbs_extra = [{"title": self.object.title, "url": None}]

        return ctx
