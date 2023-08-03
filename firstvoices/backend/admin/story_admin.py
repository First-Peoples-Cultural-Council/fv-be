from django.contrib import admin

from backend.admin import BaseInlineAdmin, BaseSiteContentAdmin
from backend.models import Story, StoryPage


class StoryPageAdmin(BaseInlineAdmin):
    model = StoryPage
    fields = (
        "site",
        "text",
        "translation",
        "ordering",
        "related_audio",
        "related_images",
        "related_videos",
    ) + BaseInlineAdmin.fields
    list_display = ("ordering", "text")
    can_delete = True
    classes = []


@admin.register(Story)
class StoryAdmin(BaseSiteContentAdmin):
    list_display = ("title",) + BaseSiteContentAdmin.list_display
    inlines = [StoryPageAdmin]
