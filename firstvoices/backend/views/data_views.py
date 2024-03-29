import json

from django.db.models import Prefetch
from django.http import HttpResponseNotFound
from drf_spectacular.utils import (
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
    inline_serializer,
)
from rest_framework import mixins, serializers, viewsets
from rest_framework.renderers import BrowsableAPIRenderer, JSONRenderer
from rest_framework.response import Response
from rules.contrib.rest_framework import AutoPermissionViewSetMixin

from backend.models import Alphabet, MTDExportFormat
from backend.models.dictionary import DictionaryEntry
from backend.models.media import Audio, Image
from backend.permissions import utils
from backend.serializers.site_data_serializers import (
    DictionaryEntryDataSerializer,
    DictionaryEntryPaginator,
    MTDSiteDataSerializer,
    SiteDataSerializer,
)
from backend.views.api_doc_variables import site_slug_parameter
from backend.views.base_views import SiteContentViewSetMixin, ThrottlingMixin

from . import doc_strings


class SnakeCaseJSONRenderer(JSONRenderer):
    def render(self, data, media_type=None, renderer_context=None):
        # convert data keys to snake_case
        data = json.loads(json.dumps(data, separators=(",", ":")))
        return super().render(data, renderer_context=renderer_context)


@extend_schema_view(
    list=extend_schema(
        description="Returns a site data object in the MTD format. The endpoint returns a config containing the "
        "alphabet and site info, as well as data containing an export of site dictionary entries and "
        "categories. Additional information on the MTD format can be found on the Mother Tongues "
        "documentation: https://docs.mothertongues.org/docs/mtd-guides-prepare",
        # NOTE: The documentation responses here are not correct, but the endpoint is destined to be removed anyways.
        responses={
            200: inline_serializer(
                name="InlineUserSerializer",
                fields={
                    "siteDataExport": serializers.DictField(),
                },
            ),
        },
        parameters=[site_slug_parameter],
    ),
)
class SitesDataViewSet(
    ThrottlingMixin,
    AutoPermissionViewSetMixin,
    SiteContentViewSetMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    http_method_names = ["get"]
    serializer_class = DictionaryEntryDataSerializer
    pagination_class = DictionaryEntryPaginator
    renderer_classes = [SnakeCaseJSONRenderer, BrowsableAPIRenderer]

    def get_queryset(self):
        site = self.get_validated_site()
        return DictionaryEntry.objects.filter(site__id__in=site).prefetch_related(
            "part_of_speech",
            "site",
            Prefetch(
                "related_audio",
                queryset=Audio.objects.all()
                .select_related(
                    "original",
                )
                .prefetch_related(
                    "speakers",
                ),
            ),
            Prefetch(
                "related_images",
                queryset=Image.objects.all().select_related(
                    "original",
                ),
            ),
            Prefetch("site__alphabet_set", queryset=Alphabet.objects.all()),
            "translation_set",
            "categories",
            "categories__parent",
            "acknowledgement_set",
            "note_set",
        )

    def list(self, request, *args, **kwargs):
        queryset = utils.filter_by_viewable(request.user, self.get_queryset())
        paginator = DictionaryEntryPaginator()
        page = paginator.paginate_queryset(queryset, request)
        serializer = self.get_serializer(page, many=True)

        data = {}

        site = (
            self.get_validated_site()
            .select_related("language", "created_by", "last_modified_by")
            .prefetch_related(
                "category_set__parent",
            )
        )

        site_config_and_categories_json = SiteDataSerializer(
            site[0], context={"request": request}
        ).data

        data = {**site_config_and_categories_json}

        if page is not None:
            paginated_data = paginator.get_paginated_data(serializer.data)
            for key, value in paginated_data.items():
                data[key] = value

        return Response(data)


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
    serializer_class = MTDSiteDataSerializer
    renderer_classes = [JSONRenderer, BrowsableAPIRenderer]

    def get_queryset(self):
        site = self.get_validated_site()
        return MTDExportFormat.objects.filter(site__id__in=site)

    def list(self, request, *args, **kwargs):
        site = self.get_validated_site()
        mtd_exports_for_site = MTDExportFormat.objects.filter(site__id__in=site)

        if mtd_exports_for_site:
            return Response(mtd_exports_for_site.latest().latest_export_result)
        return HttpResponseNotFound(
            "Site has not been indexed yet. MTD export format not found."
        )
