from rest_framework.serializers import ModelSerializer

from backend.models import Lyric, Song
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
)
from backend.serializers.site_serializers import LinkedSiteSerializer


class LyricSerializer(ModelSerializer):
    class Meta:
        model = Lyric
        fields = ("id", "text", "translation")
        read_only_fields = ("id",)


class SongSerializer(
    UpdateSerializerMixin,
    CreateSiteContentSerializerMixin,
    RelatedMediaSerializerMixin,
    SiteContentLinkedTitleSerializer,
):
    cover_image = ImageSerializer()
    site = LinkedSiteSerializer()
    lyrics = LyricSerializer(many=True)

    class Meta(SiteContentLinkedTitleSerializer.Meta):
        model = Song
        read_only_fields = (base_id_fields, base_timestamp_fields, "cover_image")
        fields = (
            base_timestamp_fields
            + RelatedMediaSerializerMixin.Meta.fields
            + (
                "url",
                "id",
                "hide_overlay",
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
    cover_image = ImageSerializer()

    class Meta(SiteContentLinkedTitleSerializer.Meta):
        model = Song
        fields = SiteContentLinkedTitleSerializer.Meta.fields + (
            "title_translation",
            "cover_image",
            "hide_overlay",
            "exclude_from_games",
            "exclude_from_kids",
        )
