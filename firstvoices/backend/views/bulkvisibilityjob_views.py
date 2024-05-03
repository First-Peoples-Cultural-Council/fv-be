from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework.viewsets import ModelViewSet

from backend.models.jobs import BulkVisibilityJob
from backend.serializers.job_serializers import BulkVisibilityJobSerializer
from backend.views import doc_strings
from backend.views.api_doc_variables import id_parameter, site_slug_parameter
from backend.views.base_views import FVPermissionViewSetMixin, SiteContentViewSetMixin


@extend_schema_view(
    list=extend_schema(
        description="A list of all characters available on the specified site.",
        responses={
            200: BulkVisibilityJobSerializer,
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404),
        },
        parameters=[site_slug_parameter],
    ),
    retrieve=extend_schema(
        description="Details about a specific character in the specified site.",
        responses={
            200: BulkVisibilityJobSerializer,
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404),
        },
        parameters=[
            site_slug_parameter,
            id_parameter,
        ],
    ),
)
class BulkVisibilityJobViewSet(
    SiteContentViewSetMixin, FVPermissionViewSetMixin, ModelViewSet
):
    """
    API endpoint that allows bulk visibility jobs to be viewed.
    """

    http_method_names = ["get"]
    serializer_class = BulkVisibilityJobSerializer

    def get_queryset(self):
        site = self.get_validated_site()
        return (
            BulkVisibilityJob.objects.filter(site=site)
            .select_related("site", "created_by", "last_modified_by")
            .order_by("created")
        )
