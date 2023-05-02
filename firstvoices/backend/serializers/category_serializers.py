from rest_framework import serializers

from backend.models.category import Category


class CategoryChildrenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "title", "description"]


class CategoryListSerializer(CategoryChildrenSerializer):
    children = CategoryChildrenSerializer(many=True)

    class Meta(CategoryChildrenSerializer.Meta):
        fields = CategoryChildrenSerializer.Meta.fields + ["children"]


class CategoryDetailSerializer(CategoryListSerializer):
    class Meta(CategoryListSerializer.Meta):
        fields = CategoryListSerializer.Meta.fields + ["parent"]
