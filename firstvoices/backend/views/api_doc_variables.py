from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, inline_serializer
from rest_framework import serializers

from backend.serializers.media_serializers import ImageSerializer, VideoSerializer
from backend.serializers.site_serializers import FeatureFlagSerializer
from backend.serializers.widget_serializers import SiteWidgetDetailSerializer

site_slug_parameter = OpenApiParameter(
    name="site_slug",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.PATH,
    description="site-slug",
)
id_parameter = OpenApiParameter(
    name="id", type=OpenApiTypes.STR, location=OpenApiParameter.PATH
)
key_parameter = OpenApiParameter(
    name="key", type=OpenApiTypes.STR, location=OpenApiParameter.PATH
)
site_page_slug_parameter = OpenApiParameter(
    name="slug",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.PATH,
    description="page-slug",
)

inline_site_doc_detail_serializer = inline_serializer(
    name="InlineSiteDetailSerializer",
    fields={
        "id": serializers.UUIDField(),
        "title": serializers.CharField(),
        "url": serializers.URLField(),
        "slug": serializers.SlugField(),
        "visibility": serializers.CharField(),
        "language": serializers.CharField(),
        "logo": ImageSerializer(),
        "features": FeatureFlagSerializer(),
        "menu": serializers.CharField(),
        "banner_image": ImageSerializer(),
        "banner_video": VideoSerializer(),
        "homepage": SiteWidgetDetailSerializer(many=True),
        "pages": serializers.CharField(),
        "songs": serializers.CharField(),
        "stories": serializers.CharField(),
        "widgets": serializers.CharField(),
    },
)

inline_page_doc_detail_serializer = inline_serializer(
    name="InlinePageDetailSerializer",
    fields={
        "id": serializers.UUIDField(),
        "title": serializers.CharField(),
        "url": serializers.URLField(),
        "visibility": serializers.CharField(),
        "subtitle": serializers.CharField(),
        "slug": serializers.CharField(),
        "widgets": SiteWidgetDetailSerializer(many=True),
        "banner_image": ImageSerializer(),
        "banner_video": VideoSerializer(),
    },
)
