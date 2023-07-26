from rest_framework.serializers import ModelSerializer

from backend.models import Story, StoryPage
from backend.models.media import Image
from backend.serializers.base_serializers import (
    CreateSiteContentSerializerMixin,
    SiteContentLinkedTitleSerializer,
    UpdateSerializerMixin,
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


class StoryPageSerializer(RelatedMediaSerializerMixin, ModelSerializer):
    class Meta:
        model = StoryPage
        fields = RelatedMediaSerializerMixin.Meta.fields + (
            "id",
            "text",
            "translation",
        )
        read_only_fields = ("id",)


class StorySerializer(
    UpdateSerializerMixin,
    CreateSiteContentSerializerMixin,
    RelatedMediaSerializerMixin,
    SiteContentLinkedTitleSerializer,
):
    cover_image = WriteableRelatedImageSerializer(
        allow_null=True, queryset=Image.objects.all()
    )
    site = LinkedSiteSerializer(required=False, read_only=True)
    pages = StoryPageSerializer(many=True, read_only=True)

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
                "title",
                "title_translation",
                "introduction",
                "introduction_translation",
                "notes",
                "pages",
                "acknowledgements",
            )
        )


class StoryListSerializer(SiteContentLinkedTitleSerializer):
    cover_image = ImageSerializer()

    class Meta(SiteContentLinkedTitleSerializer.Meta):
        model = Story
        fields = (
            SiteContentLinkedTitleSerializer.Meta.fields
            + audience_fields
            + (
                "title_translation",
                "cover_image",
            )
        )
