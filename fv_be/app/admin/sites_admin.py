from django.contrib import admin

from fv_be.app.models.sites import Language, LanguageFamily, Membership

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
    fields = ("user", "site", "role", "is_trashed")
    list_display = ("user", "role") + BaseSiteContentAdmin.list_display


class MembershipInline(BaseInlineAdmin):
    model = Membership
    fields = (
        "user",
        "role",
    ) + BaseInlineAdmin.fields
    readonly_fields = BaseInlineAdmin.readonly_fields + MembershipAdmin.readonly_fields
