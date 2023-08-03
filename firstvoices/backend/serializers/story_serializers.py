from rest_framework import serializers
from rest_framework_nested.relations import NestedHyperlinkedIdentityField
from rest_framework_nested.serializers import NestedHyperlinkedModelSerializer

from backend.models import Story, StoryPage
from backend.models.media import Image
from backend.serializers.base_serializers import (
    BaseControlledSiteContentSerializer,
    CreateControlledSiteContentSerializerMixin,
    SiteContentLinkedTitleSerializer,
    SiteContentUrlMixin,
    WritableControlledSiteContentSerializer,
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
    created = serializers.DateTimeField(read_only=True)
    created_by = serializers.StringRelatedField(read_only=True)
    last_modified = serializers.DateTimeField(read_only=True)
    last_modified_by = serializers.StringRelatedField(read_only=True)
    story = LinkedStorySerializer(read_only=True)
    site = LinkedSiteSerializer(read_only=True)

    class Meta(StoryPageSummarySerializer.Meta):
        fields = (
            base_timestamp_fields
            + StoryPageSummarySerializer.Meta.fields
            + (
                "story",
                "site",
            )
        )

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
    RelatedMediaSerializerMixin,
    WritableControlledSiteContentSerializer,
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
            WritableControlledSiteContentSerializer.Meta.fields
            + (
                "cover_image",
                "author",
                "title_translation",
                "introduction",
                "introduction_translation",
                "notes",
                "pages",
                "acknowledgements",
                "hide_overlay",
            )
            + audience_fields
            + RelatedMediaSerializerMixin.Meta.fields
        )


class StoryListSerializer(BaseControlledSiteContentSerializer):
    cover_image = ImageSerializer()

    class Meta:
        model = Story
        fields = (
            BaseControlledSiteContentSerializer.Meta.fields
            + ("title_translation", "cover_image", "hide_overlay")
            + audience_fields
        )
