from django.contrib import admin
from django.contrib.auth.models import Group

from fv_be.app.models.sites import LanguageFamily, Membership, Site, SiteInformation


class BaseAdmin(admin.ModelAdmin):
    readonly_fields = (
        "id",
        "created",
        "created_by",
        "last_modified_by",
        "last_modified",
    )
    list_display = (
        "id",
        "is_trashed",
        "created_by",
        "created",
        "last_modified_by",
        "last_modified",
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user

        obj.last_modified_by = request.user
        super().save_model(request, obj, form, change)


class BaseSiteContentAdmin(BaseAdmin):
    list_display = ("site",) + BaseAdmin.list_display


class BaseControlledSiteContentAdmin(BaseSiteContentAdmin):
    list_display = ("visibility",) + BaseSiteContentAdmin.list_display


class LanguageFamilyAdmin(BaseAdmin):
    list_display = ("title",) + BaseAdmin.list_display


class SiteAdmin(BaseAdmin):
    list_display = (
        "title",
        "slug",
        "visibility",
        "language_family",
    ) + BaseAdmin.list_display


class SiteInformationAdmin(BaseAdmin):
    list_display = (
        "site",
        "contact_information",
        "greeting",
        "about_our_language",
        "about_us",
        "description",
        "site_menu",
    ) + BaseAdmin.list_display


class MembershipAdmin(BaseSiteContentAdmin):
    list_display = ("user", "role") + BaseSiteContentAdmin.list_display


admin.site.register(Membership, MembershipAdmin)
admin.site.register(LanguageFamily, LanguageFamilyAdmin)
admin.site.register(Site, SiteAdmin)
admin.site.register(SiteInformation, SiteInformationAdmin)

admin.site.unregister(Group)
