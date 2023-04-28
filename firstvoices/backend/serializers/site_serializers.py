from rest_framework import serializers
from rest_framework.reverse import reverse

from backend.models.app import AppJson
from backend.models.sites import Site


class SiteSummarySerializer(serializers.HyperlinkedModelSerializer):
    """
    Serializes public, non-access-controlled information about a site object. This includes the type of info
    required for an "Explore Languages" type interface.
    """

    visibility = serializers.CharField(source="get_visibility_display")
    url = serializers.HyperlinkedIdentityField(
        view_name="api:site-detail", lookup_field="slug"
    )
    language = serializers.StringRelatedField()

    class Meta:
        model = Site
        fields = (
            "id",
            "title",
            "slug",
            "language",
            "visibility",
            "url",
        )


class FeatureFlagSerializer(serializers.Serializer):
    key = serializers.CharField()
    is_enabled = serializers.BooleanField()


class SiteDetailSerializer(SiteSummarySerializer):
    """
    Serializes basic details about a site object, including access-controlled related information.
    """

    features = FeatureFlagSerializer(source="sitefeature_set", many=True)
    menu = serializers.SerializerMethodField()
    characters = serializers.SerializerMethodField()
    ignored_characters = serializers.SerializerMethodField()
    dictionary = serializers.SerializerMethodField()

    def get_menu(self, site):
        return site.menu.json if hasattr(site, "menu") else self.get_default_menu()

    def get_default_menu(self):
        default_menu = AppJson.objects.filter(key="default_site_menu")
        return default_menu[0].json if len(default_menu) > 0 else None

    def get_characters(self, site):
        return self.get_site_content_link(site, "api:characters-list")

    def get_ignored_characters(self, site):
        return self.get_site_content_link(site, "api:ignored-characters-list")

    def get_dictionary(self, site):
        return self.get_site_content_link(site, "api:dictionary-list")

    def get_site_content_link(self, site, view_name):
        return reverse(
            view_name,
            args=[site.slug],
            request=self.context["request"],
        )

    class Meta(SiteSummarySerializer.Meta):
        fields = SiteSummarySerializer.Meta.fields + (
            "menu",
            "features",
            "characters",
            "ignored_characters",
            "dictionary",
        )
