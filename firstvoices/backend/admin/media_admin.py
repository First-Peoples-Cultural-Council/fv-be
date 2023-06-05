from django.contrib import admin

from backend.admin import BaseSiteContentAdmin
from backend.models.media import Audio, AudioSpeaker, Image, Person, Video


@admin.register(Video)
@admin.register(Audio)
class MediaAdmin(BaseSiteContentAdmin):
    fields = (
        "site",
        "title",
        "content",
    )
    list_display = ("title",) + BaseSiteContentAdmin.list_display
    search_fields = ("title",)


@admin.register(Image)
class ImageAdmin(BaseSiteContentAdmin):
    fields = (
        "site",
        "title",
        "content",
        "thumbnail",
        "small",
        "medium",
    )
    readonly_fields = (
        "thumbnail",
        "small",
        "medium",
    )
    list_display = ("title",) + BaseSiteContentAdmin.list_display
    search_fields = ("title",)


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
