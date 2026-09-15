from django.utils.translation import gettext as _
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from backend.models import Organization
from backend.serializers.organization_serializers import OrganizationSerializer
from backend.views.base_views import FVPermissionViewSetMixin, SiteContentViewSetMixin

from . import doc_strings
from .api_doc_variables import id_parameter, site_slug_parameter
from .utils import (
    get_site_content_select_related_fields,
    get_standard_select_related_fields,
)


@extend_schema_view(
    list=extend_schema(
        description=_(
            "A list of organization contact information associated with the specified site."
        ),
        responses={
            200: OpenApiResponse(
                description=doc_strings.success_200_list,
                response=OrganizationSerializer,
            ),
            403: OpenApiResponse(description=doc_strings.error_403_site_access_denied),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
        parameters=[site_slug_parameter],
    ),
    retrieve=extend_schema(
        description="Details about a specific organization.",
        responses={
            200: OpenApiResponse(
                description=doc_strings.success_200_detail,
                response=OrganizationSerializer,
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
        description="Create a new instance of organization information for the site.",
        responses={
            201: OpenApiResponse(
                description=doc_strings.success_201,
                response=OrganizationSerializer,
            ),
            400: OpenApiResponse(description=doc_strings.error_400_validation),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
        parameters=[site_slug_parameter],
    ),
    update=extend_schema(
        description="Update an existing instance of organization information.",
        responses={
            200: OpenApiResponse(
                description=doc_strings.success_200_edit,
                response=OrganizationSerializer,
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
        description="Update an existing instance of organization information. Any omitted fields will be unchanged.",
        responses={
            200: OpenApiResponse(
                description=doc_strings.success_200_edit,
                response=OrganizationSerializer,
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
        description="Delete an existing instance of organization information.",
        responses={
            204: OpenApiResponse(description=doc_strings.success_204_deleted),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404),
        },
        parameters=[
            site_slug_parameter,
            id_parameter,
        ],
    ),
)
class OrganizationViewSet(
    SiteContentViewSetMixin, FVPermissionViewSetMixin, ModelViewSet
):
    serializer_class = OrganizationSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset.exists():
            site = self.get_validated_site()
            return Response(
                {
                    "contact_message": f"The FirstVoices site for the {site.title} language is currently inactive. "
                    f"If this is your language or community and you are interested in working on "
                    f"this project, please contact ltp@fpcc.ca for more information.",
                    "emails": ["ltp@fpcc.ca"],
                    "urlList": ["https://www.firstvoices.com/support"],
                }
            )
        else:
            return super().list(request, *args, **kwargs)

    def get_queryset(self):
        site = self.get_validated_site()
        return (
            Organization.objects.filter(site=site)
            .order_by("order", "name")
            .select_related(
                *get_standard_select_related_fields(),
                *get_site_content_select_related_fields(),
            )
        )
