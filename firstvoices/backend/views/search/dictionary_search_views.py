from backend.search.utils.query_builder_utils import (
    get_valid_document_types,
    get_valid_starts_with_char,
)
from backend.views.search.site_search_views import SiteSearchViewsSet


class DictionarySearchViewSet(SiteSearchViewsSet):
    def get_search_params(self):
        """
        Add category, and alphabetCharacter to search params
        """
        search_params = super().get_search_params()

        starts_with_input_str = self.request.GET.get("startsWithChar", "")
        starts_with_char = get_valid_starts_with_char(starts_with_input_str)

        if starts_with_char:
            search_params["starts_with_char"] = starts_with_char

        # limit types to only words and phrases
        input_types_str = self.request.GET.get("types", "")
        valid_types_list = get_valid_document_types(
            input_types_str, allowed_values=["words", "phrases"]
        )

        search_params["types"] = valid_types_list

        return search_params
