from django.contrib import admin

from backend.models.category import Category
from backend.models.dictionary import (
    AlternateSpelling,
    DictionaryAcknowledgement,
    DictionaryEntry,
    DictionaryEntryLink,
    DictionaryNote,
    DictionaryTranslation,
    Pronunciation,
)
from backend.models.part_of_speech import PartOfSpeech

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
    readonly_fields = ("parent",) + BaseDictionaryInlineAdmin.readonly_fields
    ordering = ["title"]


@admin.register(DictionaryEntry)
class DictionaryEntryAdmin(HiddenBaseAdmin):
    inlines = [
        TranslationInline,
        AlternateSpellingInline,
        PronunciationInline,
        NotesInline,
        AcknowledgementInline,
    ]
    readonly_fields = ("custom_order",) + HiddenBaseAdmin.readonly_fields


@admin.register(PartOfSpeech)
class PartsOfSpeechAdmin(BaseAdmin):
    list_display = (
        "title",
        "parent",
    ) + BaseAdmin.list_display


# Non-customized admin forms
admin.site.register(Category, HiddenBaseAdmin)
admin.site.register(DictionaryNote, HiddenBaseAdmin)
admin.site.register(DictionaryAcknowledgement, HiddenBaseAdmin)
admin.site.register(DictionaryEntryLink, HiddenBaseAdmin)
admin.site.register(DictionaryTranslation, HiddenBaseAdmin)
admin.site.register(AlternateSpelling, HiddenBaseAdmin)
admin.site.register(Pronunciation, HiddenBaseAdmin)
