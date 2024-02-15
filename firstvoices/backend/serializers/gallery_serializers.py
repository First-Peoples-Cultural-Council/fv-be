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
        fields = ("image", "ordering")


class GallerySummarySerializer(WritableSiteContentSerializer):
    """
    List serializer for Gallery model.
    """

    cover_image = WriteableRelatedImageSerializer(
        required=False,
        queryset=Image.objects.all(),
        allow_null=True,
        validators=[SameSite()],
    )

    def validate(self, attrs):
        """
        Validate that gallery items are unique.
        """
        gallery_items = attrs.get("galleryitem_set", [])
        if len(gallery_items) != len({x["image"] for x in gallery_items}):
            raise serializers.ValidationError("Gallery items must be unique.")
        return super().validate(attrs)

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
            )
        )


class GalleryDetailSerializer(GallerySummarySerializer):
    """
    Detail serializer for Gallery model.
    """

    gallery_items = GalleryItemSerializer(
        many=True, required=False, source="galleryitem_set"
    )

    class Meta(GallerySummarySerializer.Meta):
        fields = GallerySummarySerializer.Meta.fields + ("gallery_items",)
