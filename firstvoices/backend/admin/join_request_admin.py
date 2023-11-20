from django.contrib import admin

from backend.models.join_request import JoinRequest

from .base_admin import BaseSiteContentAdmin


@admin.register(JoinRequest)
class JoinRequestAdmin(BaseSiteContentAdmin):
    list_display = ("user", "status") + BaseSiteContentAdmin.list_display
    search_fields = ("user__email", "site__title")
    autocomplete_fields = ("site", "user")
