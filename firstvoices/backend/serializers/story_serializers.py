from rest_framework import serializers
from rest_framework_nested.relations import NestedHyperlinkedIdentityField
from rest_framework_nested.serializers import NestedHyperlinkedModelSerializer

from backend.models import Story, StoryPage
from backend.models.media import Image
from backend.serializers.base_serializers import (
    CreateControlledSiteContentSerializerMixin,
    SiteContentLinkedTitleSerializer,
    SiteContentUrlMixin,
    UpdateSerializerMixin,
    WritableVisibilityField,
    audience_fields,
    base_id_fields,
    base_timestamp_fields,
)
from backend.serializers.media_serializers import (
    ImageSerializer,
    RelatedMediaSerializerMixin,
    WriteableRelatedImageSerializer,
)
from backend.serializers.site_serializers import LinkedSiteSerializer
from backend.serializers.utils import get_story_from_context


class LinkedStorySerializer(SiteContentLinkedTitleSerializer):
    class Meta(SiteContentLinkedTitleSerializer.Meta):
        model = Story


class StoryPageSummarySerializer(
    RelatedMediaSerializerMixin, SiteContentUrlMixin, NestedHyperlinkedModelSerializer
):
    serializer_url_field = NestedHyperlinkedIdentityField

    parent_lookup_kwargs = {
        "site_slug": "site__slug",
        "story_pk": "story__pk",
    }

    id = serializers.UUIDField(read_only=True)

    class Meta:
        model = StoryPage
        fields = RelatedMediaSerializerMixin.Meta.fields + (
            "id",
            "url",
            "text",
            "translation",
            "notes",
            "ordering",
        )


class StoryPageDetailSerializer(
    CreateControlledSiteContentSerializerMixin, StoryPageSummarySerializer
):
    story = LinkedStorySerializer(read_only=True)

    class Meta(StoryPageSummarySerializer.Meta):
        fields = StoryPageSummarySerializer.Meta.fields + ("story",)

    def validate(self, attrs):
        """use the visibility from the parent story for all permission checks"""
        story = get_story_from_context(self)
        attrs["visibility"] = story.visibility
        return super().validate(attrs)

    def create(self, validated_data):
        return super().create(self.add_story_id(validated_data))

    def update(self, instance, validated_data):
        return super().update(instance, self.add_story_id(validated_data))

    def add_story_id(self, validated_data):
        validated_data["story"] = get_story_from_context(self)
        return validated_data


class StorySerializer(
    CreateControlledSiteContentSerializerMixin,
    RelatedMediaSerializerMixin,
    UpdateSerializerMixin,
    SiteContentLinkedTitleSerializer,
):
    cover_image = WriteableRelatedImageSerializer(
        allow_null=True, queryset=Image.objects.all()
    )
    site = LinkedSiteSerializer(required=False, read_only=True)
    pages = StoryPageSummarySerializer(many=True, read_only=True)
    visibility = WritableVisibilityField(required=True)

    class Meta(SiteContentLinkedTitleSerializer.Meta):
        model = Story
        read_only_fields = (
            base_id_fields,
            base_timestamp_fields,
            "site",
        )
        fields = (
            base_timestamp_fields
            + RelatedMediaSerializerMixin.Meta.fields
            + audience_fields
            + (
                "url",
                "id",
                "site",
                "cover_image",
                "author",
                "visibility",
                "title",
                "title_translation",
                "introduction",
                "introduction_translation",
                "notes",
                "pages",
                "acknowledgements",
                "hide_overlay",
            )
        )


class StoryListSerializer(SiteContentLinkedTitleSerializer):
    cover_image = ImageSerializer()
    visibility = serializers.CharField(read_only=True, source="get_visibility_display")

    class Meta(SiteContentLinkedTitleSerializer.Meta):
        model = Story
        fields = (
            SiteContentLinkedTitleSerializer.Meta.fields
            + audience_fields
            + ("visibility", "title_translation", "cover_image", "hide_overlay")
        )
