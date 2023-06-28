from backend.views.base_views import SiteContentViewSetMixin
from backend.views.search.base_search_views import BaseSearchViewSet


class SiteSearchViewsSet(BaseSearchViewSet, SiteContentViewSetMixin):
    def get_search_params(self):
        """
        Add site_slug to search params
        """

        site = self.get_validated_site()
        site_id = site[0].id

        search_params = super().get_search_params()
        search_params["site_id"] = str(site_id)

        return search_params
