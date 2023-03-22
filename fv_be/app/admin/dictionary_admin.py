from django.contrib import admin
from django.utils.translation import gettext as _

# Admin settings for the Dictionary related models
from .base_admin import BaseInlineAdmin
from .sites_admin import MembershipAdmin
from fv_be.app.models.dictionary import DictionaryEntry, Note
from fv_be.app.models.category import Category


class NotesInline(BaseInlineAdmin):
    model = Note
    fields = ("text", ) + BaseInlineAdmin.fields
    readonly_fields = BaseInlineAdmin.readonly_fields + MembershipAdmin.readonly_fields


class DictionaryEntryAdmin(admin.ModelAdmin):
    inlines = [NotesInline]


    def get_model_perms(self, request):
        """
        Return emtpy dict so as to hide the model, but registration is required so as the reverse admin links
        along with the editing functionality work.
        """
        return {}


class CategoryAdmin(admin.ModelAdmin):
    def get_model_perms(self, request):
        """
        Return emtpy dict so as to hide the model, but registration is required so as the reverse admin links
        along with the editing functionality work.
        """
        return {}


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
