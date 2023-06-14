from django.contrib import admin
from django.utils.html import format_html
from embed_video.admin import AdminVideoMixin
from backend.admin import BaseSiteContentAdmin, HiddenBaseAdmin
from backend.models.media import (
    Audio,
    AudioSpeaker,
    EmbeddedVideo,
    File,
    Image,
    ImageFile,
    Person,
    Video,
)


@admin.register(File)
class FileAdmin(HiddenBaseAdmin):
    list_display = ("content", "mimetype") + HiddenBaseAdmin.list_display
    search_fields = ("content",)
    readonly_fields = ("mimetype",) + HiddenBaseAdmin.readonly_fields


@admin.register(ImageFile)
class ImageFileAdmin(HiddenBaseAdmin):
    list_display = ("content", "mimetype") + HiddenBaseAdmin.list_display
    search_fields = ("content",)
    readonly_fields = (
        "mimetype",
        "height",
        "width",
    ) + HiddenBaseAdmin.readonly_fields


@admin.register(Video)
@admin.register(Audio)
class MediaAdmin(BaseSiteContentAdmin):
    list_display = ("title",) + BaseSiteContentAdmin.list_display
    search_fields = ("title",)


@admin.register(Image)
class ImageAdmin(BaseSiteContentAdmin):
    readonly_fields = (
        "thumbnail",
        "small",
        "medium",
    ) + BaseSiteContentAdmin.readonly_fields
    list_display = ("title",) + BaseSiteContentAdmin.list_display
    search_fields = ("title",)


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
class AudioSpeakerAdmin(BaseSiteContentAdmin):
    fields = ("site", "audio", "speaker")
    list_display = ("audio", "speaker") + BaseSiteContentAdmin.list_display


@admin.register(Person)
class PersonAdmin(BaseSiteContentAdmin):
    fields = (
        "site",
        "name",
        "bio",
    )
    list_display = ("name",) + BaseSiteContentAdmin.list_display
    search_fields = ("name", "bio")
