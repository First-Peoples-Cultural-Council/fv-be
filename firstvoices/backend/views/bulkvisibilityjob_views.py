from rest_framework.viewsets import ModelViewSet

from backend.models.async_results import BulkVisibilityJob
from backend.serializers.async_results_serializers import BulkVisibilityJobSerializer
from backend.views.base_views import FVPermissionViewSetMixin, SiteContentViewSetMixin


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
            BulkVisibilityJob.objects.filter(site__slug=site[0].slug)
            .select_related("site", "created_by", "last_modified_by")
            .order_by("created")
        )
