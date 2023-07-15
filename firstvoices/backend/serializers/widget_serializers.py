from rest_framework import serializers

from backend.models.widget import (
    SiteWidget,
    SiteWidgetList,
    SiteWidgetListOrder,
    Widget,
    WidgetSettings,
)
from backend.serializers.base_serializers import (
    SiteContentLinkedTitleSerializer,
    UpdateSerializerMixin,
)
from backend.serializers.fields import SiteHyperlinkedIdentityField
from backend.serializers.validators import SameSite


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


class SiteWidgetListSerializer(serializers.ModelSerializer, UpdateSerializerMixin):
    widgets = SiteWidgetDetailSerializer(
        many=True, validators=[SameSite(queryset=SiteWidget.objects.all())]
    )

    class Meta:
        model = SiteWidgetList
        fields = (
            "id",
            "widgets",
        )

    def to_representation(self, instance):
        widgets = []
        for widget in instance.widgets.all():
            widgets.append(
                SiteWidgetDetailSerializer(widget, context=self.context).data
            )
        return widgets

    def update(self, instance, validated_data):
        new_site_widget_list = instance

        # Remove existing widgets from the list.
        for item in SiteWidgetListOrder.objects.filter(
            site_widget__in=new_site_widget_list.widgets.all()
        ):
            item.delete()

        # Create a new SiteWidgetListOrder object for each widget in the validated data and add it to the list.
        for index, widget in enumerate(validated_data["homepage"]):
            SiteWidgetListOrder.objects.create(
                site_widget=widget,
                site_widget_list=new_site_widget_list,
                order=index,
                last_modified_by=self.context["request"].user,
                created_by=self.context["request"].user,
            )

        return SiteWidgetList.objects.get(id=instance.id)
