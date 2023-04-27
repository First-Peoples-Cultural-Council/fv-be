from itertools import groupby
from operator import itemgetter

from django.db.models import Prefetch
from django.db.models.functions import Upper
from drf_spectacular.utils import (
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
    inline_serializer,
)
from rest_framework import mixins, serializers, viewsets
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rules.contrib.rest_framework import AutoPermissionViewSetMixin

from backend.models.sites import Membership, SiteFeature
from backend.predicates import utils
from backend.serializers.site_serializers import (
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
    lookup_field = "slug"
    pagination_class = None

    serializer_class = SiteDetailSerializer

    def get_queryset(self):
        # not used for list action
        return Site.objects.select_related("menu", "language").prefetch_related(
            Prefetch(
                "sitefeature_set", queryset=SiteFeature.objects.filter(is_enabled=True)
            )
        )

    def list(self, request, *args, **kwargs):
        """
        Override the list method to group sites by language.
        """
        # custom queryset to avoid prefetching from unneeded tables (list view has less detail)
        queryset = Site.objects.select_related("language").order_by(
            Upper("language__title"), Upper("title")
        )

        # apply permissions
        sites = utils.filter_by_viewable(request.user, queryset)

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


@extend_schema_view(
    list=extend_schema(
        description="A list of language sites a given user is a member of, "
        "grouped by language. If there are no accessible sites or "
        "the user does not have membership to any site then the "
        "list will be empty. Sites with no specified language "
        "will be grouped under 'Other'.",
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
)
class MySitesViewSet(
    AutoPermissionViewSetMixin, mixins.ListModelMixin, viewsets.GenericViewSet
):
    """
    Summary information about language sites a given user has membership to.
    """

    http_method_names = ["get"]
    pagination_class = None
    serializer_class = SiteSummarySerializer

    def get_queryset(self):
        # get memberships for the user
        memberships = Membership.objects.filter(user=self.request.user)
        sites_id_list = []

        # get the site ids from the memberships
        for membership in memberships:
            sites_id_list.append(membership.site.id)

        # get the site objects filtered by the id list and order by language
        queryset = (
            Site.objects.filter(id__in=sites_id_list)
            .select_related("language")
            .order_by(Upper("language__title"), Upper("title"))
        )

        # filter the list down to the sites the user has view permissions on
        sites = utils.filter_by_viewable(self.request.user, queryset)

        return sites

    def list(self, request, *args, **kwargs):
        # get the sites
        sites = self.get_queryset()

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
