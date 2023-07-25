from rest_framework import serializers

from backend.models import Image, SitePage
from backend.models.constants import Visibility
from backend.models.media import Video
from backend.models.widget import SiteWidget, SiteWidgetList
from backend.serializers.base_serializers import (
    CreateSiteContentSerializerMixin,
    SiteContentLinkedTitleSerializer,
    UpdateSerializerMixin,
)
from backend.serializers.fields import SiteHyperlinkedIdentityField
from backend.serializers.media_serializers import ImageSerializer, VideoSerializer
from backend.serializers.utils import get_site_from_context
from backend.serializers.validators import SameSite
from backend.serializers.widget_serializers import SiteWidgetListSerializer


class SitePageSerializer(SiteContentLinkedTitleSerializer):
    url = SiteHyperlinkedIdentityField(
        view_name="api:sitepage-detail", lookup_field="slug", read_only=True
    )
    slug = serializers.CharField()
    visibility = serializers.CharField(source="get_visibility_display")

    class Meta(SiteContentLinkedTitleSerializer.Meta):
        model = SitePage
        fields = SiteContentLinkedTitleSerializer.Meta.fields + (
            "visibility",
            "subtitle",
            "slug",
        )


class SitePageDetailSerializer(SitePageSerializer):
    widgets = SiteWidgetListSerializer()
    banner_image = ImageSerializer()
    banner_video = VideoSerializer()

    class Meta(SiteContentLinkedTitleSerializer.Meta):
        model = SitePage
        fields = SiteContentLinkedTitleSerializer.Meta.fields + (
            "visibility",
            "subtitle",
            "slug",
            "widgets",
            "banner_image",
            "banner_video",
        )


class SitePageDetailWriteSerializer(
    UpdateSerializerMixin, CreateSiteContentSerializerMixin, SitePageDetailSerializer
):
    widgets = serializers.PrimaryKeyRelatedField(
        queryset=SiteWidget.objects.all(),
        many=True,
    )
    banner_image = serializers.PrimaryKeyRelatedField(
        queryset=Image.objects.all(),
        allow_null=True,
        validators=[SameSite(queryset=Image.objects.all())],
    )
    banner_video = serializers.PrimaryKeyRelatedField(
        queryset=Video.objects.all(),
        allow_null=True,
        validators=[SameSite(queryset=Video.objects.all())],
    )

    def validate_widgets(self, widgets):
        if not widgets:
            raise serializers.ValidationError(
                "The widgets field must contain at least one widget ID."
            )

        site = get_site_from_context(self)
        for site_widget in widgets:
            if site_widget.site != site:
                raise serializers.ValidationError(
                    f"SiteWidget with ID ({site_widget.id}) does not belong to the site."
                )
        return widgets

    def to_representation(self, instance):
        data = SitePageDetailSerializer(instance=instance, context=self.context).data
        return data

    def create(self, validated_data):
        validated_data["visibility"] = Visibility[
            str.upper(validated_data.pop("get_visibility_display"))
        ]
        validated_data["widgets"] = SiteWidgetListSerializer.create(
            self, validated_data
        )
        created = super().create(validated_data)
        return created

    def update(self, instance, validated_data):
        widgets = instance.widgets
        if not widgets:
            widgets = SiteWidgetList.objects.create(site=instance)
        widgets = SiteWidgetListSerializer.update(self, widgets, validated_data)
        validated_data["widgets"] = widgets
        validated_data["visibility"] = Visibility[
            str.upper(validated_data.pop("get_visibility_display"))
        ]
        instance.widgets = widgets
        return super().update(instance, validated_data)
