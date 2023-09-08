from django.contrib import admin
from django.contrib.auth.models import Group

from backend.models.media import Image, Video
from backend.models.sites import Site
from backend.models.widget import SiteWidgetList

from .base_admin import BaseAdmin
from .characters_admin import (
    CharacterInline,
    CharacterVariantInline,
    IgnoredCharacterInline,
)
from .dictionary_admin import CategoryInline, WordOfTheDayInline
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
        CategoryInline,
        WordOfTheDayInline,
    ]
    search_fields = ("id", "title", "slug", "language__title", "contact_email")
    autocomplete_fields = ("language",)

    def formfield_for_choice_field(self, db_field, request, **kwargs):
        if db_field.name == "visibility":
            kwargs["help_text"] = (
                "Due to potential improper elasticsearch indexing if the save action fails, please only update a "
                "site's visibility on its own and not with other changes. Note that changing a site's visibility "
                "is a potentially very expensive operation. "
            )
        return super().formfield_for_choice_field(db_field, request, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # prefetch the media models' site info (it is used for their display name)
        site_id = request.resolver_match.kwargs.get("object_id")
        if db_field.name in ("logo", "banner_image"):
            kwargs["queryset"] = Image.objects.filter(site__id=site_id).select_related(
                "site"
            )
        if db_field.name == "banner_video":
            kwargs["queryset"] = Video.objects.filter(site__id=site_id).select_related(
                "site"
            )
        if db_field.name == "homepage":
            kwargs["queryset"] = SiteWidgetList.objects.filter(
                site__id=site_id
            ).select_related("site")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


admin.site.unregister(Group)
