from django.utils.translation import gettext as _
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import parsers, viewsets

from backend.models.media import Image
from backend.serializers.media_detail_serializers import ImageDetailSerializer
from backend.serializers.media_serializers import ImageSerializer
from backend.views.base_views import FVPermissionViewSetMixin, SiteContentViewSetMixin

from . import doc_strings
from .api_doc_variables import id_parameter, site_slug_parameter
from .utils import get_select_related_media_fields


@extend_schema_view(
    list=extend_schema(
        description=_("A list of available images for the specified site."),
        responses={
            200: ImageSerializer,
            403: OpenApiResponse(description=doc_strings.error_403_site_access_denied),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
        parameters=[site_slug_parameter],
    ),
    retrieve=extend_schema(
        description=_("An image from the specified site."),
        responses={
            200: ImageSerializer,
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404),
        },
        parameters=[
            site_slug_parameter,
            id_parameter,
        ],
    ),
    create=extend_schema(
        description=_("Add an image."),
        responses={
            201: OpenApiResponse(
                description=doc_strings.success_201, response=ImageSerializer
            ),
            400: OpenApiResponse(description=doc_strings.error_400_validation),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
        parameters=[site_slug_parameter],
    ),
    destroy=extend_schema(
        description=_("Delete an image."),
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
class ImageViewSet(
    SiteContentViewSetMixin,
    FVPermissionViewSetMixin,
    viewsets.ModelViewSet,
):
    """
    Image information.
    """

    serializer_class = ImageSerializer
    parser_classes = [
        parsers.FormParser,
        parsers.MultiPartParser,
        parsers.JSONParser,  # used in audio views, but added here for consistency across media views
    ]  # to support file uploads

    def get_queryset(self):
        site = self.get_validated_site()
        return (
            Image.objects.filter(site=site)
            .select_related(*get_select_related_media_fields(None))
            .order_by("-created")
            .defer(
                "created_by_id",
                "last_modified_by_id",
                "last_modified",
            )
        )

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ImageDetailSerializer
        return ImageSerializer
