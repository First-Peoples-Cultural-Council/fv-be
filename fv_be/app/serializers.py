from rest_framework import serializers

from .models.sites import Site


class SiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Site
        fields = ["id", "title", "slug", "language", "language_family", "visibility"]
