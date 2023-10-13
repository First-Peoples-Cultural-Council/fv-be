from rest_framework import serializers

from backend.models.widget import (
    SiteWidget,
    SiteWidgetList,
    SiteWidgetListOrder,
    Widget,
    WidgetFormats,
    WidgetSettings,
)
from backend.serializers.base_serializers import (
    SiteContentLinkedTitleSerializer,
    UpdateSerializerMixin,
    WritableControlledSiteContentSerializer,
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
    WritableControlledSiteContentSerializer,
    WidgetDetailSerializer,
):
    url = SiteHyperlinkedIdentityField(
        view_name="api:sitewidget-detail", read_only=True
    )

    class Meta(SiteContentLinkedTitleSerializer.Meta):
        model = SiteWidget
        fields = WritableControlledSiteContentSerializer.Meta.fields + (
            "type",
            "format",
            "settings",
        )

    def create(self, validated_data):
        settings = validated_data.pop("widgetsettings_set") if "widgetsettings_set" in validated_data else []
        validated_data["format"] = WidgetFormats[
            str.upper(validated_data.pop("get_format_display"))
        ]
        created = super().create(validated_data)

        for settings_instance in settings:
            WidgetSettings.objects.create(
                widget=created,
                key=settings_instance["key"],
                value=settings_instance["value"],
            )
        return created

    def update(self, instance, validated_data):
        if "widgetsettings_set" in validated_data:
            WidgetSettings.objects.filter(widget__id=instance.id).delete()
            settings = validated_data.pop("widgetsettings_set")

            for setting in settings:
                WidgetSettings.objects.create(
                    widget=instance, key=setting["key"], value=setting["value"]
                )

        if "get_format_display" in validated_data:
            validated_data["format"] = WidgetFormats[
                str.upper(validated_data.pop("get_format_display"))
            ]

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
        for widget in instance.widgets.all().order_by("sitewidgetlistorder_set__order"):
            widgets.append(
                SiteWidgetDetailSerializer(widget, context=self.context).data
            )
        return widgets

    @staticmethod
    def create_site_widget_list_order_instances(
        site_widgets, site_widget_list, user, site
    ):
        # Create a new SiteWidgetListOrder object for each widget in the validated data and add it to the list.
        for index, widget in enumerate(site_widgets):
            # Check that each SiteWidget belongs to the same site as the homepage
            if widget.site != site:
                raise serializers.ValidationError(
                    f"SiteWidget with ID ({widget.id}) does not belong to the site."
                )
            SiteWidgetListOrder.objects.create(
                site_widget=widget,
                site_widget_list=site_widget_list,
                order=index,
                last_modified_by=user,
                created_by=user,
            )

    def create(self, validated_data):
        site = get_site_from_context(self)
        new_site_widget_list = SiteWidgetList.objects.create(site=site)

        # Create new SiteWidgetListOrder objects for each widget in the validated data.
        if "widgets" in validated_data:
            SiteWidgetListSerializer.create_site_widget_list_order_instances(
                validated_data["widgets"],
                new_site_widget_list,
                self.context["request"].user,
                site,
            )

        validated_data["widgets"] = new_site_widget_list

        return new_site_widget_list

    def update(self, instance, validated_data):
        site = get_site_from_context(self)
        new_site_widget_list = instance

        # Remove existing widgets from the list.
        for item in SiteWidgetListOrder.objects.filter(
            site_widget__in=new_site_widget_list.widgets.all()
        ):
            item.delete()

        # Create new SiteWidgetListOrder objects for each widget in the validated data.
        if "widgets" in validated_data:
            SiteWidgetListSerializer.create_site_widget_list_order_instances(
                validated_data["widgets"],
                new_site_widget_list,
                self.context["request"].user,
                site,
            )

        return SiteWidgetList.objects.get(id=instance.id)
