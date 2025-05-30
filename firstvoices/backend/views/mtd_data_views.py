import hashlib

from drf_spectacular.utils import (
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
    inline_serializer,
)
from rest_framework import mixins, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework_condition import condition
from rules.contrib.rest_framework import AutoPermissionViewSetMixin

from backend.models import MTDExportJob
from backend.models.jobs import JobStatus
from backend.views.api_doc_variables import site_slug_parameter
from backend.views.base_views import (
    FVPermissionViewSetMixin,
    SiteContentViewSetMixin,
    ThrottlingMixin,
)

from ..permissions.utils import filter_by_viewable
from ..serializers.mtd_serializers import MTDExportJobSerializer
from . import doc_strings


def etag_func(request, *args, **kwargs):
    site_slug = kwargs["site_slug"]
    mtd_export_job = MTDExportJob.objects.filter(site__slug=site_slug).latest(
        "system_last_modified"
    )
    if mtd_export_job is not None:
        return hashlib.md5(
            ":".join(str(mtd_export_job.system_last_modified)).encode("utf-8")
        ).hexdigest()
    return None


def last_modified_func(request, *args, **kwargs):
    site_slug = kwargs["site_slug"]
    mtd_export_job = MTDExportJob.objects.filter(site__slug=site_slug).latest(
        "system_last_modified"
    )
    if mtd_export_job is not None:
        return mtd_export_job.system_last_modified
    return None


@extend_schema_view(
    list=extend_schema(
        description="Returns a site data object in the MTD Export format. The endpoint returns a config containing the "
        "MTD Configuration as well as L1 and L2 inverted indices with scores for ranking entries as well as the data"
        "Additional information on the MTD format can be found on the Mother Tongues "
        "documentation: https://mothertongues.github.io/mothertongues/latest/",
        responses={
            200: inline_serializer(
                name="InlineUserSerializer",
                fields={
                    "config": serializers.DictField(),
                    "l1_index": serializers.DictField(),
                    "l2_index": serializers.DictField(),
                    "data": serializers.ListField(),
                },
            ),
            404: OpenApiResponse(description=doc_strings.error_404),
        },
        parameters=[site_slug_parameter],
    ),
)
class MTDSitesDataViewSet(
    ThrottlingMixin,
    AutoPermissionViewSetMixin,
    SiteContentViewSetMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    http_method_names = ["get"]
    renderer_classes = [JSONRenderer]  # no camel-case for this data format
    permission_type_map = {
        **FVPermissionViewSetMixin.permission_type_map,
        "task": None,
    }

    @condition(etag_func=etag_func, last_modified_func=last_modified_func)
    def list(self, request, *args, **kwargs):
        site = self.get_validated_site()
        mtd_exports_for_site = MTDExportJob.objects.filter(
            site=site, status=JobStatus.COMPLETE
        ).only("export_result")

        if mtd_exports_for_site:
            return Response(mtd_exports_for_site.latest().export_result)
        return Response(
            {
                "message": "Site has not been successfully indexed yet. MTD export format not found."
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    @action(detail=False, methods=["get"])
    @condition(etag_func=etag_func, last_modified_func=last_modified_func)
    def task(self, request, *args, **kwargs):
        site = self.get_validated_site()
        mtd_exports_for_site = filter_by_viewable(
            request.user, MTDExportJob.objects.filter(site=site)
        ).order_by("-created")
        if mtd_exports_for_site:
            return Response(
                MTDExportJobSerializer(mtd_exports_for_site, many=True).data
            )
        return Response(
            {"message": "MTD export task information not available."},
            status=status.HTTP_404_NOT_FOUND,
        )
