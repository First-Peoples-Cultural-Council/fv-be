import factory
from factory.django import DjangoModelFactory

from backend.models import BulkVisibilityJob, DictionaryCleanupJob
from backend.tests.factories.access import SiteFactory, UserFactory


class DictionaryCleanupFactory(DjangoModelFactory):
    class Meta:
        model = DictionaryCleanupJob

    site = factory.SubFactory(SiteFactory)
    created_by = factory.SubFactory(UserFactory)
    last_modified_by = factory.SubFactory(UserFactory)
    cleanup_result = {"test": "test"}


class BulkVisibilityJobFactory(DjangoModelFactory):
    class Meta:
        model = BulkVisibilityJob

    site = factory.SubFactory(SiteFactory)
    created_by = factory.SubFactory(UserFactory)
    last_modified_by = factory.SubFactory(UserFactory)

    task_id = factory.sequence(lambda n: f"task_id_{n}")
