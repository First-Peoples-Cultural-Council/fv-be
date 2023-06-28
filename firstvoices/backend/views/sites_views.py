from django.db.models import Prefetch
from django.db.models.functions import Upper
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rules.contrib.rest_framework import AutoPermissionViewSetMixin

from backend.models.sites import Language, Membership, SiteFeature
from backend.serializers.membership_serializers import MembershipSiteSummarySerializer
from backend.serializers.site_serializers import (
    LanguageSerializer,
    Site,
    SiteDetailSerializer,
    SiteSummarySerializer,
)
from backend.views.base_views import FVPermissionViewSetMixin


@extend_schema_view(
    list=extend_schema(
        description="A public list of available language sites, grouped by language. "
        "Public and member sites are included, as well as any team sites the user has access to. If there "
        "are no accessible sites the list will be empty. Sites with no specified language will be grouped "
        "under 'Other'.",
        responses={200: LanguageSerializer},
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
        Return a list of sites grouped by language.
        """
        sites = Site.objects.visible(request.user).order_by(Upper("title"))
        ids_of_languages_with_sites = sites.values_list("language_id", flat=True)

        # sorting note: titles are converted to uppercase and then sorted which will put custom characters at the end
        languages = (
            Language.objects.filter(id__in=ids_of_languages_with_sites)
            .order_by(Upper("title"))
            .prefetch_related(
                Prefetch(
                    "sites__sitefeature_set",
                    queryset=SiteFeature.objects.filter(is_enabled=True),
                ),
            )
        )

        data = [
            LanguageSerializer(language, context={"request": request}).data
            for language in languages
        ]

        # add "other" sites
        other_sites = sites.filter(language=None)

        if other_sites:
            other_site_json = {
                "language": "Other",
                "languageCode": "",
                "sites": [
                    SiteSummarySerializer(site, context={"request": request}).data
                    for site in other_sites
                ],
            }

            data.append(other_site_json)

        return Response(data)


@extend_schema_view(
    list=extend_schema(
        description="A list of language sites that the current user is a member of. May be empty.",
        responses={
            200: MembershipSiteSummarySerializer,
        },
    ),
)
class MySitesViewSet(FVPermissionViewSetMixin, ModelViewSet):
    """
    Information about language sites the current user is a member of.
    """

    http_method_names = ["get"]
    lookup_field = "site__slug"
    serializer_class = MembershipSiteSummarySerializer

    def get_queryset(self):
        # note that the titles are converted to uppercase and then sorted which will put custom characters at the end
        return (
            Membership.objects.filter(user=self.request.user)
            .select_related("site", "site__language")
            .prefetch_related(
                Prefetch(
                    "site__sitefeature_set",
                    queryset=SiteFeature.objects.filter(is_enabled=True),
                ),
            )
            .order_by(Upper("site__title"))
        )
