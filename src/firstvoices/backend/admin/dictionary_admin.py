from firstvoices.backend.models.category import Category
from firstvoices.backend.models.dictionary import (
    AlternateSpelling,
    DictionaryAcknowledgement,
    DictionaryEntry,
    DictionaryNote,
    DictionaryTranslation,
    Pronunciation,
)

from .base_admin import BaseAdmin, BaseInlineAdmin, HiddenBaseAdmin
from .sites_admin import MembershipAdmin


class BaseDictionaryInlineAdmin(BaseInlineAdmin):
    fields = ("text", "site") + BaseInlineAdmin.fields
    readonly_fields = (
        ("site",) + BaseInlineAdmin.readonly_fields + MembershipAdmin.readonly_fields
    )


class NotesInline(BaseDictionaryInlineAdmin):
    model = DictionaryNote


class AcknowledgementInline(BaseDictionaryInlineAdmin):
    model = DictionaryAcknowledgement


class TranslationInline(BaseDictionaryInlineAdmin):
    model = DictionaryTranslation
    fields = (
        "language",
        "part_of_speech",
    ) + BaseDictionaryInlineAdmin.fields


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


class DictionaryEntryHiddenBaseAdmin(HiddenBaseAdmin):
    inlines = [
        NotesInline,
        AcknowledgementInline,
        TranslationInline,
        AlternateSpellingInline,
        PronunciationInline,
    ]


class PartsOfSpeechAdmin(BaseAdmin):
    list_display = ("title",) + BaseAdmin.list_display
