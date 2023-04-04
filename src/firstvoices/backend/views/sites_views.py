from django.db.models import Prefetch
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework.viewsets import ModelViewSet

from firstvoices.backend.models.sites import Language, SiteFeature
from firstvoices.backend.serializers import (
    LanguageSerializer,
    Site,
    SiteDetailSerializer,
)
from firstvoices.backend.views.base_views import FVPermissionViewSetMixin


@extend_schema_view(
    list=extend_schema(
        description="A list of languages on this server, with the available language sites for each. For a simple list "
        "of language sites, see the sites API. Public and "
        "member sites are included, as well as any team sites the user has access to. If there are no "
        "accessible sites for a language, the sites list will be empty.",
        responses={
            200: LanguageSerializer,
        },
    ),
    retrieve=extend_schema(
        description="Details about a language.",
        responses={
            200: LanguageSerializer,
            403: OpenApiResponse(
                description="Todo: Error Not Authorized (Should we use this for member sites?)"
            ),
            404: OpenApiResponse(
                description="Todo: Not Found (Should we use this for team sites?)"
            ),
        },
    ),
)
class LanguageViewSet(FVPermissionViewSetMixin, ModelViewSet):
    """
    Language information, including the list of sites for that language.
    """

    http_method_names = ["get"]
    queryset = Language.objects.all()  # todo: prefetching for related objects?
    serializer_class = LanguageSerializer


@extend_schema_view(
    list=extend_schema(
        description="A list of available language sites. For a list grouped by language, see the languages API. "
        "Public and member sites are included, as well as any team sites the user has access to. If there "
        "are no accessible sites the list will be empty.",
        responses={
            200: SiteDetailSerializer,
        },
    ),
    retrieve=extend_schema(
        description="Summary information about a language site.",
        responses={
            200: SiteDetailSerializer,
            403: OpenApiResponse(
                description="Todo: Error Not Authorized (Should we use this for member sites?)"
            ),
            404: OpenApiResponse(
                description="Todo: Not Found (Should we use this for team sites?)"
            ),
        },
    ),
)
class SiteViewSet(FVPermissionViewSetMixin, ModelViewSet):
    """
    Summary information about language sites. For a list view, see LanguageViewSet.
    """

    http_method_names = ["get"]
    queryset = Site.objects.prefetch_related(
        Prefetch("sitefeature", queryset=SiteFeature.objects.filter(is_enabled=True))
    )
    lookup_field = "slug"
    serializer_class = SiteDetailSerializer
