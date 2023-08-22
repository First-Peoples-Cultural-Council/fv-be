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


class RelatedDictionaryEntryAdminMixin:
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("dictionary_entry")


class NotesInline(RelatedDictionaryEntryAdminMixin, BaseDictionaryInlineAdmin):
    model = Note


class AcknowledgementInline(
    RelatedDictionaryEntryAdminMixin, BaseDictionaryInlineAdmin
):
    model = Acknowledgement


class TranslationInline(RelatedDictionaryEntryAdminMixin, BaseDictionaryInlineAdmin):
    model = Translation


class AlternateSpellingInline(
    RelatedDictionaryEntryAdminMixin, BaseDictionaryInlineAdmin
):
    model = AlternateSpelling


class PronunciationInline(RelatedDictionaryEntryAdminMixin, BaseDictionaryInlineAdmin):
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

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("parent")


class DictionaryEntryCharacterInline(RelatedDictionaryEntryAdminMixin, BaseInlineAdmin):
    model = DictionaryEntryRelatedCharacter
    fields = ("character",) + BaseInlineAdmin.fields


class DictionaryEntryCategoryInline(RelatedDictionaryEntryAdminMixin, BaseInlineAdmin):
    model = DictionaryEntryCategory
    fields = ("category",) + BaseInlineAdmin.fields


class DictionaryEntryLinkInline(RelatedDictionaryEntryAdminMixin, BaseInlineAdmin):
    model = DictionaryEntryLink
    fk_name = "from_dictionary_entry"
    fields = ("to_dictionary_entry",) + BaseInlineAdmin.fields


class WordOfTheDayInline(RelatedDictionaryEntryAdminMixin, BaseInlineAdmin):
    model = WordOfTheDay
    fields = (
        "dictionary_entry",
        "date",
    ) + BaseInlineAdmin.fields


@admin.register(DictionaryEntry)
class DictionaryEntryAdmin(BaseSiteContentAdmin):
    inlines = [
        TranslationInline,
        AlternateSpellingInline,
        PronunciationInline,
        NotesInline,
        AcknowledgementInline,
    ]
    list_display = ("title",) + BaseSiteContentAdmin.list_display
    readonly_fields = ("custom_order",) + BaseSiteContentAdmin.readonly_fields


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
admin.site.register(WordOfTheDay, HiddenBaseAdmin)
