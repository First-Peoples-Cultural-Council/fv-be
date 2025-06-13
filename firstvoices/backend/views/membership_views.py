from django.utils.translation import gettext as _
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework.viewsets import ModelViewSet

from backend.models import Membership
from backend.serializers.membership_serializers import MembershipDetailSerializer
from backend.views import doc_strings
from backend.views.base_views import FVPermissionViewSetMixin, SiteContentViewSetMixin


@extend_schema_view(
    list=extend_schema(
        description=_("A list of memberships associated with the specified site."),
        responses={
            200: OpenApiResponse(
                description=doc_strings.success_200_list,
                response=MembershipDetailSerializer,
            ),
            403: OpenApiResponse(description=doc_strings.error_403_site_access_denied),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
    ),
    retrieve=extend_schema(
        description=_("Details about a specific membership."),
        responses={
            200: OpenApiResponse(
                description=doc_strings.success_200_detail,
                response=MembershipDetailSerializer,
            ),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404),
        },
    ),
)
class MembershipViewSet(
    SiteContentViewSetMixin, FVPermissionViewSetMixin, ModelViewSet
):
    """
    API endpoint for managing site memberships.
    """

    serializer_class = MembershipDetailSerializer
    http_method_names = ["get"]

    def get_queryset(self):
        site = self.get_validated_site()
        return (
            Membership.objects.filter(site=site)
            .order_by("-role", "user")
            .select_related(
                "site", "site__language", "created_by", "last_modified_by", "user"
            )
        )
