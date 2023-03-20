from django.contrib import admin

from fv_be.app.models.sites import Language, LanguageFamily, Membership, SiteFeature

from .base_admin import BaseAdmin, BaseInlineAdmin, BaseSiteContentAdmin

# Admin settings for the sites models, except Site. For the main Site admin, see .admin instead.


@admin.register(LanguageFamily)
class LanguageFamilyAdmin(BaseAdmin):
    list_display = ("title", "alternate_names") + BaseAdmin.list_display


@admin.register(Language)
class LanguageAdmin(BaseAdmin):
    list_display = (
        "title",
        "alternate_names",
        "language_family",
        "language_code",
    ) + BaseAdmin.list_display


@admin.register(Membership)
class MembershipAdmin(BaseSiteContentAdmin):
    autocomplete_fields = (
        "user",
        "site",
    )
    fields = ("user", "site", "role", "is_trashed")
    list_display = ("user", "role") + BaseSiteContentAdmin.list_display
    search_fields = ("user", "site")


@admin.register(SiteFeature)
class SiteFeatureAdmin(BaseSiteContentAdmin):
    fields = ("site", "key", "is_enabled")
    list_display = (
        "key",
        "is_enabled",
    ) + BaseSiteContentAdmin.list_display


class MembershipInline(BaseInlineAdmin):
    model = Membership
    fields = (
        "user",
        "role",
        # "user_link"
    ) + BaseInlineAdmin.fields
    readonly_fields = (
        ("user",) + BaseInlineAdmin.readonly_fields + MembershipAdmin.readonly_fields
    )

    # def user_link(self, instance):
    #     url = reverse(
    #         "admin:users_user_change",
    #         args=(instance.user.id,),
    #     )
    #     # todo: i18n for 'Edit user' not working here for some reason
    #     return format_html('<a href="{}">{}: {}</a>', url, "Edit user", str(instance.user))


class SiteFeatureInline(BaseInlineAdmin):
    model = SiteFeature
    fields = (
        "key",
        "is_enabled",
    ) + BaseInlineAdmin.fields
    readonly_fields = BaseInlineAdmin.readonly_fields + MembershipAdmin.readonly_fields
