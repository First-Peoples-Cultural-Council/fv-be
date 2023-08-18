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
    BaseInlineAdmin,
    BaseSiteContentAdmin,
    HiddenBaseAdmin,
)


class BaseDictionaryInlineAdmin(BaseInlineAdmin):
    fields = ("text",) + BaseInlineAdmin.fields

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("dictionary_entry")


class NotesInline(BaseDictionaryInlineAdmin):
    model = Note


class AcknowledgementInline(BaseDictionaryInlineAdmin):
    model = Acknowledgement


class TranslationInline(BaseDictionaryInlineAdmin):
    model = Translation


class AlternateSpellingInline(BaseDictionaryInlineAdmin):
    model = AlternateSpelling


class PronunciationInline(BaseDictionaryInlineAdmin):
    model = Pronunciation


class DictionaryEntryInline(BaseDictionaryInlineAdmin):
    model = DictionaryEntry
    fields = (
        "title",
        "type",
    ) + BaseInlineAdmin.fields


class CategoryInline(BaseDictionaryInlineAdmin):
    model = Category
    fields = ("title", "parent") + BaseInlineAdmin.fields
    readonly_fields = ("parent",) + BaseDictionaryInlineAdmin.readonly_fields
    ordering = ["title"]


class DictionaryEntryCharacterInline(BaseInlineAdmin):
    model = DictionaryEntryRelatedCharacter
    fields = ("character",) + BaseInlineAdmin.fields

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("dictionary_entry")


class DictionaryEntryCategoryInline(BaseInlineAdmin):
    model = DictionaryEntryCategory
    fields = ("category",) + BaseInlineAdmin.fields

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("dictionary_entry")


class DictionaryEntryLinkInline(BaseInlineAdmin):
    model = DictionaryEntryLink
    fk_name = "from_dictionary_entry"
    fields = ("to_dictionary_entry",) + BaseInlineAdmin.fields

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("from_dictionary_entry")


class WordOfTheDayInline(BaseInlineAdmin):
    model = WordOfTheDay
    fields = (
        "dictionary_entry",
        "date",
    ) + BaseInlineAdmin.fields

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("dictionary_entry")


@admin.register(DictionaryEntry)
class DictionaryEntryAdmin(BaseSiteContentAdmin):
    inlines = [
        DictionaryEntryCategoryInline,
        TranslationInline,
        AlternateSpellingInline,
        PronunciationInline,
        NotesInline,
        AcknowledgementInline,
        DictionaryEntryLinkInline,
        DictionaryEntryCharacterInline,
    ]
    list_display = ("title",) + BaseSiteContentAdmin.list_display
    readonly_fields = ("custom_order",) + BaseSiteContentAdmin.readonly_fields


@admin.register(PartOfSpeech)
class PartsOfSpeechAdmin(BaseAdmin):
    list_display = (
        "title",
        "parent",
    ) + BaseAdmin.list_display


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
admin.site.register(WordOfTheDay, HiddenBaseAdmin)
