from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework.viewsets import ModelViewSet

from firstvoices.backend.serializers import Site, SiteSerializer
from firstvoices.backend.views.base_views import FVPermissionViewSetMixin


@extend_schema_view(
    list=extend_schema(
        description="A list of language sites available on this server, with summary information for each. Public and "
        "member sites are included, as well as any team sites the user has access to. If there are no "
        "accessible sites the list will be empty.",
        responses={
            200: SiteSerializer,
        },
    ),
    retrieve=extend_schema(
        description="Summary information about the specified language site.",
        responses={
            200: SiteSerializer,
            403: OpenApiResponse(
                description="Todo: Error Not Authorized (Should we use this for member sites?)"
            ),
            404: OpenApiResponse(
                description="Todo: Not Found (Should we use this for team sites?)"
            ),
        },
    ),
)
class SiteFilteredList(FVPermissionViewSetMixin, ModelViewSet):
    """
    Summary information about language sites available on this server. Public and member sites are included, as well as
    any team sites the user has access to.
    """

    http_method_names = ["get"]
    queryset = Site.objects.all()  # todo: prefetching for related objects?
    serializer_class = SiteSerializer
