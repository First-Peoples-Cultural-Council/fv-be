from django.contrib import admin

from backend.admin.base_admin import BaseControlledSiteContentAdmin
from backend.models.media import Image, Video
from backend.models.page import SitePage
from backend.models.widget import SiteWidgetList


@admin.register(SitePage)
class SitePageAdmin(BaseControlledSiteContentAdmin):
    list_display = ("title", "slug") + BaseControlledSiteContentAdmin.list_display
    list_filter = ["site"]
    search_fields = (
        "title",
        "widgets__widgets__title",
        "site__title",
    ) + BaseControlledSiteContentAdmin.search_fields

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # prefetch the media models' site info (it is used for their display name)
        if db_field.name == "banner_image":
            kwargs["queryset"] = Image.objects.select_related("site")
        if db_field.name == "banner_video":
            kwargs["queryset"] = Video.objects.select_related("site")
        if db_field.name == "widgets":
            kwargs["queryset"] = SiteWidgetList.objects.select_related("site")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
