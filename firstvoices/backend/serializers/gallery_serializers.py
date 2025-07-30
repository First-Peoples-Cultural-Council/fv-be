from rest_framework import serializers

from backend.models import Image
from backend.models.galleries import Gallery, GalleryItem
from backend.serializers.base_serializers import (
    WritableSiteContentSerializer,
    base_id_fields,
    base_timestamp_fields,
)
from backend.serializers.media_serializers import (
    ImageSerializer,
    WriteableRelatedImageSerializer,
)


class GalleryItemSerializer(serializers.ModelSerializer):
    """
    Serializer for GalleryItem model.
    """

    def to_representation(self, instance):
        image_data = ImageSerializer(instance.image, context=self.context).data
        image_data["ordering"] = instance.ordering
        return image_data

    class Meta:
        model = GalleryItem


class WriteableGalleryItemSerializer(serializers.PrimaryKeyRelatedField):
    def use_pk_only_optimization(self):
        return False

    def to_representation(self, value):
        return GalleryItemSerializer(context=self.context).to_representation(value)


class GallerySummarySerializer(WritableSiteContentSerializer):
    """
    List serializer for Gallery model.
    """

    title_translation = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, default=""
    )
    introduction = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, default=""
    )
    introduction_translation = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, default=""
    )

    cover_image = WriteableRelatedImageSerializer(
        required=False,
        queryset=Image.objects.all(),
        allow_null=True,
        validators=[],
    )

    def validate(self, attrs):
        """
        Validate that gallery items are unique. Must be done before create/update.
        """
        gallery_items = attrs.get("galleryitem_set", [])
        if len(gallery_items) != len(set(gallery_items)):
            raise serializers.ValidationError("Gallery items must be unique.")
        return super().validate(attrs)

    def create(self, validated_data):
        gallery_items = validated_data.pop("galleryitem_set", [])

        created = super().create(validated_data)

        for gallery_item in enumerate(gallery_items):
            GalleryItem.objects.create(
                gallery=created, ordering=gallery_item[0], image=gallery_item[1]
            )
        return created

    def update(self, instance, validated_data):
        if "galleryitem_set" in validated_data:
            GalleryItem.objects.filter(gallery=instance).delete()
            gallery_items = validated_data.pop("galleryitem_set", [])
            for gallery_item in enumerate(gallery_items):
                GalleryItem.objects.create(
                    gallery=instance, ordering=gallery_item[0], image=gallery_item[1]
                )

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

    gallery_items = WriteableGalleryItemSerializer(
        many=True,
        required=False,
        source="galleryitem_set",
        queryset=Image.objects.all(),
    )

    class Meta(GallerySummarySerializer.Meta):
        fields = GallerySummarySerializer.Meta.fields + ("gallery_items",)
