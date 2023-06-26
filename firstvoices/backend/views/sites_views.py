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

from backend.models.sites import Language, SiteFeature
from backend.serializers.site_serializers import (
    LanguageSerializer,
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
        description="A list of language sites a given user is a member of. If "
        "there are no accessible sites or the user does not have "
        "membership to any site then the list will be empty.",
        responses={
            200: inline_serializer(
                name="MySitesInlineLanguageSerializer",
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
        # get the site objects filtered by the membership set for the user
        # note that the titles are converted to uppercase and then sorted which will put custom characters at the end
        return (
            Site.objects.visible(self.request.user)
            .filter(membership_set__user=self.request.user)
            .select_related("language")
            .order_by(Upper("title"))
        )
