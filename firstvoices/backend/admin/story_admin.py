from django.contrib import admin

from backend.admin import BaseInlineAdmin, BaseSiteContentAdmin
from backend.models import Page, Story


class PageAdmin(BaseInlineAdmin):
    model = Page
    fields = ("text", "translation", "ordering", "related_audio", "related_images", "related_videos")
    list_display = ("ordering", "text")
    can_delete = True
    classes = []


@admin.register(Story)
class StoryAdmin(BaseSiteContentAdmin):

    list_display = ("title",) + BaseSiteContentAdmin.list_display
    inlines = [PageAdmin]

    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super().get_form(request, obj, change, **kwargs)
        form.base_fields["cover_image"].required = False
        return form
