from rest_framework import serializers

from backend.models import Image
from backend.models.galleries import Gallery, GalleryItem
from backend.serializers.base_serializers import (
    WritableSiteContentSerializer,
    base_id_fields,
    base_timestamp_fields,
)
from backend.serializers.media_serializers import WriteableRelatedImageSerializer
from backend.serializers.validators import SameSite


class GalleryItemSerializer(serializers.ModelSerializer):
    """
    Serializer for GalleryItem model.
    """

    image = WriteableRelatedImageSerializer(
        required=True,
        queryset=Image.objects.all(),
        validators=[SameSite()],
    )

    class Meta:
        model = GalleryItem
        fields = ("image", "order")


class GalleryDetailSerializer(WritableSiteContentSerializer):
    """
    Serializer for Gallery model.
    """

    cover_image = WriteableRelatedImageSerializer(
        required=False,
        queryset=Image.objects.all(),
        allow_null=True,
        validators=[SameSite()],
    )
    gallery_items = GalleryItemSerializer(
        many=True, required=False, source="galleryitem_set"
    )

    def create(self, validated_data):
        gallery_items = validated_data.pop("galleryitem_set", [])

        created = super().create(validated_data)

        for gallery_item in gallery_items:
            GalleryItem.objects.create(gallery=created, **gallery_item)
        return created

    def update(self, instance, validated_data):
        if "galleryitem_set" in validated_data:
            GalleryItem.objects.filter(gallery=instance).delete()
            gallery_items = validated_data.pop("galleryitem_set", [])
            for gallery_item in gallery_items:
                GalleryItem.objects.create(gallery=instance, **gallery_item)

        return super().update(instance, validated_data)

    class Meta:
        model = Gallery
        fields = (
            base_timestamp_fields
            + base_id_fields
            + (
                "site",
                "title_translation",
                "introduction",
                "introduction_translation",
                "cover_image",
                "gallery_items",
            )
        )
