from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field, extend_schema_serializer
from rest_framework import serializers

from backend.models.app import AppJson
from backend.models.media import Image, Video
from backend.models.sites import SiteFeature
from backend.models.widget import SiteWidget, SiteWidgetList
from backend.serializers.base_serializers import (
    LinkedSiteSerializer,
    UpdateSerializerMixin,
)
from backend.serializers.fields import SiteViewLinkField
from backend.serializers.media_serializers import ImageSerializer, VideoSerializer
from backend.serializers.utils.context_utils import get_site_from_context
from backend.serializers.validators import SameSite
from backend.serializers.widget_serializers import SiteWidgetListSerializer


class FeatureFlagSerializer(serializers.Serializer):
    id = serializers.CharField()
    key = serializers.CharField()
    is_enabled = serializers.BooleanField()


class SiteSummarySerializer(LinkedSiteSerializer):
    """
    Serializes public, non-access-controlled information about a site object. This includes the type of info
    required for an "Explore Languages" type interface.
    """

    logo = ImageSerializer()
    enabled_features = FeatureFlagSerializer(
        read_only=True, source="sitefeature_set", many=True
    )
    is_hidden = serializers.BooleanField(read_only=True)

    class Meta(LinkedSiteSerializer.Meta):
        fields = LinkedSiteSerializer.Meta.fields + (
            "logo",
            "enabled_features",
            "is_hidden",
        )


@extend_schema_serializer(
    exclude_fields=(
        "audio",
        "categories",
        "characters",
        "dictionary",
        "dictionary_cleanup",
        "dictionary_cleanup_preview",
        "documents",
        "features",
        "galleries",
        "ignored_characters",
        "images",
        "immersion_labels",
        "join_requests",
        "memberships",
        "mtd_data",
        "pages",
        "people",
        "songs",
        "stories",
        "videos",
        "widgets",
        "word_of_the_day",
    ),
)
class SiteDetailSerializer(UpdateSerializerMixin, SiteSummarySerializer):
    """
    Serializes basic details about a site object, including access-controlled related information.
    """

    menu = serializers.SerializerMethodField()
    banner_image = ImageSerializer()
    banner_video = VideoSerializer()

    homepage = SiteWidgetListSerializer()

    # api links
    audio = SiteViewLinkField(view_name="api:audio-list")
    bulk_visibility = SiteViewLinkField(view_name="api:bulk-visibility-list")
    categories = SiteViewLinkField(view_name="api:category-list")
    characters = SiteViewLinkField(view_name="api:character-list")
    dictionary = SiteViewLinkField(view_name="api:dictionaryentry-list")
    dictionary_cleanup = SiteViewLinkField(view_name="api:dictionary-cleanup-list")
    dictionary_cleanup_preview = SiteViewLinkField(
        view_name="api:dictionary-cleanup-preview-list"
    )
    documents = SiteViewLinkField(view_name="api:document-list")
    features = SiteViewLinkField(view_name="api:sitefeature-list")
    galleries = SiteViewLinkField(view_name="api:gallery-list")
    ignored_characters = SiteViewLinkField(view_name="api:ignoredcharacter-list")
    images = SiteViewLinkField(view_name="api:image-list")
    immersion_labels = SiteViewLinkField(view_name="api:immersionlabel-list")
    join_requests = SiteViewLinkField(view_name="api:joinrequest-list")
    memberships = SiteViewLinkField(view_name="api:membership-list")
    mtd_data = SiteViewLinkField(view_name="api:mtd-data-list")
    pages = SiteViewLinkField(view_name="api:sitepage-list")
    people = SiteViewLinkField(view_name="api:person-list")
    songs = SiteViewLinkField(view_name="api:song-list")
    stats = SiteViewLinkField(view_name="api:stats-list")
    stories = SiteViewLinkField(view_name="api:story-list")
    videos = SiteViewLinkField(view_name="api:video-list")
    widgets = SiteViewLinkField(view_name="api:sitewidget-list")
    word_of_the_day = SiteViewLinkField(view_name="api:word-of-the-day-list")

    @extend_schema_field(OpenApiTypes.STR)
    def get_menu(self, site):
        return site.menu.json if hasattr(site, "menu") else self.get_default_menu(site)

    @staticmethod
    def get_default_menu(site):
        try:
            has_app_feature = SiteFeature.objects.get(site=site, key__iexact="has_app")
            default_menu_key = (
                "has_app_site_menu"
                if has_app_feature.is_enabled
                else "default_site_menu"
            )
        except SiteFeature.DoesNotExist:
            default_menu_key = "default_site_menu"

        default_menu = AppJson.objects.filter(key=default_menu_key)
        return default_menu[0].json if len(default_menu) > 0 else None

    class Meta(SiteSummarySerializer.Meta):
        fields = SiteSummarySerializer.Meta.fields + (
            "menu",
            "banner_image",
            "banner_video",
            "homepage",
            "audio",
            "bulk_visibility",
            "categories",
            "characters",
            "dictionary",
            "dictionary_cleanup",
            "dictionary_cleanup_preview",
            "documents",
            "features",
            "galleries",
            "ignored_characters",
            "images",
            "immersion_labels",
            "join_requests",
            "memberships",
            "mtd_data",
            "pages",
            "people",
            "songs",
            "stats",
            "stories",
            "videos",
            "widgets",
            "word_of_the_day",
        )


class SiteDetailWriteSerializer(SiteDetailSerializer):
    title = serializers.CharField(read_only=True)

    homepage = serializers.PrimaryKeyRelatedField(
        queryset=SiteWidget.objects.all(),
        allow_null=True,
        many=True,
    )
    logo = serializers.PrimaryKeyRelatedField(
        queryset=Image.objects.all(),
        allow_null=True,
        validators=[SameSite()],
    )
    banner_image = serializers.PrimaryKeyRelatedField(
        queryset=Image.objects.all(),
        allow_null=True,
        validators=[],
    )
    banner_video = serializers.PrimaryKeyRelatedField(
        queryset=Video.objects.all(),
        allow_null=True,
        validators=[],
    )

    def validate_homepage(self, homepage):
        site = get_site_from_context(self)
        for site_widget in homepage:
            if site_widget.site != site:
                raise serializers.ValidationError(
                    f"SiteWidget with ID ({site_widget.id}) does not belong to the site."
                )
        return homepage

    def to_representation(self, instance):
        data = SiteDetailSerializer(instance=instance, context=self.context).data
        return data

    def update(self, instance, validated_data):
        if "homepage" in validated_data:
            homepage = instance.homepage
            if not homepage:
                homepage = SiteWidgetList.objects.create(site=instance)
            validated_data["widgets"] = validated_data.pop("homepage")
            homepage = SiteWidgetListSerializer.update(self, homepage, validated_data)
            validated_data["homepage"] = homepage
            instance.homepage = homepage
        return super().update(instance, validated_data)
