import json

from django.db.models import Prefetch
from drf_spectacular.utils import extend_schema, extend_schema_view, inline_serializer
from rest_framework import mixins, serializers, viewsets
from rest_framework.renderers import BrowsableAPIRenderer, JSONRenderer
from rest_framework.response import Response
from rules.contrib.rest_framework import AutoPermissionViewSetMixin

from backend.models import Alphabet, Site
from backend.models.dictionary import DictionaryEntry
from backend.models.media import Audio, Image
from backend.permissions import utils
from backend.serializers.site_data_serializers import (
    DictionaryEntryDataSerializer,
    DictionaryEntryPaginator,
    SiteDataSerializer,
)
from backend.views.api_doc_variables import site_slug_parameter
from backend.views.base_views import SiteContentViewSetMixin, ThrottlingMixin


class SnakeCaseJSONRenderer(BrowsableAPIRenderer):
    def get_default_renderer(self, view):
        return JSONRenderer()

    def render(self, data, media_type=None, renderer_context=None):
        # convert data keys to snake_case
        data = json.loads(json.dumps(data, separators=(",", ":")))
        return super().render(data, renderer_context=renderer_context)


def dict_entry_type_mtd_conversion(type):
    match type:
        case DictionaryEntry.TypeOfDictionaryEntry.WORD:
            return "words"
        case DictionaryEntry.TypeOfDictionaryEntry.PHRASE:
            return "phrases"
        case _:
            return None


@extend_schema_view(
    list=extend_schema(
        description="Returns a site data object in the MTD format. The endpoint returns a config containing the "
        "alphabet and site info, as well as data containing an export of site dictionary entries and "
        "categories. Additional information on the MTD format can be found on the Mother Tongues "
        "documentation: https://docs.mothertongues.org/docs/mtd-guides-prepare",
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
    renderer_classes = [SnakeCaseJSONRenderer]

    def get_queryset(self):
        site = self.get_validated_site()
        if site.count() > 0:
            return (
                DictionaryEntry.objects.filter(site__id__in=site)
                .select_related(
                    "part_of_speech",
                )
                .prefetch_related(
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
            )
        else:
            return DictionaryEntry.objects.none()

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
        if site.count() > 0:
            site_config_and_categories_json = SiteDataSerializer(
                site[0], context={"request": request}
            ).data
        else:
            site_config_and_categories_json = SiteDataSerializer(
                Site.objects.none(), context={"request": request}
            ).data

        for key, value in site_config_and_categories_json.items():
            data[key] = value

        if page is not None:
            paginated_data = paginator.get_paginated_data(serializer.data)
            for key, value in paginated_data.items():
                data[key] = value

        return Response(data)
