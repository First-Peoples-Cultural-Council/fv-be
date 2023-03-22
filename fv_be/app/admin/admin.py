from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount, SocialApp, SocialToken
from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.sites.models import Site as Sites
from rest_framework.authtoken.models import TokenProxy

from fv_be.app.models.category import Category
from fv_be.app.models.dictionary import (
    DictionaryAcknowledgement,
    AlternateSpelling,
    DictionaryEntry,
    DictionaryNote,
    Pronunciation,
    DictionaryTranslation,
)
from fv_be.app.models.part_of_speech import PartOfSpeech
from fv_be.app.models.sites import Site

from .base_admin import BaseAdmin
from .sites_admin import MembershipInline, SiteFeatureInline, SiteMenuInline
from .characters_admin import (
    CharacterInline,
    CharacterVariantInline,
    IgnoredCharacterInline,
)
from .sites_admin import MembershipInline, SiteFeatureInline
from .dictionary_admin import DictionaryEntryAdmin, CategoryAdmin, DictionaryEntryInline, CategoryInline

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
admin.site.register(DictionaryEntry, DictionaryEntryAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(PartOfSpeech)
