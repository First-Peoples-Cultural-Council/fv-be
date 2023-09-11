from django.utils.translation import gettext as _
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import parsers, viewsets

from backend.models.media import Video
from backend.serializers.media_serializers import VideoSerializer
from backend.views.base_views import FVPermissionViewSetMixin, SiteContentViewSetMixin

from . import doc_strings
from .api_doc_variables import id_parameter, site_slug_parameter
from .utils import get_select_related_media_fields


@extend_schema_view(
    list=extend_schema(
        description=_("A list of available videos for the specified site."),
        responses={
            200: VideoSerializer,
            403: OpenApiResponse(description=doc_strings.error_403_site_access_denied),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
        parameters=[site_slug_parameter],
    ),
    retrieve=extend_schema(
        description=_("A video from the specified site."),
        responses={
            200: VideoSerializer,
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404),
        },
        parameters=[
            site_slug_parameter,
            id_parameter,
        ],
    ),
    create=extend_schema(
        description=_("Add a video."),
        responses={
            201: OpenApiResponse(
                description=doc_strings.success_201, response=VideoSerializer
            ),
            400: OpenApiResponse(description=doc_strings.error_400_validation),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
        parameters=[site_slug_parameter],
    ),
    destroy=extend_schema(
        description=_("Delete a video."),
        responses={
            204: OpenApiResponse(
                description=doc_strings.success_204_deleted,
            ),
            400: OpenApiResponse(description=doc_strings.error_400_validation),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404),
        },
        parameters=[
            site_slug_parameter,
            id_parameter,
        ],
    ),
)
class VideoViewSet(
    SiteContentViewSetMixin,
    FVPermissionViewSetMixin,
    viewsets.ModelViewSet,
):
    """
    Video information.
    """

    http_method_names = ["get", "post", "delete"]
    serializer_class = VideoSerializer
    parser_classes = [
        parsers.FormParser,
        parsers.MultiPartParser,
    ]  # to support file uploads

    def get_queryset(self):
        site = self.get_validated_site()
        return (
            Video.objects.filter(site__slug=site[0].slug)
            .select_related("site", *get_select_related_media_fields(None))
            .order_by("-created")
        )
