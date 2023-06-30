from django.utils.translation import gettext as _
from drf_spectacular.utils import (
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)
from rest_framework.viewsets import ModelViewSet

from backend.views.base_views import (
    FVPermissionViewSetMixin,
    SiteContentViewSetMixin,
)
from . import doc_strings
from ..models import Song
from ..serializers.song_serializers import SongListSerializer, SongDetailSerializer


@extend_schema_view(
    list=extend_schema(
        description=_("A list of songs associated with the specified site."),
        responses={
            200: OpenApiResponse(
                description=doc_strings.success_200_list,
                response=SongListSerializer,
            ),
            403: OpenApiResponse(description=doc_strings.error_403_site_access_denied),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        }
    ),
    retrieve=extend_schema(
        description=_("Details about a specific song."),
        responses={
            200: OpenApiResponse(
                description=doc_strings.success_200_detail,
                response=SongDetailSerializer,
            ),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404),
        },
    )
)
class SongViewSet(SiteContentViewSetMixin, FVPermissionViewSetMixin, ModelViewSet):
    http_method_names = ['get']

    def get_detail_queryset(self):
        site = self.get_validated_site()
        return Song.objects.filter(site__slug=site[0].slug).all()

    def get_list_queryset(self):
        site = self.get_validated_site()
        return Song.objects.filter(site__slug=site[0].slug).order_by('id').all()

    def get_serializer_class(self):
        if self.action == "list":
            return SongListSerializer
        else:
            return SongDetailSerializer
