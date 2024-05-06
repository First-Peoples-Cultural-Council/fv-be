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
from backend.views.base_views import FVPermissionViewSetMixin, SiteContentViewSetMixin

from . import doc_strings
from .api_doc_variables import id_parameter, site_slug_parameter
from .utils import get_media_prefetch_list


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
    partial_update=extend_schema(
        description=_("Edit a song. Any omitted fields will be unchanged."),
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
    def get_queryset(self):
        site = self.get_validated_site()
        return (
            Song.objects.filter(site=site)
            .order_by("title")
            .all()
            .select_related("site", "site__language", "created_by", "last_modified_by")
            .prefetch_related("lyrics", *get_media_prefetch_list(self.request.user))
        )

    def get_serializer_class(self):
        if self.action in ("list",):
            if self.request.query_params.get("summary", "false").lower() in ("true",):
                return SongListSerializer
            return SongSerializer
        else:
            return SongSerializer
