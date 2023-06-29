from django.contrib import admin

from backend.admin import BaseAdmin
from backend.admin.base_admin import (
    BaseControlledSiteContentAdmin,
    BaseInlineAdmin,
    BaseSiteContentAdmin,
    HiddenBaseAdmin,
)
from backend.models.widget import (
    SiteWidget,
    SiteWidgetList,
    SiteWidgetListOrder,
    Widget,
    WidgetSettings,
)


class WidgetSettingsInline(BaseInlineAdmin):
    model = WidgetSettings
    fields = ("key", "value") + BaseInlineAdmin.fields


@admin.register(Widget)
class WidgetAdmin(BaseAdmin):
    def get_queryset(self, request):
        return Widget.objects.all().exclude(pk__in=SiteWidget.objects.all())

    list_display = (
        "title",
        "type",
        "format",
    ) + BaseAdmin.list_display
    list_filter = ["type", "format"]
    search_fields = (
        "title",
        "type",
        "format",
    ) + BaseAdmin.search_fields
    inlines = [WidgetSettingsInline]


@admin.register(SiteWidget)
class SiteWidgetAdmin(WidgetAdmin, BaseControlledSiteContentAdmin):
    def get_queryset(self, request):
        return SiteWidget.objects.all()

    list_display = (
        "title",
        "type",
        "format",
    ) + BaseControlledSiteContentAdmin.list_display
    list_filter = ["site"] + WidgetAdmin.list_filter
    search_fields = (
        WidgetAdmin.search_fields
        + ("site__title",)
        + BaseControlledSiteContentAdmin.search_fields
    )
    inlines = [WidgetSettingsInline]


class SiteWidgetListOrderInline(BaseInlineAdmin):
    model = SiteWidgetListOrder
    fields = (
        "site_widget",
        "order",
    ) + BaseInlineAdmin.fields


@admin.register(SiteWidgetList)
class SiteWidgetListAdmin(BaseSiteContentAdmin):
    list_display = ("__str__",) + BaseSiteContentAdmin.list_display
    list_filter = ["site"]
    search_fields = (
        "title",
        "widgets__title",
        "site__title",
    ) + BaseSiteContentAdmin.search_fields
    inlines = [SiteWidgetListOrderInline]


admin.site.register(WidgetSettings, HiddenBaseAdmin)
admin.site.register(SiteWidgetListOrder, HiddenBaseAdmin)
