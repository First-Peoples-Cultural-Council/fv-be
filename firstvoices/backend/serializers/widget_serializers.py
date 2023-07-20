from rest_framework import serializers

from backend.models.widget import (
    SiteWidget,
    SiteWidgetList,
    SiteWidgetListOrder,
    Widget,
    WidgetSettings, WidgetFormats,
)
from backend.serializers.base_serializers import (
    SiteContentLinkedTitleSerializer,
    UpdateSerializerMixin, CreateSiteContentSerializerMixin,
)
from backend.serializers.fields import SiteHyperlinkedIdentityField
from backend.serializers.utils import get_site_from_context


class WidgetSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = WidgetSettings
        fields = ("key", "value")


class WidgetDetailSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="api:widget-detail", read_only=True
    )
    type = serializers.CharField(source="widget_type", required=True)
    format = serializers.CharField(source="get_format_display", required=True)
    settings = WidgetSettingsSerializer(
        source="widgetsettings_set", many=True, required=False
    )

    class Meta:
        model = Widget
        fields = ("url", "id", "title", "type", "format", "settings")
        read_only_fields = ("id",)


class SiteWidgetDetailSerializer(
    UpdateSerializerMixin,
    CreateSiteContentSerializerMixin,
    SiteContentLinkedTitleSerializer,
    WidgetDetailSerializer,
):
    url = SiteHyperlinkedIdentityField(
        view_name="api:sitewidget-detail", read_only=True
    )
    visibility = serializers.CharField(source="get_visibility_display", read_only=True)

    class Meta(SiteContentLinkedTitleSerializer.Meta):
        model = SiteWidget
        fields = SiteContentLinkedTitleSerializer.Meta.fields + (
            "visibility",
            "type",
            "format",
            "settings",
        )

    def create(self, validated_data):
        settings = validated_data.pop("widgetsettings_set")
        validated_data["format"] = WidgetFormats[
            str.upper(validated_data.pop("get_format_display"))
        ]
        # Set the SiteWidget visibility to match the site visibility
        validated_data["visibility"] = get_site_from_context(self).visibility
        created = super().create(validated_data)

        for settings_instance in settings:
            WidgetSettings.objects.create(
                widget=created,
                key=settings_instance["key"],
                value=settings_instance["value"],
            )
        return created

    def update(self, instance, validated_data):
        WidgetSettings.objects.filter(widget__id=instance.id).delete()
        settings = validated_data.pop("widgetsettings_set")
        validated_data["format"] = WidgetFormats[
            str.upper(validated_data.pop("get_format_display"))
        ]
        # Set the SiteWidget visibility to match the site visibility
        validated_data["visibility"] = get_site_from_context(self).visibility
        for setting in settings:
            WidgetSettings.objects.create(
                widget=instance, key=setting["key"], value=setting["value"]
            )

        return super().update(instance, validated_data)


class SiteWidgetListSerializer(serializers.ModelSerializer, UpdateSerializerMixin):
    widgets = SiteWidgetDetailSerializer(many=True)

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
            # Check that each SiteWidget belongs to the same site as the homepage
            if widget.site != get_site_from_context(self):
                raise serializers.ValidationError(
                    f"SiteWidget with ID ({widget.id}) does not belong to the site."
                )
            SiteWidgetListOrder.objects.create(
                site_widget=widget,
                site_widget_list=new_site_widget_list,
                order=index,
                last_modified_by=self.context["request"].user,
                created_by=self.context["request"].user,
            )

        return SiteWidgetList.objects.get(id=instance.id)
