from django.db.models import Prefetch
from drf_spectacular.utils import (
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
    inline_serializer,
)
from rest_framework import serializers, viewsets

from backend.models.dictionary import DictionaryEntry, TypeOfDictionaryEntry
from backend.models.media import Audio, Image, Video
from backend.serializers.dictionary_serializers import (
    AcknowledgementSerializer,
    AlternateSpellingSerializer,
    CategorySerializer,
    DictionaryEntryDetailSerializer,
    NoteSerializer,
    PronunciationSerializer,
    TranslationSerializer,
)
from backend.views.api_doc_variables import id_parameter, site_slug_parameter
from backend.views.base_views import (
    DictionarySerializerContextMixin,
    FVPermissionViewSetMixin,
    SiteContentViewSetMixin,
)

from ..models.constants import Visibility
from . import doc_strings


@extend_schema_view(
    list=extend_schema(
        description="A list of available dictionary entries for the specified site.",
        responses={
            200: OpenApiResponse(
                description=doc_strings.success_200_list,
                response=DictionaryEntryDetailSerializer,
            ),
            403: OpenApiResponse(description=doc_strings.error_403_site_access_denied),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
        parameters=[site_slug_parameter],
    ),
    retrieve=extend_schema(
        description="A dictionary entry from the specified site.",
        responses={
            200: OpenApiResponse(
                description=doc_strings.success_200_detail,
                response=DictionaryEntryDetailSerializer,
            ),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404),
        },
        parameters=[
            site_slug_parameter,
            id_parameter,
        ],
    ),
    create=extend_schema(
        description="Create a new dictionary entry for the specified site.",
        responses={
            201: OpenApiResponse(
                description=doc_strings.success_201,
                response=inline_serializer(
                    name="DictionaryEntryWriteResponse",
                    fields={
                        "title": serializers.CharField(),
                        "type": serializers.ChoiceField(
                            choices=TypeOfDictionaryEntry.choices,
                            default=TypeOfDictionaryEntry.WORD,
                        ),
                        "visibility_value": serializers.ChoiceField(
                            choices=Visibility.choices,
                            default=Visibility.TEAM,
                            write_only=True,
                        ),
                        "categories": CategorySerializer(many=True),
                        "exclude_from_games": serializers.BooleanField(),
                        "exclude_from_kids": serializers.BooleanField(),
                        "acknowledgements": AcknowledgementSerializer(
                            many=True,
                            required=False,
                            source="acknowledgement_set",
                        ),
                        "alternate_spellings": AlternateSpellingSerializer(
                            many=True,
                            required=False,
                            source="alternate_spelling_set",
                        ),
                        "notes": NoteSerializer(
                            many=True,
                            required=False,
                            source="note_set",
                        ),
                        "translations": TranslationSerializer(
                            many=True,
                            required=False,
                            source="translation_set",
                        ),
                        "pronunciations": PronunciationSerializer(
                            many=True,
                            required=False,
                            source="pronunciation_set",
                        ),
                    },
                ),
            ),
            400: OpenApiResponse(description=doc_strings.error_400_validation),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
        parameters=[site_slug_parameter],
    ),
    update=extend_schema(
        description="Update a dictionary entry on the specified site.",
        responses={
            200: OpenApiResponse(
                description=doc_strings.success_200_detail,
                response=inline_serializer(
                    name="DictionaryEntryWriteResponse",
                    fields={
                        "title": serializers.CharField(),
                        "type": serializers.ChoiceField(
                            choices=TypeOfDictionaryEntry.choices,
                            default=TypeOfDictionaryEntry.WORD,
                        ),
                        "visibility_value": serializers.ChoiceField(
                            choices=Visibility.choices,
                            default=Visibility.TEAM,
                            write_only=True,
                        ),
                        "categories": CategorySerializer(many=True),
                        "exclude_from_games": serializers.BooleanField(),
                        "exclude_from_kids": serializers.BooleanField(),
                        "acknowledgements": AcknowledgementSerializer(
                            many=True,
                            required=False,
                            source="acknowledgement_set",
                        ),
                        "alternate_spellings": AlternateSpellingSerializer(
                            many=True,
                            required=False,
                            source="alternate_spelling_set",
                        ),
                        "notes": NoteSerializer(
                            many=True,
                            required=False,
                            source="note_set",
                        ),
                        "translations": TranslationSerializer(
                            many=True,
                            required=False,
                            source="translation_set",
                        ),
                        "pronunciations": PronunciationSerializer(
                            many=True,
                            required=False,
                            source="pronunciation_set",
                        ),
                    },
                ),
            ),
            400: OpenApiResponse(description=doc_strings.error_400_validation),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404),
        },
        parameters=[site_slug_parameter, id_parameter],
    ),
    destroy=extend_schema(
        description="Delete a dictionary entry from the specified site.",
        responses={
            204: OpenApiResponse(description=doc_strings.success_204_deleted),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404),
        },
        parameters=[site_slug_parameter, id_parameter],
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
