from django.utils.translation import gettext as _
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)
from rest_framework.viewsets import ModelViewSet

from backend.models import Song
from backend.serializers.song_serializers import SongListSerializer, SongSerializer
from backend.views.base_views import (
    FVPermissionViewSetMixin,
    SiteContentViewSetMixin,
    http_methods_except_patch,
)

from . import doc_strings
from .api_doc_variables import id_parameter, site_slug_parameter


@extend_schema_view(
    list=extend_schema(
        description=_("A list of songs associated with the specified site."),
        parameters=[
            site_slug_parameter,
            OpenApiParameter(
                "summary", OpenApiTypes.BOOL, OpenApiParameter.QUERY, default="false"
            ),
        ],
        responses={
            200: OpenApiResponse(
                description=doc_strings.success_200_list,
                response=SongListSerializer,
            ),
            403: OpenApiResponse(description=doc_strings.error_403_site_access_denied),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
    ),
    retrieve=extend_schema(
        description=_("Details about a specific song."),
        responses={
            200: OpenApiResponse(
                description=doc_strings.success_200_detail,
                response=SongSerializer,
            ),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404),
        },
        parameters=[
            site_slug_parameter,
            id_parameter,
        ],
    ),
    create=extend_schema(
        description=_("Add a song."),
        responses={
            201: OpenApiResponse(
                description=doc_strings.success_201, response=SongSerializer
            ),
            400: OpenApiResponse(description=doc_strings.error_400_validation),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
        parameters=[site_slug_parameter],
    ),
    update=extend_schema(
        description=_("Edit a song."),
        responses={
            200: OpenApiResponse(
                description=doc_strings.success_200_edit,
                response=SongSerializer,
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
    destroy=extend_schema(
        description=_("Delete a song."),
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
class SongViewSet(SiteContentViewSetMixin, FVPermissionViewSetMixin, ModelViewSet):
    http_method_names = http_methods_except_patch

    def get_detail_queryset(self):
        site = self.get_validated_site()
        return Song.objects.filter(site__slug=site[0].slug).all()

    def get_list_queryset(self):
        site = self.get_validated_site()
        return Song.objects.filter(site__slug=site[0].slug).order_by("id").all()

    def get_serializer_class(self):
        if self.action in ("list",):
            if self.request.query_params.get("summary", "false").lower() in ("true",):
                return SongListSerializer
            return SongSerializer
        else:
            return SongSerializer
