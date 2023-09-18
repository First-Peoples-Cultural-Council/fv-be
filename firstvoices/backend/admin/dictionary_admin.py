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


class WordOfTheDayInline(RelatedDictionaryEntryAdminMixin, BaseInlineSiteContentAdmin):
    model = WordOfTheDay
    fields = (
        "dictionary_entry",
        "date",
    ) + BaseInlineAdmin.fields

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "dictionary_entry":
            kwargs["queryset"] = DictionaryEntry.objects.filter(
                site=self.get_site_from_object(request)
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(DictionaryEntry)
class DictionaryEntryAdmin(BaseControlledSiteContentAdmin):
    inlines = [
        TranslationInline,
        AlternateSpellingInline,
        PronunciationInline,
        NotesInline,
        AcknowledgementInline,
    ]
    list_display = ("title",) + BaseControlledSiteContentAdmin.list_display
    readonly_fields = ("custom_order",) + BaseControlledSiteContentAdmin.readonly_fields
    filter_horizontal = ("related_audio", "related_images", "related_videos")


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
