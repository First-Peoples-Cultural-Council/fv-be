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


class SiteWidgetListSerializer(serializers.ModelSerializer):
    widgets = SiteWidgetDetailSerializer(many=True)

    class Meta:
        model = SiteWidgetList
        fields = (
            "id",
            "widgets",
        )

    def to_representation(self, instance):
        widgets = []
        for widget in instance.sitewidgetlistorder_set.all():
            widgets.append(
                SiteWidgetDetailSerializer(
                    widget.site_widget, context=self.context
                ).data
            )
        return widgets
