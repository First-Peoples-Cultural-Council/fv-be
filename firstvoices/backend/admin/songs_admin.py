from django.contrib import admin

from backend.admin import BaseInlineAdmin, BaseSiteContentAdmin
from backend.models import Lyric, Song


class LyricAdmin(BaseInlineAdmin):
    model = Lyric
    fields = ("text", "translation", "ordering")
    list_display = ("ordering", "text")
    can_delete = True
    classes = []


@admin.register(Song)
class SongAdmin(BaseSiteContentAdmin):
    list_display = ("title",) + BaseSiteContentAdmin.list_display
    inlines = [LyricAdmin]

    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super().get_form(request, obj, change, **kwargs)
        form.base_fields["cover_image"].required = False
        return form
