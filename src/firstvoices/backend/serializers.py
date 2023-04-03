from rest_framework import serializers

from firstvoices.backend.models.sites import Site


class SiteSerializer(serializers.HyperlinkedModelSerializer):
    visibility = serializers.CharField(source="get_visibility_display")
    url = serializers.HyperlinkedIdentityField(view_name="api:site-detail")
    language = serializers.StringRelatedField()
    language_family = serializers.StringRelatedField()

    class Meta:
        model = Site
        fields = [
            "id",
            "title",
            "slug",
            "language",
            "language_family",
            "visibility",
            "url",
        ]
