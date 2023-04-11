from itertools import groupby
from operator import itemgetter

from django.db.models import Prefetch
from drf_spectacular.utils import (
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
    inline_serializer,
)
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rules.contrib.rest_framework import AutoPermissionViewSetMixin

from firstvoices.backend.models.sites import SiteFeature
from firstvoices.backend.predicates import utils
from firstvoices.backend.serializers import (
    Site,
    SiteDetailSerializer,
    SiteSummarySerializer,
)


@extend_schema_view(
    list=extend_schema(
        description="A public list of available language sites, grouped by language. "
        "Public and member sites are included, as well as any team sites the user has access to. If there "
        "are no accessible sites the list will be empty. Sites with no specified language will be grouped "
        "under 'Other'.",
        responses={
            200: inline_serializer(
                name="InlineLanguageSerializer",
                fields={
                    "language": serializers.CharField(),
                    "sites": SiteSummarySerializer(many=True),
                },
            ),
        },
    ),
    retrieve=extend_schema(
        description="Basic information about a language site, for authorized users.",
        responses={
            200: SiteDetailSerializer,
            403: OpenApiResponse(description="Todo: Error Not Authorized"),
            404: OpenApiResponse(description="Todo: Not Found"),
        },
    ),
)
class SiteViewSet(AutoPermissionViewSetMixin, ModelViewSet):
    """
    Summary information about language sites.
    """

    http_method_names = ["get"]
    queryset = (
        Site.objects.select_related("menu", "language")
        .prefetch_related(
            Prefetch(
                "sitefeature", queryset=SiteFeature.objects.filter(is_enabled=True)
            )
        )
        .order_by("language__title", "title")
    )
    lookup_field = "slug"
    pagination_class = None

    serializer_class = SiteDetailSerializer

    def list(self, request, *args, **kwargs):
        """
        Override the list method to group sites by language.
        """
        # apply permissions
        sites = utils.filter_by_viewable(request.user, self.get_queryset())

        # serialize each site (groupby can't handle Models)
        site_jsons = [
            SiteSummarySerializer(site, context={"request": request}).data
            for site in sites
        ]

        # group by language
        rows = groupby(site_jsons, itemgetter("language"))
        data = [
            {
                "language": language if language is not None else "Other",
                "sites": list(items),
            }
            for language, items in rows
        ]

        return Response(data)
