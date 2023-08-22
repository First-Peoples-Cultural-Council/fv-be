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
        "widget_type",
        "format",
    ) + BaseAdmin.list_display
    list_filter = ["widget_type", "format"]
    search_fields = (
        "title",
        "widget_type",
        "format",
    ) + BaseAdmin.search_fields
    inlines = [WidgetSettingsInline]


@admin.register(SiteWidget)
class SiteWidgetAdmin(WidgetAdmin, BaseControlledSiteContentAdmin):
    def get_queryset(self, request):
        return SiteWidget.objects.all()

    list_display = (
        "title",
        "widget_type",
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
    readonly_fields = BaseInlineAdmin.readonly_fields


@admin.register(SiteWidgetList)
class SiteWidgetListAdmin(BaseSiteContentAdmin):
    list_display = ("__str__",) + BaseSiteContentAdmin.list_display
    list_filter = ["site"]
    fields = ("site",) + BaseSiteContentAdmin.fields
    readonly_fields = BaseSiteContentAdmin.readonly_fields
    search_fields = (
        "widgets__title",
        "site__title",
    ) + BaseSiteContentAdmin.search_fields
    inlines = [SiteWidgetListOrderInline]


class HiddenSiteWidgetListOrder(HiddenBaseAdmin):
    readonly_fields = HiddenBaseAdmin.readonly_fields
    list_display = (
        "site_widget",
        "site_widget_list",
        "order",
    ) + HiddenBaseAdmin.list_display


admin.site.register(WidgetSettings, HiddenBaseAdmin)
admin.site.register(SiteWidgetListOrder, HiddenSiteWidgetListOrder)
