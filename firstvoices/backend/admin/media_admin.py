from django.contrib import admin
from django.utils.html import format_html
from embed_video.admin import AdminVideoMixin

from backend.admin import BaseAdmin, BaseSiteContentAdmin, HiddenBaseAdmin
from backend.admin.base_admin import FilterAutocompleteBySiteMixin
from backend.models.media import (
    Audio,
    AudioSpeaker,
    EmbeddedVideo,
    File,
    Image,
    ImageFile,
    Person,
    Video,
    VideoFile,
)


@admin.register(File)
class FileAdmin(FilterAutocompleteBySiteMixin, HiddenBaseAdmin):
    list_display = ("content", "mimetype") + HiddenBaseAdmin.list_display
    search_fields = ("content",)
    readonly_fields = ("mimetype", "size") + HiddenBaseAdmin.readonly_fields

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("site", "created_by", "last_modified_by")

    def delete_queryset(self, request, queryset):
        for obj in queryset.all():
            obj.delete()

    def get_search_results(
        self, request, queryset, search_term, referer_models_list=None
    ):
        queryset, use_distinct = super().get_search_results(
            request, queryset, search_term, ["audio", "image", "video"]
        )
        return queryset, use_distinct


@admin.register(ImageFile)
@admin.register(VideoFile)
class VisualMediaFileAdmin(FileAdmin):
    readonly_fields = (
        "height",
        "width",
    ) + FileAdmin.readonly_fields


@admin.register(Audio)
class AudioAdmin(FilterAutocompleteBySiteMixin, BaseSiteContentAdmin):
    list_display = ("title",) + BaseSiteContentAdmin.list_display
    search_fields = ("title", "site__title")
    autocomplete_fields = ("original",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("site", "created_by", "last_modified_by")

    def delete_queryset(self, request, queryset):
        for obj in queryset.all():
            obj.delete()

    def get_search_results(
        self, request, queryset, search_term, referer_models_list=None
    ):
        queryset, use_distinct = super().get_search_results(
            request,
            queryset,
            search_term,
            ["site", "storypage", "song", "dictionaryentry", "character", "story"],
        )
        return queryset, use_distinct


@admin.register(Image)
@admin.register(Video)
class VisualMediaAdmin(FilterAutocompleteBySiteMixin, BaseSiteContentAdmin):
    readonly_fields = (
        "thumbnail",
        "small",
        "medium",
    ) + BaseSiteContentAdmin.readonly_fields
    list_display = ("title",) + BaseSiteContentAdmin.list_display
    search_fields = ("title",)
    autocomplete_fields = ("original",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("site", "created_by", "last_modified_by")

    def delete_queryset(self, request, queryset):
        for obj in queryset.all():
            obj.delete()

    def get_search_results(
        self, request, queryset, search_term, referer_models_list=None
    ):
        queryset, use_distinct = super().get_search_results(
            request,
            queryset,
            search_term,
            [
                "site",
                "sitepage",
                "storypage",
                "song",
                "dictionaryentry",
                "character",
                "story",
            ],
        )
        return queryset, use_distinct


@admin.register(EmbeddedVideo)
class EmbeddedVideoAdmin(BaseSiteContentAdmin, AdminVideoMixin):
    fields = (
        "site",
        "title",
        "content",
    )
    list_display = (
        "title",
        "content_url",
    ) + BaseSiteContentAdmin.list_display
    search_fields = (
        "title",
        "content",
    )

    def content_url(self, obj):
        return format_html("<a href='{url}'>{url}</a>", url=obj.content)


@admin.register(AudioSpeaker)
class AudioSpeakerAdmin(BaseAdmin):
    fields = ("audio", "speaker")
    list_display = ("audio", "speaker") + BaseAdmin.list_display
    list_select_related = (
        "audio",
        "audio__site",
        "speaker",
        "speaker__site",
        "created_by",
        "last_modified_by",
    )
    autocomplete_fields = ("audio", "speaker")


@admin.register(Person)
class PersonAdmin(BaseSiteContentAdmin):
    fields = (
        "site",
        "name",
        "bio",
    )
    list_display = ("name",) + BaseSiteContentAdmin.list_display
    search_fields = ("name", "bio")
