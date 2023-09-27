from django.utils.translation import gettext as _
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import viewsets

from backend.serializers.media_serializers import AudioSerializer
from backend.views.base_views import FVPermissionViewSetMixin, SiteContentViewSetMixin

from . import doc_strings
from .api_doc_variables import id_parameter, site_slug_parameter
from backend.models import Membership
from backend.serializers.membership_serializers import MembershipSerializer


@extend_schema_view(
    list=extend_schema(
        description=_("A list of memberships for the specified site."),
        responses={
            200: MembershipSerializer,
            403: OpenApiResponse(description=doc_strings.error_403_site_access_denied),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
        parameters=[site_slug_parameter],
    ),
    retrieve=extend_schema(
        description=_("A membership from the specified site."),
        responses={
            200: MembershipSerializer,
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404),
        },
        parameters=[
            site_slug_parameter,
            id_parameter,
        ],
    ),
    create=extend_schema(
        description=_("Add a membership."),
        responses={
            201: OpenApiResponse(
                description=doc_strings.success_201, response=MembershipSerializer
            ),
            400: OpenApiResponse(description=doc_strings.error_400_validation),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
        parameters=[site_slug_parameter],
    ),
    destroy=extend_schema(
        description=_("Delete a membership."),
        responses={
            204: OpenApiResponse(
                description=doc_strings.success_204_deleted,
            ),
            400: OpenApiResponse(description=doc_strings.error_400_validation),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404),
        },
        parameters=[
            site_slug_parameter,
            id_parameter,
        ],
    ),
)
class MembershipViewSet(
    SiteContentViewSetMixin,
    FVPermissionViewSetMixin,
    viewsets.ModelViewSet,
):
    """
    Membership information.
    """

    serializer_class = MembershipSerializer

    def get_queryset(self):
        site = self.get_validated_site()
        return (
            Membership.objects.filter(site__slug=site[0].slug)
            .select_related("user", "site")
            .order_by("-role", "user__email")
            .defer(
                "created_by_id",
                "last_modified_by_id",
                "last_modified",
                "site__language"
            )
        )
