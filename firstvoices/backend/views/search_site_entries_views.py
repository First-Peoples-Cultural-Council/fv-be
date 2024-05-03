from drf_spectacular.utils import extend_schema, extend_schema_view

from backend.search.utils.validators import (
    get_valid_category_id,
    get_valid_starts_with_char,
)
from backend.views.api_doc_variables import site_slug_parameter
from backend.views.base_views import SiteContentViewSetMixin
from backend.views.search_all_entries_views import SearchAllEntriesViewSet


@extend_schema_view(list=extend_schema(parameters=[site_slug_parameter]))
class SearchSiteEntriesViewSet(SiteContentViewSetMixin, SearchAllEntriesViewSet):
    def get_search_params(self):
        """
        Add site_slug to search params
        """
        site = self.get_validated_site()
        site_id = site.id

        search_params = super().get_search_params()
        search_params["site_id"] = str(site_id)

        starts_with_input_str = self.request.GET.get("startsWithChar", "")
        starts_with_char = get_valid_starts_with_char(starts_with_input_str)
        if starts_with_char:
            search_params["starts_with_char"] = starts_with_char

        category_input_str = self.request.GET.get("category", "")
        if category_input_str:
            category_id = get_valid_category_id(
                site,
                category_input_str,
            )
            search_params["category_id"] = category_id

        return search_params
