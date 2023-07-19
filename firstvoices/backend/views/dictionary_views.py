from django.db.models import Prefetch
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import viewsets

from backend.models.dictionary import DictionaryEntry
from backend.models.media import Audio, Image, Video
from backend.serializers.dictionary_serializers import DictionaryEntryDetailSerializer
from backend.views.api_doc_variables import id_parameter, site_slug_parameter
from backend.views.base_views import (
    DictionarySerializerContextMixin,
    FVPermissionViewSetMixin,
    SiteContentViewSetMixin,
)


@extend_schema_view(
    list=extend_schema(
        description="A list of available dictionary entries for the specified site.",
        responses={
            200: DictionaryEntryDetailSerializer,
            403: OpenApiResponse(description="Todo: Not authorized for this Site"),
            404: OpenApiResponse(description="Todo: Site not found"),
        },
        parameters=[site_slug_parameter],
    ),
    retrieve=extend_schema(
        description="A dictionary entry from the specified site.",
        responses={
            200: DictionaryEntryDetailSerializer,
            403: OpenApiResponse(description="Todo: Error Not Authorized"),
            404: OpenApiResponse(description="Todo: Not Found"),
        },
        parameters=[
            site_slug_parameter,
            id_parameter,
        ],
    ),
)
class DictionaryViewSet(
    FVPermissionViewSetMixin,
    SiteContentViewSetMixin,
    DictionarySerializerContextMixin,
    viewsets.ModelViewSet,
):
    """
    Dictionary entry information.
    """

    http_method_names = ["get", "post", "put", "delete"]
    serializer_class = DictionaryEntryDetailSerializer

    def get_queryset(self):
        site = self.get_validated_site()
        if len(site) > 0:
            return (
                DictionaryEntry.objects.filter(site__slug=site[0].slug)
                .select_related("site")
                .prefetch_related(
                    "acknowledgement_set",
                    "alternatespelling_set",
                    "note_set",
                    "pronunciation_set",
                    "translation_set",
                    "translation_set__part_of_speech",
                    "categories",
                    Prefetch(
                        "related_dictionary_entries",
                        queryset=DictionaryEntry.objects.visible(self.request.user),
                    ),
                    Prefetch(
                        "related_audio",
                        queryset=Audio.objects.visible(self.request.user),
                    ),
                    Prefetch(
                        "related_images",
                        queryset=Image.objects.visible(self.request.user),
                    ),
                    Prefetch(
                        "related_videos",
                        queryset=Video.objects.visible(self.request.user),
                    ),
                )
            )
        else:
            return DictionaryEntry.objects.none()
