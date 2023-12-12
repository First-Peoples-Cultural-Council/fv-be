from rest_framework import serializers

from backend.models.galleries import Gallery, GalleryItem
from backend.serializers.base_serializers import (
    WritableSiteContentSerializer,
    base_id_fields,
    base_timestamp_fields,
)
from backend.serializers.media_serializers import ImageSerializer


class GalleryItemSerializer(serializers.ModelSerializer):
    """
    Serializer for GalleryItem model.
    """

    image = ImageSerializer(read_only=True)

    class Meta:
        model = GalleryItem
        fields = base_timestamp_fields + ("id", "image", "order")
        # validators = [SameSite()]


class GalleryDetailSerializer(WritableSiteContentSerializer):
    """
    Serializer for Gallery model.
    """

    cover_image = ImageSerializer()
    gallery_items = GalleryItemSerializer(
        many=True, required=False, source="galleryitem_set"
    )

    class Meta:
        model = Gallery
        fields = (
            base_timestamp_fields
            + base_id_fields
            + (
                "title_translation",
                "introduction",
                "introduction_translation",
                "cover_image",
                "gallery_items",
            )
        )
        # validators = [SameSite()]
