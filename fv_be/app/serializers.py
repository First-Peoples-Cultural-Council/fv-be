from rest_framework import serializers

from .models import Site, Word


# Used to convert the language between an object and JSON
class SiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Site
        fields = ["id", "title", "state"]


# Used to convert the language between an object and JSON with fewer fields
# (for tacking onto the words/phrases endpoints)
class SiteShortenedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Site
        fields = ["id", "title"]


# Used to convert the words between an object and JSON
class WordSerializer(serializers.ModelSerializer):
    site = SiteShortenedSerializer()

    class Meta:
        model = Word
        fields = ["id", "title", "site", "state"]
