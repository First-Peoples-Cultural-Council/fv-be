from django.contrib import admin

from backend.admin.base_admin import (
    BaseControlledSiteContentAdmin,
    FilterAutocompleteBySiteMixin,
)
from backend.models.page import SitePage


@admin.register(SitePage)
class SitePageAdmin(FilterAutocompleteBySiteMixin, BaseControlledSiteContentAdmin):
    list_display = ("title", "slug") + BaseControlledSiteContentAdmin.list_display
    search_fields = (
        "title",
        "widgets__widgets__title",
        "site__title",
    ) + BaseControlledSiteContentAdmin.search_fields
    autocomplete_fields = ("widgets", "banner_image", "banner_video")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("site", "created_by", "last_modified_by")

    def get_search_results(
        self, request, queryset, search_term, referer_models_list=None
    ):
        queryset, use_distinct = super().get_search_results(
            request, queryset, search_term, ["sitepage"]
        )
        return queryset, use_distinct
