from rest_framework.serializers import ModelSerializer

from backend.models import Story, StoryPage
from backend.models.media import Image
from backend.serializers.base_serializers import (
    CreateSiteContentSerializerMixin,
    SiteContentLinkedTitleSerializer,
    UpdateSerializerMixin,
    base_id_fields,
    base_timestamp_fields,
)
from backend.serializers.media_serializers import (
    ImageSerializer,
    RelatedMediaSerializerMixin,
    WriteableRelatedImageSerializer,
)
from backend.serializers.site_serializers import LinkedSiteSerializer


class PageSerializer(ModelSerializer, RelatedMediaSerializerMixin):
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
    pages = PageSerializer(many=True)

    def create(self, validated_data):
        pages = validated_data.pop("pages")

        created = super().create(validated_data)

        for index, page_data in enumerate(pages):
            related_audio = page_data.pop("related_audio")
            related_videos = page_data.pop("related_videos")
            related_images = page_data.pop("related_images")

            created_page = StoryPage.objects.create(
                story=created, ordering=index, **page_data
            )

            created_page.related_audio.set(related_audio)
            created_page.related_videos.set(related_videos)
            created_page.related_images.set(related_images)

        return created

    def update(self, instance, validated_data):
        StoryPage.objects.filter(story__id=instance.id).delete()
        try:
            pages = validated_data.pop("pages")
            for index, page_data in enumerate(pages):
                related_audio = page_data.pop("related_audio")
                related_videos = page_data.pop("related_videos")
                related_images = page_data.pop("related_images")

                created_page = StoryPage.objects.create(
                    story=instance, ordering=index, **page_data
                )

                created_page.related_audio.set(related_audio)
                created_page.related_videos.set(related_videos)
                created_page.related_images.set(related_images)
        except KeyError:
            pass

        return super().update(instance, validated_data)

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
                "exclude_from_games",
                "exclude_from_kids",
            )
        )


class StoryListSerializer(SiteContentLinkedTitleSerializer):
    cover_image = ImageSerializer()

    class Meta(SiteContentLinkedTitleSerializer.Meta):
        model = Story
        fields = SiteContentLinkedTitleSerializer.Meta.fields + (
            "title_translation",
            "cover_image",
            "exclude_from_games",
            "exclude_from_kids",
        )
