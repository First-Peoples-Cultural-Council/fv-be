from django.contrib import admin
from django.utils.translation import gettext as _

from .base_admin import BaseInlineAdmin
from .sites_admin import MembershipAdmin
from fv_be.app.models.dictionary import DictionaryEntry, Note, Acknowledgement, Translation,\
    AlternateSpelling, Pronunciation
from fv_be.app.models.category import Category


class AdminHideUtility(admin.ModelAdmin):
    def get_model_perms(self, request):
        """
        Return emtpy dict to hide the model, but registration is required so as the reverse admin links
        along with the editing functionality work.
        """
        return {}


class DictionaryContentInlineAdmin(BaseInlineAdmin):
    fields = ("text", "site") + BaseInlineAdmin.fields
    readonly_fields = ("site",) + BaseInlineAdmin.readonly_fields + MembershipAdmin.readonly_fields


class NotesInline(DictionaryContentInlineAdmin):
    model = Note


class AcknowledgementInline(DictionaryContentInlineAdmin):
    model = Acknowledgement


class TranslationInline(DictionaryContentInlineAdmin):
    model = Translation
    fields = ("language", "part_of_speech", ) + DictionaryContentInlineAdmin.fields


class AlternateSpellingInline(DictionaryContentInlineAdmin):
    model = AlternateSpelling


class PronunciationInline(DictionaryContentInlineAdmin):
    model = Pronunciation


class DictionaryEntryInline(BaseInlineAdmin):
    model = DictionaryEntry
    verbose_name = _("DictionaryEntry")
    verbose_name_plural = _("Dictionary Entries")
    fields = (
        'title',
        'type',
    ) + BaseInlineAdmin.fields
    readonly_fields = BaseInlineAdmin.readonly_fields + MembershipAdmin.readonly_fields


class CategoryInline(BaseInlineAdmin):
    model = Category
    verbose_name = _("Category")
    verbose_name_plural = _("Categories")
    fields = (
        'title',
        'parent'
    ) + BaseInlineAdmin.fields
    readonly_fields = BaseInlineAdmin.readonly_fields + MembershipAdmin.readonly_fields


class DictionaryEntryAdmin(AdminHideUtility):
    inlines = [NotesInline, AcknowledgementInline, TranslationInline, AlternateSpellingInline, PronunciationInline]
