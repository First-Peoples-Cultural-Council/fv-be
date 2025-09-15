from rest_framework import serializers

from backend.models import DictionaryEntry
from backend.serializers.base_serializers import ReadOnlyVisibilityFieldMixin
from backend.serializers.fields import CommaSeparatedIDsField, InvertedBooleanField
from backend.serializers.search_result_serializers import (
    SearchResultPrefetchMixin,
    SearchResultSerializer,
)


class DictionaryEntryExportResultSerializer(
    ReadOnlyVisibilityFieldMixin, SearchResultPrefetchMixin, serializers.ModelSerializer
):
    part_of_speech = serializers.StringRelatedField()
    categories = serializers.StringRelatedField(many=True)
    include_in_games = InvertedBooleanField(source="exclude_from_games", read_only=True)
    include_on_kids_site = InvertedBooleanField(
        source="exclude_from_kids", read_only=True
    )
    audio_ids = CommaSeparatedIDsField(source="related_audio", read_only=True)
    video_ids = CommaSeparatedIDsField(source="related_videos", read_only=True)
    image_ids = CommaSeparatedIDsField(source="related_images", read_only=True)

    class Meta:
        model = DictionaryEntry
        fields = (
            "id",
            "visibility",
            "title",
            "type",
            "categories",
            "translations",
            "notes",
            "acknowledgements",
            "alternate_spellings",
            "pronunciations",
            "audio_ids",
            "video_ids",
            "image_ids",
            "part_of_speech",
            "related_video_links",
            "related_dictionary_entries",
            "include_in_games",
            "include_on_kids_site",
        )


class DictionaryEntryExportSerializer(SearchResultSerializer):
    entry_serializer = DictionaryEntryExportResultSerializer

    @staticmethod
    def get_type(obj):
        return obj["entry"].type
