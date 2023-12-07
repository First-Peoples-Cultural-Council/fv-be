from django.contrib import admin

from backend.models.category import Category
from backend.models.dictionary import (
    Acknowledgement,
    AlternateSpelling,
    DictionaryEntry,
    DictionaryEntryCategory,
    DictionaryEntryLink,
    DictionaryEntryRelatedCharacter,
    Note,
    Pronunciation,
    Translation,
    WordOfTheDay,
)
from backend.models.part_of_speech import PartOfSpeech

from .base_admin import (
    BaseAdmin,
    BaseControlledSiteContentAdmin,
    BaseInlineAdmin,
    BaseInlineSiteContentAdmin,
    FilterAutocompleteBySiteMixin,
    HiddenBaseAdmin,
)


class WordOfTheDayInline(BaseInlineSiteContentAdmin):
    model = WordOfTheDay
    fields = (
        "dictionary_entry",
        "date",
    ) + BaseInlineAdmin.fields
    autocomplete_fields = ("dictionary_entry",)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "dictionary_entry":
            kwargs["queryset"] = DictionaryEntry.objects.filter(
                site=self.get_site_from_object(request)
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("dictionary_entry")


@admin.register(WordOfTheDay)
class WordOfTheDayAdmin(FilterAutocompleteBySiteMixin, HiddenBaseAdmin):
    model = WordOfTheDay
    readonly_fields = ("site",) + HiddenBaseAdmin.readonly_fields
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
        "related_images",
        "related_videos",
        "batch_id",
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


# Non-customized admin forms
admin.site.register(Category, HiddenBaseAdmin)
admin.site.register(Note, HiddenBaseAdmin)
admin.site.register(Acknowledgement, HiddenBaseAdmin)
admin.site.register(DictionaryEntryLink, HiddenBaseAdmin)
admin.site.register(DictionaryEntryCategory, HiddenBaseAdmin)
admin.site.register(DictionaryEntryRelatedCharacter, HiddenBaseAdmin)
admin.site.register(Translation, HiddenBaseAdmin)
admin.site.register(AlternateSpelling, HiddenBaseAdmin)
admin.site.register(Pronunciation, HiddenBaseAdmin)
