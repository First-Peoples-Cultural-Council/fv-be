from rest_framework import serializers

from backend.models.category import Category
from backend.models.constants import CATEGORY_POS_MAX_TITLE_LENGTH
from backend.serializers.base_serializers import (
    CreateSiteContentSerializerMixin,
    SiteContentLinkedTitleSerializer,
    UpdateSerializerMixin,
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
    description = serializers.CharField(required=False)

    class Meta(SiteContentLinkedTitleSerializer.Meta):
        model = Category
        fields = SiteContentLinkedTitleSerializer.Meta.fields + ("description",)


class ParentCategoryListSerializer(ChildCategoryListSerializer):
    children = ChildCategoryListSerializer(many=True, read_only=True)

    class Meta(ChildCategoryListSerializer.Meta):
        fields = ChildCategoryListSerializer.Meta.fields + ("children",)


class CategoryDetailSerializer(
    UpdateSerializerMixin,
    CreateSiteContentSerializerMixin,
    ParentCategoryListSerializer,
):
    parent = LinkedCategorySerializer(read_only=True)
    parent_id = serializers.PrimaryKeyRelatedField(
        write_only=True,
        required=False,
        allow_null=True,
        validators=[
            SameSite(queryset=Category.objects.all()),
            HasNoParent(queryset=Category.objects.all()),
        ],
        source="parent",
        queryset=Category.objects.all(),
    )

    class Meta(ParentCategoryListSerializer.Meta):
        fields = ParentCategoryListSerializer.Meta.fields + (
            "parent",
            "parent_id",
        )
