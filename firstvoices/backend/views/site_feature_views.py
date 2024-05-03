from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework.viewsets import ModelViewSet

from backend.models.sites import SiteFeature
from backend.serializers.site_feature_serializers import SiteFeatureDetailSerializer
from backend.views import doc_strings
from backend.views.api_doc_variables import key_parameter, site_slug_parameter
from backend.views.base_views import FVPermissionViewSetMixin, SiteContentViewSetMixin


@extend_schema_view(
    list=extend_schema(
        description="A list of available site feature flags for the current site.",
        responses={
            200: OpenApiResponse(
                description=doc_strings.success_200_list,
                response=SiteFeatureDetailSerializer,
            ),
            403: OpenApiResponse(description=doc_strings.error_403_site_access_denied),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
        parameters=[site_slug_parameter],
    ),
    retrieve=extend_schema(
        description="Details about a feature flag for the current site.",
        responses={
            200: OpenApiResponse(
                description=doc_strings.success_200_detail,
                response=SiteFeatureDetailSerializer,
            ),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404),
        },
        parameters=[
            site_slug_parameter,
            key_parameter,
        ],
    ),
    create=extend_schema(
        description="Create a new feature flag for the site. Site feature keys cannot be changed after creation.",
        responses={
            201: OpenApiResponse(
                description=doc_strings.success_201,
                response=SiteFeatureDetailSerializer,
            ),
            400: OpenApiResponse(description=doc_strings.error_400_validation),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
        parameters=[site_slug_parameter],
    ),
    update=extend_schema(
        description="Edit a feature flag for the specified site. Site feature keys cannot be changed after creation.",
        responses={
            200: OpenApiResponse(
                description=doc_strings.success_200_edit,
                response=SiteFeatureDetailSerializer,
            ),
            400: OpenApiResponse(description=doc_strings.error_400_validation),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404),
        },
        parameters=[
            site_slug_parameter,
            key_parameter,
        ],
    ),
    partial_update=extend_schema(
        description="Edit a feature flag for the specified site. Any omitted fields will be unchanged.",
        responses={
            200: OpenApiResponse(
                description=doc_strings.success_200_edit,
                response=SiteFeatureDetailSerializer,
            ),
            400: OpenApiResponse(description=doc_strings.error_400_validation),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404),
        },
        parameters=[
            site_slug_parameter,
            key_parameter,
        ],
    ),
    destroy=extend_schema(
        description="Delete a feature flag from the specified site.",
        responses={
            204: OpenApiResponse(description=doc_strings.success_204_deleted),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404),
        },
        parameters=[site_slug_parameter, key_parameter],
    ),
)
class SiteFeatureViewSet(
    SiteContentViewSetMixin, FVPermissionViewSetMixin, ModelViewSet
):
    """
    API endpoint that allows site feature flags to be viewed or edited.
    """

    lookup_field = "key"
    serializer_class = SiteFeatureDetailSerializer

    def get_queryset(self):
        site = self.get_validated_site()
        return SiteFeature.objects.filter(site=site).select_related(
            "site",
            "site__language",
            "created_by",
            "last_modified_by",
        )
