from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    extend_schema,
    extend_schema_view,
)

from backend.search.utils.validators import get_valid_site_ids_from_slugs
from backend.views.base_search_entries_views import BaseSearchEntriesViewSet


@extend_schema_view(
    list=extend_schema(
        description="List of search results from all sites satisfying the query.",
        parameters=[
            OpenApiParameter(
                name="sites",
                description="Filter results based on site. Multiple site slugs can be passed as a comma-separated "
                "list. For searching a single site, see also the site-level search API.",
                required=False,
                default="",
                type=str,
                examples=[
                    OpenApiExample(
                        "One Site",
                        value="site1",
                        description="Return results from site1.",
                    ),
                    OpenApiExample(
                        "Multiple Sites",
                        value="site1,site2",
                        description="Return results from site1 and site2.",
                    ),
                ],
            ),
        ],
    ),
)
class SearchAllEntriesViewSet(BaseSearchEntriesViewSet):
    def get_search_params(self):
        """
        Function to return search params in a structured format.
        """
        base_search_params = super().get_search_params()

        sites = self.request.GET.get("sites", "")
        valid_site_ids = get_valid_site_ids_from_slugs(sites, self.request.user)

        return {
            **base_search_params,
            "sites": valid_site_ids,
        }

    def has_invalid_input(self, search_params):
        return (
            super().has_invalid_input(search_params) or search_params["sites"] is None
        )
