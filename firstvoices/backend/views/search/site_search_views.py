from backend.views.base_views import SiteContentViewSetMixin
from backend.views.search.base_search_views import BaseSearchViewSet


class SiteSearchViewsSet(BaseSearchViewSet, SiteContentViewSetMixin):
    def get_search_params(self):
        """
        Add site_slug to search params
        """

        site = self.get_validated_site()
        site_slug = site[0].slug

        search_params = super().get_search_params()
        search_params["site_slug"] = site_slug

        return search_params
