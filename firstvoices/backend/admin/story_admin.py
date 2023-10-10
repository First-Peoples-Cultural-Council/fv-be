from django.contrib import admin
from django_better_admin_arrayfield.admin.mixins import DynamicArrayMixin

from backend.admin.base_admin import BaseInlineSiteContentAdmin, BaseSiteContentAdmin
from backend.models import Story, StoryPage


class StoryPageInlineAdmin(BaseInlineSiteContentAdmin, DynamicArrayMixin):
    model = StoryPage
    fields = (
        "ordering",
        "text",
        "translation",
    ) + BaseInlineSiteContentAdmin.fields
    list_display = ("ordering", "text")
    can_delete = True
    classes = []

    def save_model(self, request, obj, form, change):
        obj.site = obj.story.site
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("story")


@admin.register(StoryPage)
class StoryPageAdmin(BaseSiteContentAdmin):
    list_display = ("story", "ordering") + BaseSiteContentAdmin.list_display
    list_select_related = ["story"] + BaseSiteContentAdmin.list_select_related
    autocomplete_fields = ("related_audio", "related_images", "related_videos")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("story", "site", "created_by", "last_modified_by")


@admin.register(Story)
class StoryAdmin(BaseSiteContentAdmin):
    list_display = ("title",) + BaseSiteContentAdmin.list_display
    inlines = [StoryPageInlineAdmin]
    autocomplete_fields = ("related_audio", "related_images", "related_videos")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            "site", "created_by", "last_modified_by"
        ).prefetch_related("pages")
