from backend.search.utils.query_builder_utils import (
    get_valid_category_id,
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

        category_input_str = self.request.GET.get("category", "")
        category_id = get_valid_category_id(
            category_input_str, self.get_validated_site()
        )

        if starts_with_char:
            search_params["starts_with_char"] = starts_with_char

        if category_id:
            search_params["category_id"] = category_id

        # limit types to only words and phrases
        input_types_str = self.request.GET.get("types", "")
        valid_types_list = get_valid_document_types(
            input_types_str, allowed_values=["words", "phrases"]
        )

        search_params["types"] = valid_types_list

        return search_params
