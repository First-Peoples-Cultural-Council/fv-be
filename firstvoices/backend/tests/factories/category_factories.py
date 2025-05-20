import factory

from backend.models import Category
from backend.tests.factories.base_factories import SiteContentFactory


class ParentCategoryFactory(SiteContentFactory):
    class Meta:
        model = Category

    title = factory.Sequence(lambda n: "Category title %03d" % n)
    description = factory.Sequence(lambda n: "Category description %03d" % n)


class ChildCategoryFactory(ParentCategoryFactory):
    parent = factory.SubFactory(ParentCategoryFactory)

    class Meta:
        model = Category
