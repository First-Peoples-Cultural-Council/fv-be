from rest_framework import serializers

from backend.models import SitePage
from backend.serializers.base_serializers import (
    CreateSiteContentSerializerMixin,
    SiteContentLinkedTitleSerializer,
    UpdateSerializerMixin,
    WritableVisibilityField,
)
from backend.serializers.fields import SiteHyperlinkedIdentityField
from backend.serializers.media_serializers import ImageSerializer, VideoSerializer
from backend.serializers.widget_serializers import SiteWidgetListSerializer


class SitePageSerializer(
    CreateSiteContentSerializerMixin,
    UpdateSerializerMixin,
    SiteContentLinkedTitleSerializer,
):
    url = SiteHyperlinkedIdentityField(
        view_name="api:sitepage-detail", lookup_field="slug"
    )
    slug = serializers.CharField(read_only=True)
    visibility = WritableVisibilityField(required=True)

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
