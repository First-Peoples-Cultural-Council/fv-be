from django.contrib import admin
from django.contrib.auth.models import Group

from backend.models.sites import Site

from .base_admin import BaseAdmin
from .characters_admin import (
    CharacterInline,
    CharacterVariantInline,
    IgnoredCharacterInline,
)
from .dictionary_admin import CategoryInline, DictionaryEntryInline
from .sites_admin import MembershipInline, SiteFeatureInline, SiteMenuInline

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


admin.site.unregister(Group)
