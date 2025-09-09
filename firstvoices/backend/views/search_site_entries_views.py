from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    extend_schema,
    extend_schema_view,
)

from backend.models import Category, ImportJob
from backend.search.validators import get_valid_instance_id, get_valid_starts_with_char
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
                value="valid UUID",
                description="Return entries which are associated with "
                "the given category or its child categories.",
            ),
            OpenApiExample(
                "invalid UUID",
                value="invalid UUID",
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
        """
        Add site_slug to search params
        """
        site = self.get_validated_site()
        site_id = site.id

        search_params = super().get_search_params()
        search_params["sites"] = [str(site_id)]

        starts_with_input_str = self.request.GET.get("startsWithChar", "")
        starts_with_char = get_valid_starts_with_char(starts_with_input_str)
        if starts_with_char:
            search_params["starts_with_char"] = starts_with_char

        category_input_str = self.request.GET.get("category", "")
        if category_input_str:
            category_id = get_valid_instance_id(
                site,
                Category,
                category_input_str,
            )
            search_params["category_id"] = category_id
        else:
            search_params["category_id"] = ""

        import_job_input_str = self.request.GET.get("importJobId", "")
        if import_job_input_str:
            import_job_id = get_valid_instance_id(site, ImportJob, import_job_input_str)
            search_params["import_job_id"] = import_job_id
        else:
            search_params["import_job_id"] = ""

        return search_params

    def has_invalid_input(self, search_params):
        return (
            super().has_invalid_input(search_params)
            or search_params["category_id"] is None
            or search_params["import_job_id"] is None
        )
