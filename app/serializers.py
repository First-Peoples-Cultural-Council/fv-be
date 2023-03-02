from rest_framework import serializers

from .models import Language, Word, Phrase


# Used to convert the language between an object and JSON
class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ['id', 'title', 'description', 'state']


# Used to convert the language between an object and JSON with fewer fields
# (for tacking onto the words/phrases endpoints)
class LanguageShortenedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ['id', 'title']


# Used to convert the words between an object and JSON
class WordSerializer(serializers.ModelSerializer):
    language = LanguageShortenedSerializer()

    class Meta:
        model = Word
        fields = ['id', 'title', 'state', 'language']


# Used to convert the phrases between an object and JSON
class PhraseSerializer(serializers.ModelSerializer):
    language = LanguageShortenedSerializer()

    class Meta:
        model = Phrase
        fields = ['id', 'title', 'state', 'language']
