import pytest
from rest_framework import serializers

from backend.models import Category
from backend.serializers import validators
from backend.serializers.category_serializers import CategoryDetailSerializer
from backend.tests import factories


class SameSiteSerializer(serializers.ModelSerializer):
    parent = serializers.PrimaryKeyRelatedField(
        validators=[validators.SameSite()],
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
        validators=[validators.HasNoParent()],
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


class TestCategoryDetailSerializerValidation:
    @pytest.mark.django_db
    def test_duplicate_category_title_on_same_site_fails(self):
        """
        Verify CategoryDetailSerializer safely catches duplicate titles on the same site,
        turning what used to be a database 500 integrity error into a clean 400 validation error.
        """
        unique_title = "UniqueTestCategoryXYZ"
        site = factories.SiteFactory.create()
        factories.CategoryFactory.create(title=unique_title, site=site)

        duplicate_payload = {
            "title": unique_title,
            "description": "A different description, but a duplicated name!",
        }
        context = {"site": site}
        serializer = CategoryDetailSerializer(data=duplicate_payload, context=context)

        assert not serializer.is_valid()
        assert serializer.errors == {
            "title": ["This field must be unique within the site."]
        }

    @pytest.mark.django_db
    def test_same_category_title_on_different_sites_succeeds(self):
        """
        Verify that having an identical category title across different sites is perfectly
        legal and passes our site-scoped validation check successfully.
        """
        unique_title = "UniqueTestCategoryXYZ"
        site_a = factories.SiteFactory.create()
        factories.CategoryFactory.create(title=unique_title, site=site_a)

        site_b = factories.SiteFactory.create()
        cross_site_payload = {
            "title": unique_title,
        }
        context = {"site": site_b}
        serializer = CategoryDetailSerializer(data=cross_site_payload, context=context)

        assert serializer.is_valid()
