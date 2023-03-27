from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount, SocialApp, SocialToken
from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.sites.models import Site as Sites
from rest_framework.authtoken.models import TokenProxy

from firstvoices.backend.models.category import Category
from firstvoices.backend.models.dictionary import (
    AlternateSpelling,
    DictionaryAcknowledgement,
    DictionaryEntry,
    DictionaryNote,
    DictionaryTranslation,
    Pronunciation,
)
from firstvoices.backend.models.part_of_speech import PartOfSpeech
from firstvoices.backend.models.sites import Site

from .base_admin import BaseAdmin, HiddenBaseAdmin
from .dictionary_admin import DictionaryEntryHiddenBaseAdmin, DictionaryEntryInline, CategoryInline
from .characters_admin import (
    CharacterInline,
    CharacterVariantInline,
    IgnoredCharacterInline,
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
        CategoryInline
    ]
    search_fields = ("id", "title", "slug", "language__title", "contact_email")
    autocomplete_fields = ("language",)


admin.site.unregister(Sites)
admin.site.unregister(EmailAddress)
admin.site.unregister(TokenProxy)
admin.site.unregister(Group)
admin.site.unregister(SocialAccount)
admin.site.unregister(SocialApp)
admin.site.unregister(SocialToken)

# Dictionary models
# todo: make suitable admin objects to register for each model
# todo: make custom admin forms to prevent self selection in ManyToMany fields referring to self
# ref: https://stackoverflow.com/questions/869856/
admin.site.register(DictionaryEntry, DictionaryEntryHiddenBaseAdmin)
admin.site.register(Category, HiddenBaseAdmin)
admin.site.register(DictionaryNote, HiddenBaseAdmin)
admin.site.register(DictionaryAcknowledgement, HiddenBaseAdmin)
admin.site.register(DictionaryTranslation, HiddenBaseAdmin)
admin.site.register(AlternateSpelling, HiddenBaseAdmin)
admin.site.register(Pronunciation, HiddenBaseAdmin)
admin.site.register(PartOfSpeech)
