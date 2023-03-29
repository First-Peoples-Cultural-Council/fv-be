from rest_framework import serializers

from .models.sites import Site


class SiteSerializer(serializers.ModelSerializer):
    visibility = serializers.CharField(source="get_visibility_display")

    class Meta:
        model = Site
        fields = ["id", "title", "slug", "language", "language_family", "visibility"]
