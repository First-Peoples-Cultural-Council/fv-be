from django.utils.translation import gettext as _
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import viewsets

from backend.models.media import Image
from backend.views.base_views import FVPermissionViewSetMixin, SiteContentViewSetMixin

from ..serializers.media_serializers import ImageSerializer
from . import doc_strings


@extend_schema_view(
    list=extend_schema(
        description=_("A list of available images for the specified site."),
        responses={
            200: ImageSerializer,
            403: OpenApiResponse(description=doc_strings.error_403_site_access_denied),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
    ),
    retrieve=extend_schema(
        description=_("An image from the specified site."),
        responses={
            200: ImageSerializer,
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404),
        },
    ),
)
class ImageViewSet(
    FVPermissionViewSetMixin,
    SiteContentViewSetMixin,
    viewsets.ModelViewSet,
):
    """
    Image information.
    """

    http_method_names = ["get"]
    serializer_class = ImageSerializer

    def get_queryset(self):
        site = self.get_validated_site()
        return Image.objects.filter(site__slug=site[0].slug)
