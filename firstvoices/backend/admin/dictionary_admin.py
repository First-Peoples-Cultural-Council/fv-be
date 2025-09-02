from django.contrib import admin

from backend.models.category import Category
from backend.models.dictionary import (
    DictionaryEntry,
    DictionaryEntryCategory,
    DictionaryEntryLink,
    DictionaryEntryRelatedCharacter,
    ExternalDictionaryEntrySystem,
    WordOfTheDay,
)
from backend.models.part_of_speech import PartOfSpeech

from .base_admin import (
    BaseAdmin,
    BaseControlledSiteContentAdmin,
    BaseSiteContentAdmin,
    FilterAutocompleteBySiteMixin,
    HiddenBaseAdmin,
)


@admin.register(WordOfTheDay)
class WordOfTheDayAdmin(FilterAutocompleteBySiteMixin, BaseSiteContentAdmin):
    model = WordOfTheDay
    readonly_fields = ("site",) + BaseSiteContentAdmin.readonly_fields
    autocomplete_fields = ("dictionary_entry",)


@admin.register(DictionaryEntry)
class DictionaryEntryAdmin(
    FilterAutocompleteBySiteMixin, BaseControlledSiteContentAdmin, HiddenBaseAdmin
):
    # Read-only admin form to support auto-complete in character and word-of-the-day admin forms,
    # can be removed once related forms are also removed
    list_display = ("title",) + BaseControlledSiteContentAdmin.list_display
    readonly_fields = (
        "site",
        "visibility",
        "title",
        "type",
        "custom_order",
    ) + BaseControlledSiteContentAdmin.readonly_fields
    search_fields = (
        "title",
        "site__title",
        "created_by__email",
        "last_modified_by__email",
    )
    exclude = [
        "exclude_from_games",
        "exclude_from_kids",
        "related_audio",
        "related_documents",
        "related_images",
        "related_videos",
        "legacy_batch_filename",
        "exclude_from_wotd",
        "part_of_speech",
        "split_chars_base",
    ]

    def get_search_results(
        self, request, queryset, search_term, referer_models_list=None
    ):
        queryset, use_distinct = super().get_search_results(
            request, queryset, search_term, ["wordoftheday", "site", "character"]
        )
        return queryset, use_distinct


@admin.register(PartOfSpeech)
class PartsOfSpeechAdmin(BaseAdmin):
    list_display = (
        "title",
        "parent",
    ) + BaseAdmin.list_display

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("parent")


@admin.register(ExternalDictionaryEntrySystem)
class ExternalDictionaryEntrySystemAdmin(BaseAdmin):
    list_display = ("title",) + BaseAdmin.list_display


# Non-customized admin forms
admin.site.register(Category, HiddenBaseAdmin)
admin.site.register(DictionaryEntryLink, HiddenBaseAdmin)
admin.site.register(DictionaryEntryCategory, HiddenBaseAdmin)
admin.site.register(DictionaryEntryRelatedCharacter, HiddenBaseAdmin)
