from rest_framework import serializers

from backend.models.category import Category
from backend.models.constants import CATEGORY_POS_MAX_TITLE_LENGTH
from backend.serializers.base_serializers import (
    SiteContentLinkedTitleSerializer,
    WritableSiteContentSerializer,
)
from backend.serializers.validators import HasNoParent, SameSite, UniqueForSite


class LinkedCategorySerializer(SiteContentLinkedTitleSerializer):
    class Meta(SiteContentLinkedTitleSerializer.Meta):
        model = Category


class ChildCategoryListSerializer(SiteContentLinkedTitleSerializer):
    title = serializers.CharField(
        max_length=CATEGORY_POS_MAX_TITLE_LENGTH,
        validators=[UniqueForSite(queryset=Category.objects.all())],
    )
    description = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, default=""
    )

    class Meta(SiteContentLinkedTitleSerializer.Meta):
        model = Category
        fields = SiteContentLinkedTitleSerializer.Meta.fields + ("description",)


class ParentCategoryListSerializer(ChildCategoryListSerializer):
    children = ChildCategoryListSerializer(many=True, read_only=True)

    class Meta(ChildCategoryListSerializer.Meta):
        fields = ChildCategoryListSerializer.Meta.fields + ("children",)


class ParentCategoryFlatListSerializer(ChildCategoryListSerializer):
    parent_title = serializers.CharField(source="parent.title", read_only=True)

    class Meta(ChildCategoryListSerializer.Meta):
        fields = ChildCategoryListSerializer.Meta.fields + ("parent_title",)


class CategoryDetailSerializer(
    WritableSiteContentSerializer,
):
    description = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, default=""
    )
    children = ChildCategoryListSerializer(many=True, read_only=True)
    parent = LinkedCategorySerializer(read_only=True)
    parent_id = serializers.PrimaryKeyRelatedField(
        write_only=True,
        required=False,
        allow_null=True,
        validators=[
            SameSite(),
            HasNoParent(),
        ],
        source="parent",
        queryset=Category.objects.all(),
    )

    class Meta(ParentCategoryListSerializer.Meta):
        fields = WritableSiteContentSerializer.Meta.fields + (
            "description",
            "children",
            "parent",
            "parent_id",
        )
