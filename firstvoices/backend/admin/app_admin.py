from django.contrib import admin

from backend.models.app import AppImportStatus, AppJson, AppMembership

from .base_admin import BaseAdmin


@admin.register(AppJson)
class AppJsonAdmin(BaseAdmin):
    fields = (
        "key",
        "json",
    )
    list_display = (
        "key",
        "json",
    ) + BaseAdmin.list_display
    search_fields = (
        "key",
        "json",
    )


@admin.register(AppMembership)
class AppMembershipAdmin(BaseAdmin):
    fields = (
        "user",
        "role",
    )
    list_display = (
        "user",
        "role",
    ) + BaseAdmin.list_display
    search_fields = (
        "user__email",
        "role",
    )
    autocomplete_fields = ("user",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("user", "created_by", "last_modified_by")


@admin.register(AppImportStatus)
class AppImportStatusAdmin(BaseAdmin):
    fields = (
        "label",
        "no_warnings",
        "successful",
    )
    list_display = (
        "label",
        "no_warnings",
        "successful",
    ) + BaseAdmin.list_display
    readonly_fields = (
        "label",
        "no_warnings",
        "successful",
    ) + BaseAdmin.readonly_fields
    search_fields = ("label",)
