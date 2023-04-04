from rest_framework import serializers

from firstvoices.backend.models import AppJson
from firstvoices.backend.models.sites import Language, Site


class SiteSummarySerializer(serializers.HyperlinkedModelSerializer):
    """
    Serializes public, non-access-controlled information about a site object. This includes the type of info
    required for an "Explore Languages" type interface.
    """

    visibility = serializers.CharField(source="get_visibility_display")
    url = serializers.HyperlinkedIdentityField(
        view_name="api:site-detail", lookup_field="slug"
    )

    class Meta:
        model = Site
        fields = (
            "id",
            "title",
            "slug",
            "visibility",
            "url",
        )


class FeatureFlagSerializer(serializers.Serializer):
    key = serializers.CharField()
    is_enabled = serializers.BooleanField()


class LinkedTitleLanguageSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="api:language-detail")

    class Meta:
        model = Language
        fields = ("title", "url")


class SiteDetailSerializer(SiteSummarySerializer):
    """
    Serializes details about a site object, including access-controlled related information.
    """

    language = LinkedTitleLanguageSerializer()
    features = FeatureFlagSerializer(source="sitefeature", many=True)
    menu = serializers.SerializerMethodField()

    def get_menu(self, site):
        return site.menu.json if hasattr(site, "menu") else self.get_default_menu()

    def get_default_menu(self):
        default_menu = AppJson.objects.filter(key="default_site_menu")
        return default_menu[0].json if len(default_menu) > 0 else None

    class Meta(SiteSummarySerializer.Meta):
        fields = SiteSummarySerializer.Meta.fields + ("language", "menu", "features")


class LanguageSerializer(serializers.HyperlinkedModelSerializer):
    language_family = serializers.StringRelatedField()
    sites = SiteSummarySerializer(many=True)
    url = serializers.HyperlinkedIdentityField(view_name="api:language-detail")

    class Meta:
        model = Language
        fields = [
            "id",
            "title",
            "url",
            "alternate_names",
            "language_code",
            "language_family",
            "sites",
        ]
