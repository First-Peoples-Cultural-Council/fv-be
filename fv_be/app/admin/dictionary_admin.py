from django.contrib import admin
from django.utils.translation import gettext as _

from .base_admin import BaseAdmin, BaseInlineAdmin, AdminHideUtility
from .sites_admin import MembershipAdmin
from fv_be.app.models.dictionary import DictionaryEntry, Note, Acknowledgement, Translation,\
    AlternateSpelling, Pronunciation
from fv_be.app.models.category import Category


class BaseDictionaryInlineAdmin(BaseInlineAdmin):
    fields = ("text", "site") + BaseInlineAdmin.fields
    readonly_fields = ("site",) + BaseInlineAdmin.readonly_fields + MembershipAdmin.readonly_fields


class NotesInline(BaseDictionaryInlineAdmin):
    model = Note


class AcknowledgementInline(BaseDictionaryInlineAdmin):
    model = Acknowledgement


class TranslationInline(BaseDictionaryInlineAdmin):
    model = Translation
    fields = ("language", "part_of_speech", ) + BaseDictionaryInlineAdmin.fields


class AlternateSpellingInline(BaseDictionaryInlineAdmin):
    model = AlternateSpelling


class PronunciationInline(BaseDictionaryInlineAdmin):
    model = Pronunciation


class DictionaryEntryInline(BaseDictionaryInlineAdmin):
    model = DictionaryEntry
    fields = (
        'title',
        'type',
    ) + BaseInlineAdmin.fields


class CategoryInline(BaseDictionaryInlineAdmin):
    model = Category
    fields = (
        'title',
        'parent'
    ) + BaseInlineAdmin.fields


class DictionaryEntryAdmin(AdminHideUtility):
    inlines = [NotesInline, AcknowledgementInline, TranslationInline, AlternateSpellingInline, PronunciationInline]
