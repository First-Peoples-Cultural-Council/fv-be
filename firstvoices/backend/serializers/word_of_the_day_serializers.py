from rest_framework import serializers

from backend.models.dictionary import WordOfTheDay
from backend.serializers.dictionary_serializers import DictionaryEntryDetailSerializer


class WordOfTheDayListSerializer(serializers.ModelSerializer):
    dictionary_entry = DictionaryEntryDetailSerializer()

    class Meta:
        model = WordOfTheDay
        fields = ["date", "dictionary_entry"]
