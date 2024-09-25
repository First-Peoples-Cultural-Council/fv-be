from django.contrib import admin

from backend.models.sites import (
    Language,
    LanguageFamily,
    Membership,
    SiteFeature,
    SiteMenu,
)

from ..search.tasks.site_content_indexing_tasks import (
    request_sync_all_media_site_content_in_indexes,
)
from .base_admin import BaseAdmin, BaseSiteContentAdmin

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

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("language_family", "created_by", "last_modified_by")


@admin.register(Membership)
class MembershipAdmin(BaseSiteContentAdmin):
    fields = ("user", "site", "role")
    list_display = ("user", "role") + BaseSiteContentAdmin.list_display
    search_fields = (
        "id",
        "user__email",
        "site__title",
    )
    list_filter = ("role",) + BaseSiteContentAdmin.list_filter
    list_select_related = ("user", "site", "created_by", "last_modified_by")
    autocomplete_fields = ("user", "site")


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

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        request_sync_all_media_site_content_in_indexes(obj.site)

    def delete_model(self, request, obj):
        super().delete_model(request, obj)
        request_sync_all_media_site_content_in_indexes(obj.site)


@admin.register(SiteMenu)
class SiteMenuAdmin(BaseSiteContentAdmin):
    fields = ("site", "json")
    list_display = ("json",) + BaseSiteContentAdmin.list_display
    search_fields = ("site__title", "json")
    autocomplete_fields = ("site",)
    list_filter = ()
