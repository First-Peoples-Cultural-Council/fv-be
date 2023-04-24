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
from backend.models.sites import Site

from .base_admin import BaseAdmin, HiddenBaseAdmin
from .characters_admin import (
    CharacterInline,
    CharacterVariantInline,
    IgnoredCharacterInline,
)
from .dictionary_admin import (
    CategoryInline,
    DictionaryEntryHiddenBaseAdmin,
    DictionaryEntryInline,
    PartsOfSpeechAdmin,
)
from .sites_admin import MembershipInline, SiteFeatureInline, SiteMenuInline

dictionary_models = [
    DictionaryNote,
    DictionaryAcknowledgement,
    DictionaryTranslation,
    AlternateSpelling,
    Pronunciation,
    DictionaryEntry,
]

# Main Site admin settings. For related sites models, see .sites_admin


@admin.register(Site)
class SiteAdmin(BaseAdmin):
    list_display = (
        "title",
        "slug",
        "visibility",
        "language_family",
    ) + BaseAdmin.list_display
    inlines = [
        MembershipInline,
        CharacterInline,
        CharacterVariantInline,
        IgnoredCharacterInline,
        SiteFeatureInline,
        SiteMenuInline,
        DictionaryEntryInline,
        CategoryInline,
    ]
    search_fields = ("id", "title", "slug", "language__title", "contact_email")
    autocomplete_fields = ("language",)


# admin.site.unregister(Group)

# Dictionary models
admin.site.register(DictionaryEntry, DictionaryEntryHiddenBaseAdmin)
admin.site.register(Category, HiddenBaseAdmin)
admin.site.register(DictionaryNote, HiddenBaseAdmin)
admin.site.register(DictionaryAcknowledgement, HiddenBaseAdmin)
admin.site.register(DictionaryEntryLink, HiddenBaseAdmin)
admin.site.register(DictionaryTranslation, HiddenBaseAdmin)
admin.site.register(AlternateSpelling, HiddenBaseAdmin)
admin.site.register(Pronunciation, HiddenBaseAdmin)
admin.site.register(PartOfSpeech, PartsOfSpeechAdmin)
