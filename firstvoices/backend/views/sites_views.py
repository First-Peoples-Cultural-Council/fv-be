from django.db.models import Prefetch
from django.db.models.functions import Upper
from django.utils.translation import gettext as _
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from backend.models.constants import Visibility
from backend.models.sites import Language, Membership, Site, SiteFeature
from backend.models.widget import SiteWidget, WidgetSettings
from backend.serializers.membership_serializers import MembershipSiteSummarySerializer
from backend.serializers.site_serializers import (
    LanguageSerializer,
    SiteDetailWriteSerializer,
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
        "under 'Other'.",
        responses={200: LanguageSerializer},
    ),
    retrieve=extend_schema(
        description="Basic information about a language site, for authorized users.",
        responses={
            200: inline_site_doc_detail_serializer,
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404),
        },
    ),
    update=extend_schema(
        description=_("Edit a site."),
        responses={
            200: OpenApiResponse(
                description=doc_strings.success_200_edit,
                response=inline_site_doc_detail_serializer,
            ),
            400: OpenApiResponse(description=doc_strings.error_400_validation),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404),
        },
    ),
    partial_update=extend_schema(
        description=_("Edit a site. Any omitted fields will be unchanged."),
        responses={
            200: OpenApiResponse(
                description=doc_strings.success_200_edit,
                response=inline_site_doc_detail_serializer,
            ),
            400: OpenApiResponse(description=doc_strings.error_400_validation),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404),
        },
    ),
)
class SiteViewSet(FVPermissionViewSetMixin, ModelViewSet):
    """
    Summary information about language sites.
    """

    http_method_names = ["get", "put", "patch"]
    lookup_field = "slug"
    pagination_class = None
    serializer_class = SiteDetailWriteSerializer

    def get_detail_queryset(self):
        sites = (
            Site.objects.all()
            .select_related(
                "menu",
                "language",
                "homepage",
                *get_select_related_media_fields("logo"),
                *get_select_related_media_fields("banner_image"),
                *get_select_related_media_fields("banner_video"),
            )
            .prefetch_related(
                Prefetch(
                    "sitefeature_set",
                    queryset=SiteFeature.objects.filter(
                        is_enabled=True
                    ).prefetch_related(
                        "site", "site__language", "created_by", "last_modified_by"
                    ),
                ),
                Prefetch(
                    "homepage__widgets",
                    queryset=SiteWidget.objects.visible(self.request.user)
                    .select_related(
                        "site", "site__language", "created_by", "last_modified_by"
                    )
                    .prefetch_related(
                        Prefetch(
                            "widgetsettings_set", queryset=WidgetSettings.objects.all()
                        )
                    ),
                ),
            )
        )

        return sites

    def get_list_queryset(self):
        return Site.objects.none()  # not used-- see the list method instead

    def list(self, request, *args, **kwargs):
        """
        Return a list of sites grouped by language.
        """
        # retrieve visible sites in order to filter out empty languages
        sites = Site.objects.filter(visibility__gte=Visibility.MEMBERS, is_hidden=False)
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
                "language": "Other",
                "languageCode": "",
                "sites": [
                    SiteSummarySerializer(site, context={"request": request}).data
                    for site in other_sites
                ],
            }

            data.append(other_site_json)

        return Response(data)

    def get_serializer_context(self):
        # Add site to serializer context for field level validation purposes
        context = super().get_serializer_context()
        context["site"] = self.get_object()
        return context


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
