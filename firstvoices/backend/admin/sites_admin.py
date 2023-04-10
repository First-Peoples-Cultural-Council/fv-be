from django.contrib import admin

from backend.models.sites import (
    Language,
    LanguageFamily,
    Membership,
    SiteFeature,
    SiteMenu,
)

from .base_admin import BaseAdmin, BaseInlineAdmin, BaseSiteContentAdmin

# Admin settings for the sites models, except Site. For the main Site admin, see .admin instead.


@admin.register(LanguageFamily)
class LanguageFamilyAdmin(BaseAdmin):
    list_display = ("title", "alternate_names") + BaseAdmin.list_display
    search_fields = (
        "id",
        "title",
        "alternate_names",
    )


@admin.register(Language)
class LanguageAdmin(BaseAdmin):
    list_display = (
        "title",
        "alternate_names",
        "language_family",
        "language_code",
    ) + BaseAdmin.list_display
    search_fields = (
        "id",
        "title",
        "alternate_names",
        "language_family__title",
        "language_code",
    )
    autocomplete_fields = ("language_family",)


@admin.register(Membership)
class MembershipAdmin(BaseSiteContentAdmin):
    fields = ("user", "site", "role", "is_trashed")
    list_display = ("user", "role") + BaseSiteContentAdmin.list_display
    search_fields = (
        "id",
        "user__username",
        "site__title",
    )
    list_filter = ("role",)


@admin.register(SiteFeature)
class SiteFeatureAdmin(BaseSiteContentAdmin):
    fields = ("site", "key", "is_enabled")
    list_display = (
        "key",
        "is_enabled",
    ) + BaseSiteContentAdmin.list_display
    search_fields = (
        "id",
        "key",
        "is_enabled",
    )
    autocomplete_fields = ("site",)


@admin.register(SiteMenu)
class SiteMenuAdmin(BaseSiteContentAdmin):
    fields = ("site", "json")
    list_display = ("json",) + BaseSiteContentAdmin.list_display
    search_fields = ("site__title", "json")
    autocomplete_fields = ("site",)


class MembershipInline(BaseInlineAdmin):
    model = Membership
    fields = (
        "user",
        "role",
    ) + BaseInlineAdmin.fields
    readonly_fields = (
        ("user",) + BaseInlineAdmin.readonly_fields + MembershipAdmin.readonly_fields
    )


class SiteFeatureInline(BaseInlineAdmin):
    model = SiteFeature
    fields = (
        "key",
        "is_enabled",
    ) + BaseInlineAdmin.fields
    readonly_fields = BaseInlineAdmin.readonly_fields + MembershipAdmin.readonly_fields


class SiteMenuInline(BaseInlineAdmin):
    model = SiteMenu
    fields = ("json",) + BaseInlineAdmin.fields
    readonly_fields = BaseInlineAdmin.readonly_fields + MembershipAdmin.readonly_fields
