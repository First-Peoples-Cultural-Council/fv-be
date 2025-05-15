import factory
from factory.django import DjangoModelFactory

from backend.tests.factories.access import SiteFactory, UserFactory


class BaseFactory(DjangoModelFactory):
    class Meta:
        abstract = True

    created_by = factory.SubFactory(UserFactory)
    last_modified_by = factory.SubFactory(UserFactory)
    system_last_modified_by = factory.SubFactory(UserFactory)


class SiteContentFactory(BaseFactory):
    class Meta:
        abstract = True

    site = factory.SubFactory(SiteFactory)
