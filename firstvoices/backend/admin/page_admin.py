from django.contrib import admin

from backend.admin.base_admin import BaseControlledSiteContentAdmin
from backend.models.page import SitePage


@admin.register(SitePage)
class SitePageAdmin(BaseControlledSiteContentAdmin):
    list_display = ("title", "slug") + BaseControlledSiteContentAdmin.list_display
    list_filter = ["site"]
    search_fields = (
        "title",
        "widgets__widgets__title",
        "site__title",
    ) + BaseControlledSiteContentAdmin.search_fields
