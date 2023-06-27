from rest_framework.serializers import ModelSerializer

from backend.models import Lyric, Song
from backend.serializers.base_serializers import (
    SiteContentLinkedTitleSerializer,
    base_timestamp_fields,
)
from backend.serializers.media_serializers import (
    ImageSerializer,
    RelatedMediaSerializerMixin,
)
from backend.serializers.site_serializers import LinkedSiteSerializer


class LyricSerializer(ModelSerializer):
    class Meta:
        model = Lyric
        fields = ("text", "translation")


class SongDetailSerializer(
    RelatedMediaSerializerMixin, SiteContentLinkedTitleSerializer
):
    cover_image = ImageSerializer()
    site = LinkedSiteSerializer()

    lyrics = LyricSerializer(many=True)

    class Meta(SiteContentLinkedTitleSerializer.Meta):
        model = Song
        fields = (
            base_timestamp_fields
            + RelatedMediaSerializerMixin.Meta.fields
            + (
                "url",
                "id",
                "hide_overlay",
                "title",
                "site",
                "cover_image",
                "title",
                "title_translation",
                "introduction",
                "introduction_translation",
                "notes",
                "lyrics",
                "acknowledgements",
                "exclude_from_games",
                "exclude_from_kids",
            )
        )


class SongListSerializer(SiteContentLinkedTitleSerializer):
    class Meta(SiteContentLinkedTitleSerializer.Meta):
        model = Song
