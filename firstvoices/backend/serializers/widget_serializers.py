from rest_framework import serializers

from backend.models.widget import SiteWidget, SiteWidgetList, Widget, WidgetSettings
from backend.serializers.base_serializers import SiteContentLinkedTitleSerializer
from backend.serializers.fields import SiteHyperlinkedIdentityField


class WidgetSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = WidgetSettings
        fields = ("key", "value")


class WidgetDetailSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="api:widget-detail")
    type = serializers.CharField(source="widget_type")
    format = serializers.CharField(source="get_format_display")
    settings = WidgetSettingsSerializer(source="widgetsettings_set", many=True)

    class Meta:
        model = Widget
        fields = ("url", "id", "title", "type", "format", "settings")


class SiteWidgetDetailSerializer(
    SiteContentLinkedTitleSerializer, WidgetDetailSerializer
):
    url = SiteHyperlinkedIdentityField(view_name="api:sitewidget-detail")
    visibility = serializers.CharField(source="get_visibility_display")

    class Meta(SiteContentLinkedTitleSerializer.Meta):
        model = SiteWidget
        fields = SiteContentLinkedTitleSerializer.Meta.fields + (
            "visibility",
            "type",
            "format",
            "settings",
        )


class SiteWidgetListOrderDetailSerializer(SiteWidgetDetailSerializer):
    order = serializers.SerializerMethodField()

    class Meta(SiteWidgetDetailSerializer.Meta):
        model = SiteWidget
        fields = (
            "id",
            "order",
            "title",
            "widget_type",
            "format",
            "visibility",
            "settings",
        )

    def get_order(self, widget):
        return widget.sitewidgetlistorder_set.all().first().order


class SiteWidgetListSerializer(serializers.ModelSerializer):
    widgets = SiteWidgetListOrderDetailSerializer(many=True)

    class Meta:
        model = SiteWidgetList
        fields = ("id", "widgets")
