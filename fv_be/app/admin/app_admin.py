from django.contrib import admin

from fv_be.app.models.app import AppJson

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
