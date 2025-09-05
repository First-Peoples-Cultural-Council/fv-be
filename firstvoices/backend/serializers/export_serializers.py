from rest_framework import serializers

from backend.models import DictionaryEntry
from backend.serializers.base_serializers import ReadOnlyVisibilityFieldMixin
from backend.serializers.search_result_serializers import (
    SearchResultPrefetchMixin,
    SearchResultSerializer,
)


class DictionaryEntryExportResultSerializer(
    ReadOnlyVisibilityFieldMixin, SearchResultPrefetchMixin, serializers.ModelSerializer
):
    part_of_speech = serializers.StringRelatedField()
    categories = serializers.StringRelatedField(many=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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
            "related_audio",
            "related_images",
            "related_videos",
            "part_of_speech",
            "related_video_links",
            "related_dictionary_entries",
            "exclude_from_games",
            "exclude_from_kids",
        )


class DictionaryEntryExportSerializer(SearchResultSerializer):
    entry_serializer = DictionaryEntryExportResultSerializer

    @staticmethod
    def get_type(obj):
        return obj["entry"].type
