import factory
from factory.django import DjangoModelFactory

from backend.models import Category
from backend.tests.factories.access import SiteFactory, UserFactory


class ParentCategoryFactory(DjangoModelFactory):
    site = factory.SubFactory(SiteFactory)
    title = factory.Sequence(lambda n: "Category title %03d" % n)
    description = factory.Sequence(lambda n: "Category description %03d" % n)
    created_by = factory.SubFactory(UserFactory)
    last_modified_by = factory.SubFactory(UserFactory)

    class Meta:
        model = Category


class ChildCategoryFactory(ParentCategoryFactory):
    parent = factory.SubFactory(ParentCategoryFactory)

    class Meta:
        model = Category
