import pytest
from rest_framework import serializers

from backend.models import Category
from backend.serializers import validators
from backend.tests import factories


class SameSiteSerializer(serializers.ModelSerializer):
    parent = serializers.PrimaryKeyRelatedField(
        validators=[validators.SameSite(queryset=Category.objects.all())],
        queryset=Category.objects.all(),
    )

    # make required fields read-only so we don't have to include them in test data
    title = serializers.CharField(read_only=True)
    site = serializers.CharField(read_only=True)

    class Meta:
        # use any model with a site field and another related field
        model = Category
        fields = "__all__"


class TestSameSiteValidator:
    @pytest.mark.django_db
    def test_related_model_in_same_site(self):
        instance = factories.CategoryFactory.create()
        data = {"parent": instance.id}
        context = {"site": instance.site}

        serializer = SameSiteSerializer(data=data, context=context)
        assert serializer.is_valid()

    @pytest.mark.django_db
    def test_related_model_in_different_site(self):
        instance = factories.CategoryFactory.create()
        data = {"parent": str(instance.id)}
        context = {"site": factories.SiteFactory.create()}

        serializer = SameSiteSerializer(data=data, context=context)
        assert not serializer.is_valid()
        assert serializer.errors == {"parent": ["Must be in the same site."]}


class UniqueForSiteSerializer(serializers.ModelSerializer):
    title = serializers.CharField(
        validators=[validators.UniqueForSite(queryset=Category.objects.all())]
    )

    # make required fields read-only so we don't have to include them in test data
    site = serializers.CharField(read_only=True)

    class Meta:
        # use any model with a site field and another related field
        model = Category
        fields = "__all__"


class TestUniqueForSiteValidator:
    @pytest.mark.django_db
    def test_unique_for_site_success(self):
        title = "a title"

        factories.CategoryFactory.create(title=title)

        # value can be used in a different site
        data = {"title": title}
        context = {"site": factories.SiteFactory.create()}

        serializer = UniqueForSiteSerializer(data=data, context=context)
        assert serializer.is_valid()

    @pytest.mark.django_db
    def test_unique_for_site_fail(self):
        title = "a title"
        site = factories.SiteFactory.create()
        factories.CategoryFactory.create(title=title, site=site)

        # value can't be used in same site
        data = {"title": title}
        context = {"site": site}

        serializer = UniqueForSiteSerializer(data=data, context=context)
        assert not serializer.is_valid()
        assert serializer.errors == {
            "title": ["This field must be unique within the site."]
        }


class HasNoParentSerializer(serializers.ModelSerializer):
    parent = serializers.PrimaryKeyRelatedField(
        validators=[validators.HasNoParent(queryset=Category.objects.all())],
        queryset=Category.objects.all(),
    )

    # make required fields read-only so we don't have to include them in test data
    title = serializers.CharField(read_only=True)
    site = serializers.CharField(read_only=True)

    class Meta:
        # use any model with a site field and another related field
        model = Category
        fields = "__all__"


class TestHasNoParentValidator:
    @pytest.mark.django_db
    def test_has_no_parent_success(self):
        instance = factories.CategoryFactory.create()

        data = {"parent": instance.id}
        context = {"site": instance.site}

        serializer = HasNoParentSerializer(data=data, context=context)
        assert serializer.is_valid()

    @pytest.mark.django_db
    def test_has_no_parent_fail(self):
        parent = factories.CategoryFactory.create()
        child = factories.CategoryFactory.create(parent=parent, site=parent.site)

        data = {"parent": child.id}
        context = {"site": child.site}

        serializer = HasNoParentSerializer(data=data, context=context)
        assert not serializer.is_valid()
        assert serializer.errors == {"parent": ["Must not have a parent."]}
