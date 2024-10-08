from django.contrib import admin
from django.contrib.auth.models import Group
from django_better_admin_arrayfield.admin.mixins import DynamicArrayMixin

from backend.models.sites import Site

from .base_admin import BaseAdmin
from .characters_admin import (
    CharacterInline,
    CharacterVariantInline,
    IgnoredCharacterInline,
)

# Main Site admin settings. For related sites models, see .sites_admin


@admin.register(Site)
class SiteAdmin(DynamicArrayMixin, BaseAdmin):
    list_display = (
        "title",
        "slug",
        "visibility",
        "language_family",
    ) + BaseAdmin.list_display
    inlines = [
        CharacterInline,
        CharacterVariantInline,
        IgnoredCharacterInline,
    ]
    search_fields = ("id", "title", "slug", "language__title", "contact_emails")
    autocomplete_fields = (
        "language",
        "homepage",
        "logo",
        "banner_image",
        "banner_video",
        "contact_users",
    )

    def formfield_for_choice_field(self, db_field, request, **kwargs):
        if db_field.name == "visibility":
            kwargs["help_text"] = (
                "Due to potential improper elasticsearch indexing if the save action fails, please only update a "
                "site's visibility on its own and not with other changes. Note that changing a site's visibility "
                "is a potentially very expensive operation. "
            )
        return super().formfield_for_choice_field(db_field, request, **kwargs)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            "language", "language__language_family", "created_by", "last_modified_by"
        )


admin.site.unregister(Group)
