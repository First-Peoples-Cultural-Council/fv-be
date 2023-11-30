from django.contrib import admin

from backend.models.immersion_labels import ImmersionLabel

from .base_admin import BaseSiteContentAdmin


@admin.register(ImmersionLabel)
class ImmersionLabelAdmin(BaseSiteContentAdmin):
    list_display = ("key", "dictionary_entry") + BaseSiteContentAdmin.list_display
    search_fields = ("key",)
