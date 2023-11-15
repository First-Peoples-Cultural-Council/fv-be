import json

from django.db.models import Prefetch
from drf_spectacular.utils import extend_schema, extend_schema_view, inline_serializer
from rest_framework import mixins, serializers, viewsets
from rest_framework.renderers import BrowsableAPIRenderer, JSONRenderer
from rules.contrib.rest_framework import AutoPermissionViewSetMixin

from backend.models import Alphabet, Site
from backend.models.dictionary import DictionaryEntry
from backend.models.media import Audio, Image
from backend.serializers.site_data_serializers import SiteDataSerializer
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
    serializer_class = SiteDataSerializer
    pagination_class = None
    renderer_classes = [SnakeCaseJSONRenderer]

    def get_queryset(self):
        site = self.get_validated_site()
        if site.count() > 0:
            return site.select_related(
                "language", "created_by", "last_modified_by"
            ).prefetch_related(
                "category_set__parent",
                Prefetch(
                    "dictionaryentry_set",
                    queryset=DictionaryEntry.objects.all()
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
                    ),
                ),
            )
        else:
            return Site.objects.none()
