from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext as _
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework.viewsets import ModelViewSet

from backend.models import Membership
from backend.models.constants import AppRole, Role
from backend.serializers.membership_serializers import MembershipDetailSerializer
from backend.views import doc_strings
from backend.views.api_doc_variables import id_parameter, site_slug_parameter
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
        parameters=[site_slug_parameter],
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
        parameters=[
            site_slug_parameter,
            id_parameter,
        ],
    ),
    create=extend_schema(
        description=_("Add a membership. User cannot be changed after creation."),
        responses={
            201: OpenApiResponse(
                description=doc_strings.success_201, response=MembershipDetailSerializer
            ),
            400: OpenApiResponse(description=doc_strings.error_400_validation),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
        parameters=[site_slug_parameter],
    ),
    update=extend_schema(
        description=_("Edit a membership. User cannot be changed after creation."),
        responses={
            200: OpenApiResponse(
                description=doc_strings.success_200_edit,
                response=MembershipDetailSerializer,
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
    partial_update=extend_schema(
        description=_(
            "Edit a membership. Any omitted fields will be unchanged. User cannot be changed after creation."
        ),
        responses={
            200: OpenApiResponse(
                description=doc_strings.success_200_edit,
                response=MembershipDetailSerializer,
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
    SiteContentViewSetMixin, FVPermissionViewSetMixin, ModelViewSet
):
    """
    API endpoint for managing site memberships.
    """

    serializer_class = MembershipDetailSerializer

    def initial(self, *args, **kwargs):
        """Ensures user has permission to perform the requested action."""
        super().initial(*args, **kwargs)

        if self.request.method.lower() in ["put", "patch", "delete"]:
            requesting_user = self.request.user
            membership = Membership.objects.filter(pk=kwargs["pk"]).first()

            # If the membership being changed is that of a Language Admin
            # ensure that the requesting user is at least staff
            if membership.role == Role.LANGUAGE_ADMIN:
                if hasattr(requesting_user, "app_role"):
                    app_role = requesting_user.app_role
                    if app_role.role not in (AppRole.STAFF, AppRole.SUPERADMIN):
                        raise PermissionDenied(
                            "Staff or Super Admin app role is required to alter a Language Administrator's membership."
                        )
                else:
                    raise PermissionDenied(
                        "Contact support to alter a Language Administrator's membership."
                    )

    def get_queryset(self):
        site = self.get_validated_site()
        return (
            Membership.objects.filter(site=site)
            .order_by("-role", "user")
            .select_related(
                "site", "site__language", "created_by", "last_modified_by", "user"
            )
        )
