from rest_framework import serializers

from backend.models import SitePage
from backend.serializers.base_serializers import SiteContentLinkedTitleSerializer
from backend.serializers.fields import SiteHyperlinkedIdentityField
from backend.serializers.media_serializers import ImageSerializer, VideoSerializer
from backend.serializers.widget_serializers import SiteWidgetListSerializer


class SitePageSerializer(SiteContentLinkedTitleSerializer):
    url = SiteHyperlinkedIdentityField(
        view_name="api:sitepage-detail", lookup_field="slug"
    )
    slug = serializers.CharField(read_only=True)
    visibility = serializers.CharField(read_only=True, source="get_visibility_display")

    class Meta(SiteContentLinkedTitleSerializer.Meta):
        model = SitePage
        fields = SiteContentLinkedTitleSerializer.Meta.fields + (
            "visibility",
            "subtitle",
            "slug",
        )


class SitePageDetailSerializer(SiteContentLinkedTitleSerializer):
    url = SiteHyperlinkedIdentityField(
        view_name="api:sitepage-detail", lookup_field="slug"
    )
    slug = serializers.CharField(read_only=True)
    visibility = serializers.CharField(read_only=True, source="get_visibility_display")
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
