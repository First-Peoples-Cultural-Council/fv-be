from django.utils.translation import gettext as _
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import parsers, viewsets

from backend.models.media import Audio
from backend.serializers.media_detail_serializers import AudioDetailSerializer
from backend.serializers.media_serializers import AudioSerializer
from backend.views.base_views import FVPermissionViewSetMixin, SiteContentViewSetMixin

from . import doc_strings
from .api_doc_variables import id_parameter, site_slug_parameter


@extend_schema_view(
    list=extend_schema(
        description=_("A list of available audio for the specified site."),
        responses={
            200: AudioSerializer,
            403: OpenApiResponse(description=doc_strings.error_403_site_access_denied),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
        parameters=[site_slug_parameter],
    ),
    retrieve=extend_schema(
        description=_("An audio item from the specified site."),
        responses={
            200: AudioSerializer,
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404),
        },
        parameters=[
            site_slug_parameter,
            id_parameter,
        ],
    ),
    create=extend_schema(
        description=_("Add an audio item."),
        responses={
            201: OpenApiResponse(
                description=doc_strings.success_201, response=AudioSerializer
            ),
            400: OpenApiResponse(description=doc_strings.error_400_validation),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
        parameters=[site_slug_parameter],
    ),
    destroy=extend_schema(
        description=_("Delete an audio item."),
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
class AudioViewSet(
    SiteContentViewSetMixin,
    FVPermissionViewSetMixin,
    viewsets.ModelViewSet,
):
    """
    Audio information.
    """

    serializer_class = AudioSerializer
    parser_classes = [
        parsers.FormParser,
        parsers.MultiPartParser,
    ]  # to support file uploads

    def get_queryset(self):
        site = self.get_validated_site()
        return (
            Audio.objects.filter(site__slug=site[0].slug)
            .prefetch_related("original", "site", "speakers")
            .order_by("-created")
            .defer(
                "created_by_id",
                "last_modified_by_id",
                "last_modified",
            )
        )

    def get_serializer_class(self):
        if self.action == "retrieve":
            return AudioDetailSerializer
        return AudioSerializer

    def update(self, request, *args, **kwargs):
        # To handle empty list in multipart form-data
        request.data._mutable = True
        speakers = request.data.getlist("speakers", None)
        if len(speakers) == 1 and speakers[0] == "[]":
            speakers = []
        request.data.setlist("speakers", speakers)
        request.data._mutable = False

        return super().update(request, *args, **kwargs)
