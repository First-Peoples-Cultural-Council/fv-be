from django.core.exceptions import PermissionDenied
from django.http import Http404
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework.viewsets import ModelViewSet

from backend.models import DictionaryEntry, Site
from backend.predicates import utils
from backend.serializers.dictionary_serializers import DictionaryEntryDetailSerializer
from backend.views.base_views import FVPermissionViewSetMixin


@extend_schema_view(
    list=extend_schema(
        description="A list of available dictionary entries for the specified site.",
        responses={
            200: DictionaryEntryDetailSerializer,
            403: OpenApiResponse(description="Todo: Not authorized for this Site"),
            404: OpenApiResponse(description="Todo: Site not found"),
        },
    ),
    retrieve=extend_schema(
        description="A dictionary entry from the specified site.",
        responses={
            200: DictionaryEntryDetailSerializer,
            403: OpenApiResponse(description="Todo: Error Not Authorized"),
            404: OpenApiResponse(description="Todo: Not Found"),
        },
    ),
)
class DictionaryViewSet(FVPermissionViewSetMixin, ModelViewSet):
    """
    Dictionary entry information.
    """

    http_method_names = ["get"]
    serializer_class = DictionaryEntryDetailSerializer

    def get_validated_site(self):
        site_slug = self.kwargs["site_slug"]
        site = Site.objects.filter(slug=site_slug)

        if site.count() == 0:
            raise Http404

        if utils.filter_by_viewable(self.request.user, site).count() == 0:
            raise PermissionDenied

        return site

    def get_queryset(self):
        site = self.get_validated_site()
        if site.count() > 0:
            return DictionaryEntry.objects.filter(site__slug=site[0].slug)
        else:
            return DictionaryEntry.objects.filter(site__slug=None)
