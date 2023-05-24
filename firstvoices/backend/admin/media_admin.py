from django.contrib import admin

from backend.admin import BaseSiteContentAdmin
from backend.models.media import Image


@admin.register(Image)
class ImageAdmin(BaseSiteContentAdmin):
    fields = (
        "site",
        "title",
        "content",
    )
    list_display = ("title",) + BaseSiteContentAdmin.list_display
    search_fields = ("title",)
