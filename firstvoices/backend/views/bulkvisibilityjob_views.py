from django.core.exceptions import PermissionDenied
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework.viewsets import ModelViewSet

from backend.models.jobs import BulkVisibilityJob
from backend.permissions.predicates import is_superadmin
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
    create=extend_schema(
        description="Create and queue a new bulk visibility job.",
        responses={
            201: BulkVisibilityJobSerializer,
            400: OpenApiResponse(description=doc_strings.error_400_validation),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404),
        },
        parameters=[site_slug_parameter],
    ),
)
class BulkVisibilityJobViewSet(
    SiteContentViewSetMixin, FVPermissionViewSetMixin, ModelViewSet
):
    """
    API endpoint that allows bulk visibility jobs to be viewed.
    """

    http_method_names = ["get", "post"]
    serializer_class = BulkVisibilityJobSerializer

    def initial(self, *args, **kwargs):
        if not is_superadmin(self.request.user, None):
            raise PermissionDenied
        super().initial(*args, **kwargs)

    def get_queryset(self):
        site = self.get_validated_site()
        return (
            BulkVisibilityJob.objects.filter(site__slug=site[0].slug)
            .select_related("site", "created_by", "last_modified_by")
            .order_by("created")
        )
