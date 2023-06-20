from django.utils.translation import gettext as _
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)
from rest_framework import viewsets

from backend.models.media import Audio
from backend.serializers.media_serializers import AudioSerializer
from backend.views.base_views import FVPermissionViewSetMixin, SiteContentViewSetMixin

from . import doc_strings


@extend_schema_view(
    list=extend_schema(
        description=_("A list of available audio for the specified site."),
        responses={
            200: AudioSerializer,
            403: OpenApiResponse(description=doc_strings.error_403_site_access_denied),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
        parameters=[
            OpenApiParameter(
                name="site_slug", type=OpenApiTypes.STR, location=OpenApiParameter.PATH
            )
        ],
    ),
    retrieve=extend_schema(
        description=_("An audio item from the specified site."),
        responses={
            200: AudioSerializer,
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404),
        },
        parameters=[
            OpenApiParameter(
                name="site_slug", type=OpenApiTypes.STR, location=OpenApiParameter.PATH
            ),
            OpenApiParameter(
                name="id", type=OpenApiTypes.UUID, location=OpenApiParameter.PATH
            ),
        ],
    ),
)
class AudioViewSet(
    FVPermissionViewSetMixin,
    SiteContentViewSetMixin,
    viewsets.ModelViewSet,
):
    """
    Audio information.
    """

    http_method_names = ["get"]
    serializer_class = AudioSerializer

    def get_queryset(self):
        site = self.get_validated_site()
        return Audio.objects.filter(site__slug=site[0].slug).prefetch_related(
            "speakers"
        )
