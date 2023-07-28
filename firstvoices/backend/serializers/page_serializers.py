from rest_framework import serializers

from backend.models import Image, SitePage
from backend.models.constants import Visibility
from backend.models.media import Video
from backend.models.widget import SiteWidget, SiteWidgetList
from backend.serializers.base_serializers import (
    CreateControlledSiteContentSerializerMixin,
    SiteContentLinkedTitleSerializer,
    UpdateSerializerMixin,
)
from backend.serializers.fields import SiteHyperlinkedIdentityField
from backend.serializers.media_serializers import ImageSerializer, VideoSerializer
from backend.serializers.validators import SameSite
from backend.serializers.widget_serializers import SiteWidgetListSerializer


class SitePageSerializer(SiteContentLinkedTitleSerializer):
    url = SiteHyperlinkedIdentityField(
        view_name="api:sitepage-detail", lookup_field="slug", read_only=True
    )
    slug = serializers.CharField(required=False)
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
    UpdateSerializerMixin,
    CreateControlledSiteContentSerializerMixin,
    SitePageDetailSerializer,
):
    widgets = serializers.PrimaryKeyRelatedField(
        queryset=SiteWidget.objects.all(),
        allow_null=True,
        many=True,
        validators=[SameSite()],
    )
    banner_image = serializers.PrimaryKeyRelatedField(
        queryset=Image.objects.all(),
        allow_null=True,
        validators=[SameSite()],
    )
    banner_video = serializers.PrimaryKeyRelatedField(
        queryset=Video.objects.all(),
        allow_null=True,
        validators=[SameSite()],
    )

    def to_representation(self, instance):
        data = SitePageDetailSerializer(instance=instance, context=self.context).data
        return data

    def create(self, validated_data):
        if "slug" not in validated_data:
            raise serializers.ValidationError(
                "A slug must be provided when creating a page."
            )
        validated_data["widgets"] = SiteWidgetListSerializer.create(
            self, validated_data
        )
        created = super().create(validated_data)
        return created

    def update(self, instance, validated_data):
        if "widgets" in validated_data:
            widgets = instance.widgets
            if not widgets:
                widgets = SiteWidgetList.objects.create(site=instance)
            widgets = SiteWidgetListSerializer.update(self, widgets, validated_data)
            validated_data["widgets"] = widgets
            instance.widgets = widgets

        validated_data.pop("slug", None)  # Prevent the slug field from being updated.

        if "get_visibility_display" in validated_data:
            validated_data["visibility"] = Visibility[
                str.upper(validated_data.pop("get_visibility_display"))
            ]

        return super().update(instance, validated_data)
