# Main views module
from .search import (
    SearchView,
    TagCloudView,
    search_by_tag,
)

# Create function-based view aliases for URL patterns
search_view = SearchView.as_view()
tag_search_view = TagCloudView.as_view()
tag_results_view = search_by_tag
