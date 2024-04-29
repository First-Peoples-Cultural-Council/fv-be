from django.http import HttpResponseNotFound
from drf_spectacular.utils import (
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
    inline_serializer,
)
from rest_framework import mixins, serializers, viewsets
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rules.contrib.rest_framework import AutoPermissionViewSetMixin

from backend.models import MTDExportFormat
from backend.views.api_doc_variables import site_slug_parameter
from backend.views.base_views import SiteContentViewSetMixin, ThrottlingMixin

from . import doc_strings


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

    def list(self, request, *args, **kwargs):
        site = self.get_validated_site()
        mtd_exports_for_site = (
            MTDExportFormat.objects.filter(site=site.first())
            .filter(is_preview=False)
            .only("latest_export_result")
        )

        if mtd_exports_for_site:
            return Response(mtd_exports_for_site.latest().latest_export_result)
        return HttpResponseNotFound(
            "Site has not been indexed yet. MTD export format not found."
        )
