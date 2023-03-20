from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount, SocialApp, SocialToken
from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.sites.models import Site as Sites
from rest_framework.authtoken.models import TokenProxy

from fv_be.app.models.category import Category
from fv_be.app.models.dictionary import (
    Acknowledgement,
    AlternateSpelling,
    DictionaryEntry,
    Note,
    Pronunciation,
    Translation,
)
from fv_be.app.models.part_of_speech import PartOfSpeech
from fv_be.app.models.sites import Site

from .base_admin import BaseAdmin
from .sites_admin import MembershipInline, SiteFeatureInline

dictionary_models = [
    Note,
    Acknowledgement,
    Translation,
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
        SiteFeatureInline,
    ]


admin.site.unregister(Sites)
admin.site.unregister(EmailAddress)
admin.site.unregister(TokenProxy)
admin.site.unregister(Group)
admin.site.unregister(SocialAccount)
admin.site.unregister(SocialApp)
admin.site.unregister(SocialToken)

dictionary_models = [
    Note,
    Acknowledgement,
    Translation,
    AlternateSpelling,
    Pronunciation,
    DictionaryEntry,
]
# Dictionary models
# todo: make suitable admin objects to register for each model
# todo: make custom admin forms to prevent self selection in ManyToMany fields referring to self
# ref: https://stackoverflow.com/questions/869856/
admin.site.register(dictionary_models)
admin.site.register(Category)
admin.site.register(PartOfSpeech)
