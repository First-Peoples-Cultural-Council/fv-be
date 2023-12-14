from django.db.models import Prefetch
from django.db.models.functions import Upper
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from backend.models.constants import Visibility
from backend.models.sites import Language, Membership, Site, SiteFeature
from backend.serializers.membership_serializers import MembershipSiteSummarySerializer
from backend.serializers.site_serializers import (
    LanguageSerializer,
    SiteSummarySerializer,
)
from backend.views import doc_strings
from backend.views.api_doc_variables import inline_site_doc_detail_serializer
from backend.views.base_views import FVPermissionViewSetMixin

from .utils import get_select_related_media_fields


@extend_schema_view(
    list=extend_schema(
        description="A public list of available language sites, grouped by language. "
        "Public and member sites are included, as well as any team sites the user has access to. If there "
        "are no accessible sites the list will be empty. Sites with no specified language will be grouped "
        "under 'More FirstVoices Sites'.",
        responses={200: LanguageSerializer},
    ),
    retrieve=extend_schema(
        description="Basic information about a language.",
        responses={
            200: inline_site_doc_detail_serializer,
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404),
        },
    ),
)
class LanguageViewSet(FVPermissionViewSetMixin, ModelViewSet):
    """
    Summary information about languages.
    """

    http_method_names = ["get"]
    serializer_class = LanguageSerializer
    pagination_class = None
    model = Language

    def get_detail_queryset(self):
        return (
            Language.objects.all()
            .order_by(Upper("title"))
            .prefetch_related(
                Prefetch(
                    "sites",
                    queryset=Site.objects.visible(user=self.request.user)
                    .order_by(Upper("title"))
                    .select_related(*get_select_related_media_fields("logo")),
                ),
                Prefetch(
                    "sites__sitefeature_set",
                    queryset=SiteFeature.objects.filter(is_enabled=True),
                ),
            )
        )

    def get_list_queryset(self):
        return Language.objects.none()  # not used-- see the list method instead

    def list(self, request, *args, **kwargs):
        """
        Return a list of sites grouped by language.
        """
        # retrieve visible sites in order to filter out empty languages
        sites = Site.objects.filter(visibility__gte=Visibility.MEMBERS)
        ids_of_languages_with_sites = sites.values_list("language_id", flat=True)

        # then retrieve the desired data as a Language queryset
        # sorting note: titles are converted to uppercase and then sorted which will put custom characters at the end
        languages = (
            Language.objects.filter(id__in=ids_of_languages_with_sites)
            .order_by(Upper("title"))
            .prefetch_related(
                Prefetch(
                    "sites",
                    queryset=sites.order_by(Upper("title")).select_related(
                        *get_select_related_media_fields("logo")
                    ),
                ),
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
        other_sites = (
            sites.filter(language=None)
            .order_by(Upper("title"))
            .select_related(*get_select_related_media_fields("logo"))
            .prefetch_related(
                Prefetch(
                    "sitefeature_set",
                    queryset=SiteFeature.objects.filter(is_enabled=True),
                ),
            )
        )

        if other_sites:
            other_site_json = {
                "language": "More FirstVoices Sites",
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
        if self.request.user.is_anonymous:
            return Membership.objects.none()

        # note that the titles are converted to uppercase and then sorted which will put custom characters at the end
        return (
            Membership.objects.filter(user=self.request.user)
            .select_related(
                "site", "site__language", *get_select_related_media_fields("site__logo")
            )
            .prefetch_related(
                Prefetch(
                    "site__sitefeature_set",
                    queryset=SiteFeature.objects.filter(is_enabled=True),
                ),
            )
            .order_by(Upper("site__title"))
        )
