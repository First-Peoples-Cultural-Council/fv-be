from rest_framework import serializers
from rest_framework.reverse import reverse

from backend.models.app import AppJson
from backend.models.sites import Site
from backend.serializers.base_serializers import base_id_fields
from backend.serializers.media_serializers import ImageSerializer, VideoSerializer


class LinkedSiteSerializer(serializers.HyperlinkedModelSerializer):
    """
    Minimal info about a site, suitable for serializing a site as a related field.
    """

    url = serializers.HyperlinkedIdentityField(
        view_name="api:site-detail", lookup_field="slug"
    )
    language = serializers.StringRelatedField()
    visibility = serializers.CharField(source="get_visibility_display")

    class Meta:
        model = Site
        fields = base_id_fields + ("slug", "visibility", "language")


class SiteSummarySerializer(LinkedSiteSerializer):
    """
    Serializes public, non-access-controlled information about a site object. This includes the type of info
    required for an "Explore Languages" type interface.
    """

    logo = ImageSerializer()

    class Meta(LinkedSiteSerializer.Meta):
        fields = LinkedSiteSerializer.Meta.fields + ("logo",)


class FeatureFlagSerializer(serializers.Serializer):
    id = serializers.CharField()
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
    dictionary_cleanup = serializers.SerializerMethodField()
    dictionary_cleanup_preview = serializers.SerializerMethodField()
    categories = serializers.SerializerMethodField()
    word_of_the_day = serializers.SerializerMethodField()
    banner_image = ImageSerializer()
    banner_video = VideoSerializer()

    def get_menu(self, site):
        return site.menu.json if hasattr(site, "menu") else self.get_default_menu()

    def get_default_menu(self):
        default_menu = AppJson.objects.filter(key="default_site_menu")
        return default_menu[0].json if len(default_menu) > 0 else None

    def get_characters(self, site):
        return self.get_site_content_link(site, "api:character-list")

    def get_ignored_characters(self, site):
        return self.get_site_content_link(site, "api:ignoredcharacter-list")

    def get_dictionary(self, site):
        return self.get_site_content_link(site, "api:dictionaryentry-list")

    def get_dictionary_cleanup(self, site):
        return self.get_site_content_link(site, "api:dictionary-cleanup-list")

    def get_dictionary_cleanup_preview(self, site):
        return self.get_site_content_link(site, "api:dictionary-cleanup/preview-list")

    def get_categories(self, site):
        return self.get_site_content_link(site, "api:category-list")

    def get_word_of_the_day(self, site):
        return self.get_site_content_link(site, "api:word-of-the-day-list")

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
            "dictionary_cleanup",
            "dictionary_cleanup_preview",
            "categories",
            "word_of_the_day",
            "banner_image",
            "banner_video",
        )
