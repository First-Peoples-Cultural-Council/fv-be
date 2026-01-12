from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    extend_schema,
    extend_schema_view,
)
from search.utils import (
    get_site_entries_search_params,
    has_invalid_site_entries_search_input,
)

from backend.views.api_doc_variables import site_slug_parameter
from backend.views.base_search_entries_views import (
    BASE_SEARCH_PARAMS,
    BaseSearchEntriesViewSet,
)
from backend.views.base_views import SiteContentViewSetMixin

SITE_SEARCH_PARAMS = [
    site_slug_parameter,
    OpenApiParameter(
        name="startsWithChar",
        description="Return entries that start with the specified character.",
        required=False,
        default="",
        type=str,
        examples=[
            OpenApiExample(
                "",
                value="",
                description="Default case. Do not add startsWithChar filter.",
            ),
            OpenApiExample(
                "a",
                value="a",
                description="Return all entries starting with a.",
            ),
        ],
    ),
    OpenApiParameter(
        name="importJobId",
        description="Filter results based on the associated batch import job.",
        required=False,
        default="",
        type=str,
        examples=[
            OpenApiExample(
                "valid UUID",
                value="6cdb161a-2ce7-4197-813d-1683448128a2",
                description="Return entries which were imported by the specified job.",
            ),
        ],
    ),
    OpenApiParameter(
        name="category",
        description="Return entries which are associated with the given category or its child categories.",
        required=False,
        default="",
        type=str,
        examples=[
            OpenApiExample(
                "",
                value="",
                description="Default case. Do not add categories filter.",
            ),
            OpenApiExample(
                "valid UUID",
                value="6cdb161a-2ce7-4197-813d-1683448128a2",
                description="Return entries which are associated with "
                "the given category or its child categories.",
            ),
            OpenApiExample(
                "invalid UUID",
                value="invalid-uuid",
                description="Cannot validate given id, returns empty result set.",
            ),
        ],
    ),
]


@extend_schema_view(
    list=extend_schema(
        description="List of search results from this site satisfying the query.",
        parameters=[*BASE_SEARCH_PARAMS, *SITE_SEARCH_PARAMS],
    )
)
class SearchSiteEntriesViewSet(SiteContentViewSetMixin, BaseSearchEntriesViewSet):
    def get_search_params(self):
        site = self.get_validated_site()
        return get_site_entries_search_params(self.request, site)

    def has_invalid_input(self, search_params):
        return has_invalid_site_entries_search_input(search_params)
