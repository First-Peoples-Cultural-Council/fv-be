from rest_framework.serializers import ModelSerializer

from backend.models import Song, TranslatedText
from backend.serializers.base_serializers import SiteContentLinkedTitleSerializer, base_timestamp_fields
from backend.serializers.media_serializers import RelatedMediaSerializerMixin, ImageSerializer
from backend.serializers.site_serializers import LinkedSiteSerializer


class TranslatedTextSerializer(ModelSerializer):
    class Meta:
        model = TranslatedText
        fields = ('text', 'language')


class SongDetailSerializer(
    RelatedMediaSerializerMixin,
    SiteContentLinkedTitleSerializer
):
    cover_image = ImageSerializer()
    site = LinkedSiteSerializer()
    title_translations = TranslatedTextSerializer(many=True)
    introduction_translations = TranslatedTextSerializer(many=True)
    lyrics_translations = TranslatedTextSerializer(many=True)

    class Meta(SiteContentLinkedTitleSerializer.Meta):
        model = Song
        fields = (
            base_timestamp_fields
            + RelatedMediaSerializerMixin.Meta.fields
            + ("url",
               "id",
               "title",
               "site",
               "cover_image",
               "title",
               "title_translations",
               "introduction",
               "introduction_translations",
               "lyrics",
               "lyrics_translations",
               "authours")
        )


class SongListSerializer(SiteContentLinkedTitleSerializer):
    class Meta(SiteContentLinkedTitleSerializer.Meta):
        model = Song
