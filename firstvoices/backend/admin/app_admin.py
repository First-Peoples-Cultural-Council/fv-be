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
        "user",
        "role",
    )


@admin.register(AppImportStatus)
class AppImportStatusAdmin(BaseAdmin):
    fields = (
        "label",
        "warnings",
        "successful",
    )
    list_display = (
        "label",
        "warnings",
        "successful",
    ) + BaseAdmin.list_display
    search_fields = ("label",)
